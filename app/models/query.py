from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
from pydantic.json import pydantic_encoder


class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str
    search_type: Optional[str] = "tavily"  # "tavily" or "serper"


class SearchResult(BaseModel):
    """Model for individual search results"""
    title: str
    url: str
    content: str
    source: str


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    query: str
    results: List[SearchResult]
    timestamp: datetime


class StreamMessage(BaseModel):
    """Model for WebSocket streaming messages"""
    type: str  # "search_result", "status", "error", "complete"
    data: dict
    timestamp: datetime
    
    def json_serializable_dict(self):
        """Return a dictionary that is JSON serializable"""
        data = self.dict()
        # Convert datetime to ISO format string
        data['timestamp'] = self.timestamp.isoformat()
        return data