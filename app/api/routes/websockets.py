from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import json
from typing import Dict, Optional
import logging

from app.utils.websocket_manager import manager
from app.core.security import SECRET_KEY, ALGORITHM
from jose import JWTError, jwt
from app.models.user import User
from app.database.database import db, USERS_COLLECTION
from app.services.user_service import UserService

# Create a router for WebSocket endpoints
router = APIRouter()

# Configure logging
logger = logging.getLogger(__name__)

# Security scheme for token extraction (bearer token)
security = HTTPBearer()


async def get_user_from_token(token: str) -> Optional[Dict]:
    """
    Validate JWT token and extract user information
    """
    try:
        # Extract token from Bearer format if needed
        if token.startswith("Bearer "):
            token = token[7:]  # Remove "Bearer " prefix
            
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        
        # Get user from database using the service
        user = await UserService.find_by_email(email)
        if user is None:
            return None
        
        return {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
            
    except JWTError as e:
        logger.error(f"WebSocket JWT Error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Get authentication token from query parameters
        token = websocket.query_params.get("token")
        if not token:
            await websocket.send_text(json.dumps({"error": "Authentication required"}))
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Validate token and get user
        user_data = await get_user_from_token(token)
        if not user_data:
            await websocket.send_text(json.dumps({"error": "Invalid authentication token"}))
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Add connection to manager
        user_id = user_data["id"]
        await manager.connect(websocket, user_id)
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "data": {
                "message": "Connected to WebSocket",
                "user": user_data
            }
        }))
        
        # Handle incoming messages
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            
            try:
                # Parse JSON message
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                # Handle different message types
                if message_type == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "data": {"time": message.get("data", {}).get("time")}
                    }))
                elif message_type == "emotion_update":
                    # Handle emotion update (this will be broadcast by the backend service)
                    pass
                else:
                    # Unknown message type
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {"message": f"Unknown message type: {message_type}"}
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"message": "Invalid JSON message"}
                }))
    
    except WebSocketDisconnect:
        # Handle client disconnect
        if 'user_id' in locals():
            manager.disconnect(user_id)
    except Exception as e:
        # Handle other exceptions
        logger.error(f"WebSocket error: {str(e)}")
        if 'websocket' in locals() and not websocket.client_state.DISCONNECTED:
            await websocket.send_text(json.dumps({
                "type": "error",
                "data": {"message": "Internal server error"}
            }))
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR) 