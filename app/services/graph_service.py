try:
    from neo4j import AsyncGraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Warning: neo4j package not available. Graph functionality will be mocked.")
    
from app.config import Config
from app.models.query import SearchResult
import logging


class GraphService:
    """Service class for handling Neo4j graph operations."""

    def __init__(self):
        """Initialize the graph service with Neo4j configuration."""
        self.uri = Config.NEO4J_URI
        self.user = Config.NEO4J_USERNAME
        self.password = Config.NEO4J_PASSWORD
        self.database = Config.NEO4J_DATABASE
        self.driver = None
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        """
        Establish connection to Neo4j database.
        
        Raises:
            Exception: If connection fails
        """
        if not NEO4J_AVAILABLE:
            self.logger.warning("Neo4j not available, using mock implementation")
            return
            
        try:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Test the connection
            async with self.driver.session(database=self.database) as session:
                await session.run("RETURN 1")
            self.logger.info("Successfully connected to Neo4j database")
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {str(e)}")
            raise

    async def close(self):
        """Close the Neo4j connection."""
        if self.driver:
            await self.driver.close()

    async def save_query_and_sources(self, query_text: str, search_results: list[SearchResult], session_id: str = None):
        """
        Save the query and its search results to Neo4j with Query -> Source relationships.
        
        Args:
            query_text: The original query text
            search_results: List of SearchResult objects
            session_id: Optional session identifier
            
        Raises:
            Exception: If saving fails
        """
        if not NEO4J_AVAILABLE:
            self.logger.warning("Neo4j not available, skipping save to graph")
            return
        
        if not self.driver:
            raise Exception("Neo4j driver not initialized. Call connect() first.")
        
        try:
            async with self.driver.session(database=self.database) as session:
                # Create or merge the query node with session_id
                if session_id:
                    query_result = await session.run(
                        """
                        MERGE (q:Query {text: $query_text})
                        SET q.timestamp = datetime(),
                            q.session_id = $session_id
                        RETURN q
                        """,
                        query_text=query_text,
                        session_id=session_id
                    )
                else:
                    query_result = await session.run(
                        """
                        MERGE (q:Query {text: $query_text})
                        SET q.timestamp = datetime()
                        RETURN q
                        """,
                        query_text=query_text
                    )
                
                # Create source nodes and relationships
                for result in search_results:
                    # Skip if URL is empty
                    if not result.url.strip():
                        continue
                        
                    # Create source node with deduplication
                    source_result = await session.run(
                        """
                        MERGE (s:Source {url: $url})
                        SET s.title = $title,
                            s.snippet = $snippet,
                            s.source = $source,
                            s.fetch_time = datetime()
                        RETURN s
                        """,
                        url=result.url,
                        title=result.title,
                        snippet=result.content,
                        source=result.source
                    )
                    
                    # Create relationship between query and source
                    await session.run(
                        """
                        MATCH (q:Query {text: $query_text})
                        MATCH (s:Source {url: $url})
                        MERGE (q)-[:REFERENCES]->(s)
                        """,
                        query_text=query_text,
                        url=result.url
                    )
                
                self.logger.info(f"Successfully saved query and {len(search_results)} sources to Neo4j")
                
        except Exception as e:
            self.logger.error(f"Error saving query and sources to Neo4j: {str(e)}")
            raise

    async def get_query_history(self, limit: int = 10):
        """
        Retrieve recent queries from Neo4j.
        
        Args:
            limit: Maximum number of queries to retrieve
            
        Returns:
            List of query history items
            
        Raises:
            Exception: If retrieval fails
        """
        if not NEO4J_AVAILABLE:
            self.logger.warning("Neo4j not available, returning empty history")
            return []
        
        if not self.driver:
            raise Exception("Neo4j driver not initialized. Call connect() first.")
        
        try:
            async with self.driver.session(database=self.database) as session:
                result = await session.run(
                    """
                    MATCH (q:Query)
                    RETURN q.text AS query, q.timestamp AS timestamp
                    ORDER BY q.timestamp DESC
                    LIMIT $limit
                    """,
                    limit=limit
                )
                
                queries = []
                async for record in result:
                    queries.append({
                        "query": record["query"],
                        "timestamp": record["timestamp"]
                    })
                
                return queries
        except Exception as e:
            self.logger.error(f"Error retrieving query history from Neo4j: {str(e)}")
            raise