from fastapi import WebSocket
from typing import Dict, List, Any, Set
import json
import asyncio
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Class to manage WebSocket connections.
    It maps user IDs to a set of WebSocket connections.
    """
    
    def __init__(self):
        # Map of user_id -> set of active WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        logger.info("WebSocket connection manager initialized")
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """
        Add a WebSocket connection for a user
        
        Args:
            websocket: The WebSocket connection
            user_id: The ID of the user
        """
        # Create entry for user if not exists
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        # Add this connection to the user's connections
        self.active_connections[user_id].add(websocket)
        logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, user_id: str, websocket: WebSocket = None):
        """
        Remove a WebSocket connection for a user
        
        Args:
            user_id: The ID of the user
            websocket: The specific WebSocket to remove (if None, removes all)
        """
        # Check if user exists
        if user_id not in self.active_connections:
            return
        
        # If a specific websocket is provided, remove only it
        if websocket is not None:
            self.active_connections[user_id].discard(websocket)
            logger.info(f"Removed a connection for user {user_id}")
        else:
            # Remove all connections for this user
            self.active_connections[user_id].clear()
            logger.info(f"Removed all connections for user {user_id}")
        
        # If user has no more connections, remove the user entry
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        """
        Send a message to all connections of a specific user
        
        Args:
            message: The message to send (will be converted to JSON)
            user_id: The ID of the user to send the message to
        """
        if user_id not in self.active_connections:
            logger.warning(f"Attempted to send message to non-connected user {user_id}")
            return
        
        message_json = json.dumps(message)
        
        # Send to all of user's connections (allows multiple devices)
        disconnected = set()
        for connection in self.active_connections[user_id]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {str(e)}")
                disconnected.add(connection)
        
        # Clean up disconnected websockets
        for ws in disconnected:
            self.active_connections[user_id].discard(ws)
        
        # If user has no more connections, remove the user entry
        if not self.active_connections[user_id]:
            del self.active_connections[user_id]
    
    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected clients
        
        Args:
            message: The message to broadcast (will be converted to JSON)
        """
        message_json = json.dumps(message)
        
        # Track disconnected users for cleanup
        disconnected_users = []
        
        # Send to all connections of all users
        for user_id, connections in self.active_connections.items():
            disconnected = set()
            for connection in connections:
                try:
                    await connection.send_text(message_json)
                except Exception as e:
                    logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            for ws in disconnected:
                connections.discard(ws)
            
            # If user has no more connections, mark for removal
            if not connections:
                disconnected_users.append(user_id)
        
        # Clean up users with no connections
        for user_id in disconnected_users:
            del self.active_connections[user_id]
    
    async def broadcast_emotion_update(self, user_id: str, emotion: Dict[str, Any]):
        """
        Broadcast an emotion update to all connections of a user
        
        Args:
            user_id: The ID of the user whose emotion changed
            emotion: The new emotion data
        """
        await self.send_personal_message({
            "type": "emotion_update",
            "data": {
                "emotion": emotion,
                "timestamp": emotion.get("timestamp", None)
            }
        }, user_id)
        
        logger.info(f"Broadcasted emotion update for user {user_id}: {emotion.get('name', 'Unknown')}")
    
    def get_connected_users(self) -> List[str]:
        """
        Get a list of all connected user IDs
        
        Returns:
            List of user IDs with active connections
        """
        return list(self.active_connections.keys())

# Create a global instance of the connection manager
manager = ConnectionManager() 