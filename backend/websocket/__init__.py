"""
WebSocket module for real-time updates.
"""

from .manager import Connection, ConnectionManager, manager
from .router import (
    set_connection_manager,
    get_manager,
    broadcast_task_created,
    broadcast_task_updated,
    broadcast_task_deleted,
    broadcast_conflict_alert,
    broadcast_schedule_updated,
)

__all__ = [
    "Connection",
    "ConnectionManager",
    "manager",
    "set_connection_manager",
    "get_manager",
    "broadcast_task_created",
    "broadcast_task_updated",
    "broadcast_task_deleted",
    "broadcast_conflict_alert",
    "broadcast_schedule_updated",
]
