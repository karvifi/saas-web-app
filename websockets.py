"""
WebSocket support for real-time AI Agent Platform
Real-time task updates, notifications, and live agent interactions
"""

from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Depends
from typing import Dict, List, Set
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    """WebSocket connection manager for real-time features"""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str, channel: str = "general"):
        """Connect a WebSocket for a user"""
        await websocket.accept()

        if channel not in self.active_connections:
            self.active_connections[channel] = set()

        self.active_connections[channel].add(websocket)
        self.user_connections[user_id] = websocket

        logger.info(f"User {user_id} connected to channel {channel}")

        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "user_id": user_id,
            "channel": channel,
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

    def disconnect(self, websocket: WebSocket, user_id: str, channel: str = "general"):
        """Disconnect a WebSocket"""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)

        if user_id in self.user_connections:
            del self.user_connections[user_id]

        logger.info(f"User {user_id} disconnected from channel {channel}")

    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """Send message to specific WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")

    async def broadcast_to_channel(self, message: Dict, channel: str = "general"):
        """Broadcast message to all connections in a channel"""
        if channel not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.add(connection)

        # Clean up disconnected connections
        for conn in disconnected:
            self.active_connections[channel].discard(conn)

    async def send_to_user(self, user_id: str, message: Dict):
        """Send message to specific user"""
        if user_id in self.user_connections:
            await self.send_personal_message(message, self.user_connections[user_id])

    async def broadcast_task_update(self, task_id: str, status: str, user_id: str, result: Dict = None):
        """Broadcast task status updates"""
        message = {
            "type": "task_update",
            "task_id": task_id,
            "status": status,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        if result:
            message["result"] = result

        await self.send_to_user(user_id, message)
        await self.broadcast_to_channel(message, "tasks")

    async def broadcast_agent_status(self, agent_name: str, status: str, active_users: int = 0):
        """Broadcast agent status updates"""
        message = {
            "type": "agent_status",
            "agent": agent_name,
            "status": status,
            "active_users": active_users,
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.broadcast_to_channel(message, "agents")

    async def broadcast_system_notification(self, title: str, message: str, level: str = "info"):
        """Broadcast system-wide notifications"""
        notification = {
            "type": "system_notification",
            "title": title,
            "message": message,
            "level": level,  # info, warning, error, success
            "timestamp": datetime.utcnow().isoformat()
        }

        await self.broadcast_to_channel(notification, "system")

# Global connection manager
manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, channel: str = "general"):
    """Main WebSocket endpoint"""
    await manager.connect(websocket, user_id, channel)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Handle different message types
            message_type = data.get("type", "unknown")

            if message_type == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)

            elif message_type == "subscribe_channel":
                new_channel = data.get("channel", "general")
                # Reconnect to new channel
                manager.disconnect(websocket, user_id, channel)
                await manager.connect(websocket, user_id, new_channel)
                channel = new_channel

            elif message_type == "task_status_request":
                task_id = data.get("task_id")
                # Could implement task status lookup here
                await manager.send_personal_message({
                    "type": "task_status_response",
                    "task_id": task_id,
                    "status": "checking"
                }, websocket)

            # Echo back for debugging
            await manager.send_personal_message({
                "type": "echo",
                "original_message": data,
                "timestamp": datetime.utcnow().isoformat()
            }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id, channel)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id, channel)

@router.websocket("/ws/tasks/{task_id}")
async def task_websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for specific task monitoring"""
    await websocket.accept()

    try:
        # Send initial task status
        await websocket.send_json({
            "type": "task_info",
            "task_id": task_id,
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })

        while True:
            # Keep connection alive and listen for task updates
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Task WebSocket error for task {task_id}: {e}")

# Helper functions for external use
async def notify_task_update(task_id: str, status: str, user_id: str, result: Dict = None):
    """Helper function to notify about task updates"""
    await manager.broadcast_task_update(task_id, status, user_id, result)

async def notify_agent_status(agent_name: str, status: str, active_users: int = 0):
    """Helper function to notify about agent status"""
    await manager.broadcast_agent_status(agent_name, status, active_users)

async def send_system_notification(title: str, message: str, level: str = "info"):
    """Helper function to send system notifications"""
    await manager.broadcast_system_notification(title, message, level)

async def send_user_notification(user_id: str, title: str, message: str, level: str = "info"):
    """Helper function to send notifications to specific users"""
    notification = {
        "type": "user_notification",
        "title": title,
        "message": message,
        "level": level,
        "timestamp": datetime.utcnow().isoformat()
    }
    await manager.send_to_user(user_id, notification)