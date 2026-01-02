# GraphRAG - Perplexity-style Search Engine

A real-time search application with knowledge graph visualization that connects user queries to information sources through a dynamic graph interface.

## Features

- Real-time Search: Integrates with Tavily API for up-to-date search results
- WebSocket Streaming: Live streaming of search results as they are found
- Knowledge Graph: Visual representation of query-source relationships
- Interactive UI: Three-panel interface with query input, results, and graph visualization
- Neo4j Integration: Stores query-source relationships in a graph database

## Tech Stack

- Backend: FastAPI
- Frontend: HTML, CSS, JavaScript
- Graph Visualization: Three.js + three-forcegraph
- Database: Neo4j
- Search APIs: Tavily, Serper

## Project Structure

```
GraphRAG/
├── app/
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration and environment variables
│   ├── models/
│   │   └── query.py            # Data models (Pydantic)
│   ├── services/
│   │   ├── search_service.py   # Tavily/Serper API integration
│   │   └── graph_service.py    # Neo4j graph operations
│   ├── routes/
│   │   └── query_routes.py     # API routes
│   ├── websocket/
│   │   └── stream_manager.py   # WebSocket streaming manager
│   └── utils/
│       └── logger.py           # Logging utilities
├── static/
│   ├── index.html              # Main UI
│   ├── styles.css              # Styling
│   └── script.js               # Frontend JavaScript
├── requirements.txt            # Dependencies
├── .env                       # Environment variables
└── .gitignore                 # Git ignore rules
```

## Setup

1. Install Dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Environment Variables: Create a `.env` file with:
   ```env
   NEO4J_URI=neo4j+s://your-neo4j-uri
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your-password
   NEO4J_DATABASE=neo4j
   TAVILY_API_KEY=your-tavily-api-key
   SERPER_API_KEY=your-serper-api-key
   ```

3. Run the Application:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### REST Endpoints

- `GET /` - Main UI
- `GET /health` - Health check
- `POST /api/query` - Submit a query
- `GET /api/history` - Get query history

### WebSocket Endpoints

- `WS /api/ws/stream/{session_id}` - WebSocket for real-time streaming

## Usage

1. Open your browser and navigate to `http://localhost:8000`
2. Enter a query in the search box
3. Watch as results stream in real-time in the left panel
4. Observe the knowledge graph build dynamically in the right panel
5. The graph shows relationships between your query and the information sources

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.