from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes.query_routes import router as query_router
from app.config import Config
from app.utils.logger import get_logger


# Create FastAPI app instance
app = FastAPI(
    title="GraphRAG Backend",
    description="Backend system for accepting queries, searching, and building Neo4j graphs",
    version="1.0.0"
)

# Set up logger
logger = get_logger(__name__)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query_router, prefix="/api", tags=["query"])

# Serve static files
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
async def root():
    """Serve the main HTML page"""
    from fastapi.responses import HTMLResponse
    from pathlib import Path
    
    html_path = Path("static/index.html")
    if html_path.exists():
        return HTMLResponse(html_path.read_text())
    else:
        return {"message": "GraphRAG Backend is running!", "status": "ok"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GraphRAG Backend"
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting GraphRAG Backend server...")
    uvicorn.run(
        "app.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=True  # Enable auto-reload during development
    )