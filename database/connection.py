# # database/connection.py

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



db = DatabaseConnection()