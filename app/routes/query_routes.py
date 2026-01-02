from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Optional
import uuid
from datetime import datetime

from app.models.query import QueryRequest, QueryResponse, SearchResult
from app.services.search_service import SearchService
from app.services.graph_service import GraphService
from app.websocket.stream_manager import StreamManager
from app.utils.logger import get_logger


# Initialize router and services
router = APIRouter()
search_service = SearchService()
graph_service = GraphService()
stream_manager = StreamManager()
logger = get_logger(__name__)


@router.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await graph_service.connect()


@router.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown"""
    await graph_service.close()


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Main query endpoint that accepts user queries and returns search results.
    
    Args:
        request: QueryRequest containing the query and search type
        
    Returns:
        QueryResponse with search results and timestamp
    """
    try:
        # Log the incoming query
        logger.info(f"Processing query: {request.query}")
        
        # Perform the search
        results = await search_service.search(request.query, request.search_type)
        
        # Save query and results to Neo4j
        await graph_service.save_query_and_sources(request.query, results)
        
        # Create and return response
        response = QueryResponse(
            query=request.query,
            results=results,
            timestamp=datetime.now()
        )
        
        logger.info(f"Query processed successfully, returned {len(results)} results")
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@router.websocket("/ws/stream/{session_id}")
async def websocket_stream_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time streaming of search results.
    
    Args:
        websocket: WebSocket connection
        session_id: Unique session identifier
    """
    await stream_manager.manager.connect(websocket, session_id)
    
    try:
        # Receive the initial query from the client
        data = await websocket.receive_json()
        query_text = data.get("query", "")
        search_type = data.get("search_type", "tavily")
        
        if not query_text:
            await stream_manager.send_message(websocket, {"event": "error", "message": "Query text is required"})
            return
        
        # Send initial status
        await stream_manager.send_message(websocket, {"event": "status", "message": "Searching sources..."})
        
        # Perform search with streaming
        results = []
        
        async def result_callback(result: SearchResult):
            """Callback function to handle each search result as it arrives"""
            source_data = {
                "event": "source",
                "title": result.title,
                "url": result.url,
                "snippet": result.content,
                "source_id": str(uuid.uuid4())[:8]  # Generate a short ID
            }
            await stream_manager.send_message(websocket, source_data)
            results.append(result)
        
        try:
            # Perform streaming search
            await search_service.search_streaming(query_text, search_type, result_callback)
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            await stream_manager.send_message(websocket, {"event": "error", "message": f"Search failed: {str(e)}"})
            return
        
        # Save results to Neo4j
        try:
            await graph_service.save_query_and_sources(query_text, results, session_id)
        except Exception as e:
            logger.error(f"Error saving to Neo4j: {str(e)}")
            # Still send completion even if Neo4j fails
        
        # Send completion message
        await stream_manager.send_message(websocket, {"event": "done", "total_results": len(results)})
        
    except WebSocketDisconnect:
        stream_manager.manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await stream_manager.send_message(websocket, {"event": "error", "message": f"WebSocket error: {str(e)}"})
        except:
            pass  # If we can't send the error, just disconnect
        stream_manager.manager.disconnect(session_id)


@router.get("/history")
async def get_query_history(limit: int = 10):
    """
    Get recent query history from Neo4j.
    
    Args:
        limit: Maximum number of queries to return
        
    Returns:
        Dictionary with history of queries
    """
    try:
        history = await graph_service.get_query_history(limit)
        return {"history": history}
    except Exception as e:
        logger.error(f"Error retrieving query history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving query history: {str(e)}")