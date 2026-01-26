"""
Database connection and session management
"""

import asyncpg
import redis.asyncio as redis
from typing import Optional
import structlog

from config import settings

logger = structlog.get_logger()

# Global connection pools
pg_pool: Optional[asyncpg.Pool] = None
redis_client: Optional[redis.Redis] = None

async def init_db():
    """Initialize database connections"""
    global pg_pool, redis_client
    
    try:
        # PostgreSQL connection pool
        pg_pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        logger.info("PostgreSQL connection pool created")
        
        # Redis connection
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        logger.info("Redis connection established")
        
    except Exception as e:
        logger.error("Failed to initialize database connections", error=str(e))
        raise

async def close_db():
    """Close database connections"""
    global pg_pool, redis_client
    
    if pg_pool:
        await pg_pool.close()
        logger.info("PostgreSQL connection pool closed")
    
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")

async def get_db_connection():
    """Get database connection from pool"""
    if not pg_pool:
        raise RuntimeError("Database pool not initialized")
    return await pg_pool.acquire()

async def get_redis_client():
    """Get Redis client"""
    if not redis_client:
        raise RuntimeError("Redis client not initialized")
    return redis_client