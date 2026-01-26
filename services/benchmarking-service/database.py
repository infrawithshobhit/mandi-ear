"""
Database configuration for Benchmarking Service
"""

import asyncio
from typing import Optional
import structlog

logger = structlog.get_logger()

class DatabaseConnection:
    """
    Database connection manager for benchmarking service
    """
    
    def __init__(self):
        """Initialize database connection"""
        self.connected = False
        logger.info("Database connection initialized")
    
    async def connect(self):
        """Connect to database"""
        # Simulate database connection
        await asyncio.sleep(0.1)
        self.connected = True
        logger.info("Connected to database")
    
    async def disconnect(self):
        """Disconnect from database"""
        # Simulate database disconnection
        await asyncio.sleep(0.05)
        self.connected = False
        logger.info("Disconnected from database")
    
    def is_connected(self) -> bool:
        """Check if connected to database"""
        return self.connected

# Global database connection
_db_connection: Optional[DatabaseConnection] = None

async def get_database():
    """
    Get database connection (dependency injection)
    
    Returns:
        Database connection instance
    """
    global _db_connection
    
    if _db_connection is None:
        _db_connection = DatabaseConnection()
        await _db_connection.connect()
    
    if not _db_connection.is_connected():
        await _db_connection.connect()
    
    return _db_connection

async def close_database():
    """Close database connection"""
    global _db_connection
    
    if _db_connection and _db_connection.is_connected():
        await _db_connection.disconnect()
        _db_connection = None