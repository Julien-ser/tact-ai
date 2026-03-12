"""
WebSocket Connection Manager for real-time updates.

Manages active WebSocket connections and provides methods to send messages
to specific users or broadcast to all connections.
"""

from typing import Dict, List, Optional, Set
import logging
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User as UserModel

logger = logging.getLogger(__name__)


class Connection:
    """Represents an active WebSocket connection."""

    def __init__(self, websocket: WebSocket, user_id: int):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_id = id(websocket)

    async def send_json(self, data: dict) -> None:
        """Send JSON data to this connection."""
        try:
            await self.websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error sending to connection {self.connection_id}: {e}")

    async def close(self) -> None:
        """Close this connection."""
        try:
            await self.websocket.close()
        except Exception as e:
            logger.error(f"Error closing connection {self.connection_id}: {e}")


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.

    Supports:
    - User-specific connections (one user can have multiple connections)
    - Sending messages to individual users
    - Broadcasting to all connected users
    - Automatic cleanup on disconnect
    """

    def __init__(self):
        # Map user_id -> Set of Connection objects
        self._user_connections: Dict[int, Set[Connection]] = {}
        # Map connection_id -> Connection object for fast lookup
        self._connections: Dict[int, Connection] = {}
        # Map connection_id -> user_id for reverse lookup
        self._connection_to_user: Dict[int, int] = {}

    def add_connection(self, connection: Connection) -> None:
        """Add a new connection to the manager."""
        user_id = connection.user_id
        if user_id not in self._user_connections:
            self._user_connections[user_id] = set()
        self._user_connections[user_id].add(connection)
        self._connections[connection.connection_id] = connection
        self._connection_to_user[connection.connection_id] = user_id
        logger.info(f"Added connection {connection.connection_id} for user {user_id}")

    def remove_connection(self, connection_id: int) -> None:
        """Remove a connection from the manager."""
        if connection_id not in self._connections:
            return

        connection = self._connections[connection_id]
        user_id = connection.user_id

        # Remove from user connections
        if user_id in self._user_connections:
            self._user_connections[user_id].discard(connection)
            if not self._user_connections[user_id]:
                del self._user_connections[user_id]

        # Remove from mappings
        del self._connections[connection_id]
        del self._connection_to_user[connection_id]

        logger.info(f"Removed connection {connection_id} for user {user_id}")

    async def send_to_user(self, user_id: int, event: str, data: dict) -> None:
        """
        Send a message to all connections of a specific user.

        Args:
            user_id: Target user ID
            event: Event type (e.g., "task_created", "conflict_alert")
            data: JSON-serializable data payload
        """
        if user_id not in self._user_connections:
            logger.debug(f"No connections for user {user_id}")
            return

        message = {"event": event, "data": data}
        connections = list(self._user_connections[user_id])

        # Send to all connections, remove dead ones
        dead_connections = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                dead_connections.append(connection.connection_id)

        # Clean up dead connections
        for conn_id in dead_connections:
            self.remove_connection(conn_id)

    async def broadcast(
        self, event: str, data: dict, exclude_user_id: Optional[int] = None
    ) -> None:
        """
        Broadcast a message to all connected users.

        Args:
            event: Event type
            data: JSON-serializable data payload
            exclude_user_id: Optional user ID to exclude from broadcast
        """
        message = {"event": event, "data": data}
        all_connections = list(self._connections.values())

        for connection in all_connections:
            if exclude_user_id is not None and connection.user_id == exclude_user_id:
                continue
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {connection.user_id}: {e}")

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self._connections)

    def get_user_connection_count(self, user_id: int) -> int:
        """Get number of active connections for a specific user."""
        return len(self._user_connections.get(user_id, set()))

    def get_connected_users(self) -> Set[int]:
        """Get set of user IDs with active connections."""
        return set(self._user_connections.keys())


# Global connection manager instance
manager = ConnectionManager()
