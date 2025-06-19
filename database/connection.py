# # database/connection.py
# import os
# import asyncio
# import logging
# from typing import Optional, Dict, Any
# from contextlib import asynccontextmanager
# import psycopg2
# from psycopg2.extras import RealDictCursor
# from dataclasses import dataclass

# logger = logging.getLogger(__name__)

# @dataclass
# class DatabaseConfig:
#     """Database configuration parameters"""
#     host: str = "localhost"
#     port: int = 5432
#     database: str = "temperature_db"  # Updated to match your database
#     username: str = "tm_user"         # Updated to match your user
#     password: str = "tm_pass"         # Updated to match your password
    
#     @classmethod
#     def from_env(cls) -> 'DatabaseConfig':
#         """Load configuration from environment variables"""
#         return cls(
#             host=os.getenv("DB_HOST", "localhost"),
#             port=int(os.getenv("DB_PORT", "5432")),
#             database=os.getenv("DB_NAME", "temperature_db"),  # Updated default
#             username=os.getenv("DB_USER", "tm_user"),         # Updated default
#             password=os.getenv("DB_PASSWORD", "tm_pass"),     # Updated default
#         )
    
#     @property
#     def connection_string(self) -> str:
#         """Get psycopg2 connection string"""
#         return f"host={self.host} port={self.port} dbname={self.database} user={self.username} password={self.password}"

# class DatabaseConnection:
#     """Database connection manager for synchronous operations"""
    
#     def __init__(self, config: Optional[DatabaseConfig] = None):
#         self.config = config or DatabaseConfig.from_env()
#         self._connection = None
    
#     def connect(self):
#         """Establish database connection"""
#         try:
#             self._connection = psycopg2.connect(
#                 self.config.connection_string,
#                 cursor_factory=RealDictCursor
#             )
#             self._connection.autocommit = False
#             logger.info("Database connection established")
#             return self._connection
#         except Exception as e:
#             logger.error(f"Failed to connect to database: {e}")
#             raise
    
#     def disconnect(self):
#         """Close database connection"""
#         if self._connection:
#             self._connection.close()
#             self._connection = None
#             logger.info("Database connection closed")
    
#     @property
#     def connection(self):
#         """Get current connection, establish if needed"""
#         if not self._connection or self._connection.closed:
#             self.connect()
#         return self._connection
    
#     def execute_query(self, query: str, params: tuple = None) -> list:
#         """Execute SELECT query and return results"""
#         with self.connection.cursor() as cursor:
#             cursor.execute(query, params)
#             return cursor.fetchall()
    
#     def execute_command(self, command: str, params: tuple = None) -> int:
#         """Execute INSERT/UPDATE/DELETE and return affected rows"""
#         with self.connection.cursor() as cursor:
#             cursor.execute(command, params)
#             affected = cursor.rowcount
#             self.connection.commit()
#             return affected
    
#     def execute_script(self, script_path: str):
#         """Execute SQL script file"""
#         with open(script_path, 'r') as f:
#             script = f.read()
        
#         with self.connection.cursor() as cursor:
#             cursor.execute(script)
#             self.connection.commit()
#             logger.info(f"Executed script: {script_path}")

# def test_connection():
#     """Test database connectivity"""
#     try:
#         conn = DatabaseConnection()
#         result = conn.execute_query("SELECT 1 as test")
#         print(f"✅ Database connection successful: {result}")
#         conn.disconnect()
#         return True
#     except Exception as e:
#         print(f"❌ Database connection failed: {e}")
#         return False

# if __name__ == "__main__":
#     test_connection()



import os
import asyncpg
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(
        self,
        host: str = os.getenv("DB_HOST", "localhost"),
        port: int = int(os.getenv("DB_PORT", "5432")),
        database: str = os.getenv("DB_NAME", "temperature_db"),
        username: str = os.getenv("DB_USER", "tm_user"),
        password: str = os.getenv("DB_PASSWORD", "tm_pass"),
    ):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.pool = None

    async def connect(self):
        """Create a connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                min_size=5,  # Minimum connections in pool
                max_size=20,  # Maximum connections in pool
            )
            logger.info(f"Connected to database {self.database} at {self.host}:{self.port}")
            return self.pool
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def close(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    async def execute(self, query: str, *args, timeout: Optional[float] = None) -> str:
        """Execute a SQL query"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args, timeout=timeout)

    async def fetch(self, query: str, *args, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """Fetch records from the database"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args, timeout=timeout)
            return [dict(row) for row in rows]

    async def fetchrow(self, query: str, *args, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Fetch a single record from the database"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, *args, timeout=timeout)
            return dict(row) if row else None

    async def fetchval(self, query: str, *args, column: int = 0, timeout: Optional[float] = None) -> Any:
        """Fetch a single value from the database"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args, column=column, timeout=timeout)

    async def transaction(self):
        """Create a transaction context manager"""
        if not self.pool:
            await self.connect()
        
        return self.pool.acquire()


# Database singleton instance
db = DatabaseConnection()