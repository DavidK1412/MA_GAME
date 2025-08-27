"""
Enhanced database client with transaction support and better error handling.
"""

import psycopg2
import psycopg2.extras
from psycopg2.extras import DictCursor
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Union
from core.logging import get_logger
from core.exceptions import DatabaseError

logger = get_logger(__name__)


class DatabaseClient:
    """Enhanced PostgreSQL database client with transaction support."""
    
    def __init__(self, dbname: str, user: str, password: str, host: str = 'localhost', port: str = '5432'):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None
        self.cursor = None
        self._connection_params = {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }

    def connect(self) -> None:
        """Establish database connection with error handling."""
        try:
            self.connection = psycopg2.connect(**self._connection_params)
            self.connection.autocommit = False  # Enable transactions
            self.cursor = self.connection.cursor(cursor_factory=DictCursor)
            logger.info(f"Database connection established to {self.host}:{self.port}/{self.dbname}")
        except psycopg2.DatabaseError as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseError(f"Failed to connect to database: {e}")

    def is_connected(self) -> bool:
        """Check if database connection is active."""
        return (
            self.connection is not None 
            and not self.connection.closed 
            and self.cursor is not None
        )

    def ensure_connection(self) -> None:
        """Ensure database connection is active, reconnect if necessary."""
        if not self.is_connected():
            logger.warning("Database connection lost, attempting to reconnect...")
            self.connect()

    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        if not self.is_connected():
            self.connect()
        
        try:
            yield self
            self.connection.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise

    def execute_query(self, query: str, params: Optional[Union[tuple, list, dict]] = None) -> None:
        """Execute a query with parameters."""
        self.ensure_connection()
        
        try:
            self.cursor.execute(query, params)
            logger.debug(f"Query executed successfully: {query[:100]}...")
        except psycopg2.DatabaseError as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise DatabaseError(f"Query execution failed: {e}")

    def fetch_results(self, query: str, params: Optional[Union[tuple, list, dict]] = None) -> List[Dict[str, Any]]:
        """Fetch all results from a query."""
        self.ensure_connection()
        
        try:
            self.cursor.execute(query, params)
            results = [dict(row) for row in self.cursor.fetchall()]
            logger.debug(f"Fetched {len(results)} results from query")
            return results
        except psycopg2.DatabaseError as e:
            logger.error(f"Failed to fetch results: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            return []

    def fetch_one(self, query: str, params: Optional[Union[tuple, list, dict]] = None) -> Optional[Dict[str, Any]]:
        """Fetch a single result from a query."""
        self.ensure_connection()
        
        try:
            self.cursor.execute(query, params)
            result = self.cursor.fetchone()
            return dict(result) if result else None
        except psycopg2.DatabaseError as e:
            logger.error(f"Failed to fetch single result: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            return None

    def execute_many(self, query: str, params_list: List[Union[tuple, list, dict]]) -> None:
        """Execute a query multiple times with different parameters."""
        self.ensure_connection()
        
        try:
            self.cursor.executemany(query, params_list)
            logger.debug(f"Executed query {len(params_list)} times: {query[:100]}...")
        except psycopg2.DatabaseError as e:
            logger.error(f"Batch execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params count: {len(params_list)}")
            raise DatabaseError(f"Batch execution failed: {e}")

    def get_last_insert_id(self) -> Optional[str]:
        """Get the ID of the last inserted row."""
        if not self.cursor:
            return None
        
        try:
            return self.cursor.fetchone()[0] if self.cursor.rowcount > 0 else None
        except Exception:
            return None

    def get_row_count(self) -> int:
        """Get the number of rows affected by the last operation."""
        return self.cursor.rowcount if self.cursor else 0

    def close(self) -> None:
        """Close database connection safely."""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            
            if self.connection and not self.connection.closed:
                self.connection.close()
                self.connection = None
                
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close()
