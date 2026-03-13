"""
WebSocket Router for real-time updates.

Provides WebSocket endpoint for push notifications with JWT authentication.
Supports events for task changes and conflict alerts.
"""

import json
import logging
from typing import Optional, Dict, Any
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.database import get_db
from backend.models.user import User as UserModel
from backend.auth.utils import decode_token
from .manager import Connection, ConnectionManager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Get the global connection manager (will be set by main.py)
_manager: Optional[ConnectionManager] = None


def set_connection_manager(manager: ConnectionManager) -> None:
    """Set the global connection manager instance (called from main.py)."""
    global _manager
    _manager = manager


def get_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    if _manager is None:
        raise RuntimeError("Connection manager not initialized")
    return _manager


async def get_user_from_token(token: str, db: Session) -> Optional[UserModel]:
    """
    Validate JWT token and get user.

    Args:
        token: JWT token string
        db: Database session

    Returns:
        User model if valid, None otherwise
    """
    payload = decode_token(token)
    if payload is None:
        return None

    username: Optional[str] = payload.get("sub")
    if username is None:
        return None

    user = db.execute(
        select(UserModel).where(UserModel.email == username)
    ).scalar_one_or_none()

    return user


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT access token"),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time updates.

    Connect with a JWT token as a query parameter:
      ws://localhost:8000/ws?token=YOUR_JWT_TOKEN

    The connection will be authenticated and associated with your user account.
    You'll receive real-time notifications for:
      - task_created: when a new task is created
      - task_updated: when a task is modified
      - task_deleted: when a task is removed
      - conflict_alert: when schedule conflicts are detected

    Args:
        websocket: WebSocket connection
        token: JWT token (query parameter, required)
        db: Database session (injected by FastAPI)
    """
    manager = get_manager()

    # Authenticate user via JWT token
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    user = await get_user_from_token(token, db)
    if user is None:
        await websocket.close(code=1008, reason="Invalid authentication token")
        return

    # Accept connection
    await websocket.accept()

    connection = Connection(websocket, user.id)
    manager.add_connection(connection)

    logger.info(
        f"User {user.id} connected via WebSocket (connection: {connection.connection_id})"
    )

    try:
        # Send initial connection confirmation
        await connection.send_json(
            {
                "event": "connected",
                "data": {
                    "user_id": user.id,
                    "message": "Connected to Tact AI real-time updates",
                },
            }
        )

        # Keep connection alive and handle incoming messages
        # (primarily for heartbeat/ping from client)
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle ping/pong for connection health checks
                if message.get("type") == "ping":
                    await connection.send_json(
                        {"type": "pong", "timestamp": message.get("timestamp")}
                    )

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user.id}")
            except Exception as e:
                logger.error(f"Error receiving message from user {user.id}: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"User {user.id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for user {user.id}: {e}")
    finally:
        manager.remove_connection(connection.connection_id)


# Helper functions to be used by other routers for broadcasting events
async def broadcast_task_created(
    manager: ConnectionManager, task_data: Dict[str, Any], user_id: int
):
    """Broadcast task creation event to the task owner."""
    await manager.send_to_user(user_id, "task_created", task_data)


async def broadcast_task_updated(
    manager: ConnectionManager, task_data: Dict[str, Any], user_id: int
):
    """Broadcast task update event to the task owner."""
    await manager.send_to_user(user_id, "task_updated", task_data)


async def broadcast_task_deleted(
    manager: ConnectionManager, task_id: int, user_id: int
):
    """Broadcast task deletion event to the task owner."""
    await manager.send_to_user(user_id, "task_deleted", {"task_id": task_id})


async def broadcast_conflict_alert(
    manager: ConnectionManager, conflicts_data: Dict[str, Any], user_id: int
):
    """Broadcast conflict alert to the user."""
    await manager.send_to_user(user_id, "conflict_alert", conflicts_data)


async def broadcast_schedule_updated(
    manager: ConnectionManager, schedule_data: Dict[str, Any], user_id: int
):
    """Broadcast schedule update event to the user."""
    await manager.send_to_user(user_id, "schedule_updated", schedule_data)
