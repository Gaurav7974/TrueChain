import asyncio
import json
from typing import Dict, List
from fastapi import WebSocket, WebSocketDisconnect
from app.models.query import StreamMessage
from datetime import datetime


class ConnectionManager:
    """Manager class for handling WebSocket connections."""

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Connect a WebSocket client.
        
        Args:
            websocket: WebSocket connection object
            client_id: Unique client identifier
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        """
        Disconnect a WebSocket client.
        
        Args:
            client_id: Unique client identifier
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str):
        """
        Send a message to a specific client.
        
        Args:
            message: Message dictionary to send
            client_id: Unique client identifier
        """
        websocket = self.active_connections.get(client_id)
        if websocket:
            # Convert datetime objects to ISO format strings for JSON serialization
            def convert_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {key: convert_datetime(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime(item) for item in obj]
                return obj
            
            converted_message = convert_datetime(message)
            await websocket.send_text(json.dumps(converted_message))

    async def send_message(self, websocket: WebSocket, message: dict):
        """
        Send a message directly to a WebSocket connection.
        
        Args:
            websocket: WebSocket connection object
            message: Message dictionary to send
        """
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Message dictionary to send
        """
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except WebSocketDisconnect:
                # Remove disconnected clients
                self.disconnect(client_id)


class StreamManager:
    """Manager class for handling WebSocket streaming operations."""

    def __init__(self):
        """Initialize the stream manager."""
        self.manager = ConnectionManager()

    async def send_message(self, websocket: WebSocket, message: dict):
        """
        Send a message directly to a WebSocket connection.
        
        Args:
            websocket: WebSocket connection object
            message: Message dictionary to send
        """
        await self.manager.send_message(websocket, message)

    async def send_status_update(self, client_id: str, status: str, query: str = None):
        """
        Send a status update to a specific client.
        
        Args:
            client_id: Unique client identifier
            status: Status message
            query: Optional query text
        """
        message = StreamMessage(
            type="status",
            data={
                "status": status,
                "query": query
            },
            timestamp=datetime.now()
        )
        await self.manager.send_personal_message(message.json_serializable_dict(), client_id)

    async def send_search_result(self, client_id: str, result_data: dict):
        """
        Send a search result to a specific client.
        
        Args:
            client_id: Unique client identifier
            result_data: Search result data
        """
        message = StreamMessage(
            type="search_result",
            data=result_data,
            timestamp=datetime.now()
        )
        await self.manager.send_personal_message(message.json_serializable_dict(), client_id)

    async def send_error(self, client_id: str, error_message: str):
        """
        Send an error message to a specific client.
        
        Args:
            client_id: Unique client identifier
            error_message: Error message text
        """
        message = StreamMessage(
            type="error",
            data={
                "error": error_message
            },
            timestamp=datetime.now()
        )
        await self.manager.send_personal_message(message.json_serializable_dict(), client_id)

    async def send_complete(self, client_id: str, total_results: int):
        """
        Send completion message to a specific client.
        
        Args:
            client_id: Unique client identifier
            total_results: Total number of results
        """
        message = StreamMessage(
            type="complete",
            data={
                "total_results": total_results,
                "completed_at": datetime.now().isoformat()
            },
            timestamp=datetime.now()
        )
        await self.manager.send_personal_message(message.json_serializable_dict(), client_id)

    async def handle_client_connection(self, websocket: WebSocket, client_id: str):
        """
        Handle a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection object
            client_id: Unique client identifier
        """
        await self.manager.connect(websocket, client_id)
        try:
            while True:
                # Listen for messages from client (though for this use case we may not need it)
                data = await websocket.receive_text()
                # For now, just echo back the message
                await self.manager.send_personal_message({"message": f"Received: {data}"}, client_id)
        except WebSocketDisconnect:
            self.manager.disconnect(client_id)