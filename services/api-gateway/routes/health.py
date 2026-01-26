"""
Health check routes
"""

from fastapi import APIRouter
from datetime import datetime
import asyncio
import structlog

from models import HealthResponse
from database import get_db_connection, get_redis_client

logger = structlog.get_logger()
router = APIRouter()

@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint"""
    services = {}
    
    # Check PostgreSQL
    try:
        conn = await get_db_connection()
        await conn.fetchval("SELECT 1")
        await conn.close()
        services["postgresql"] = "healthy"
    except Exception as e:
        logger.error("PostgreSQL health check failed", error=str(e))
        services["postgresql"] = "unhealthy"
    
    # Check Redis
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        services["redis"] = "healthy"
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        services["redis"] = "unhealthy"
    
    # Overall status
    overall_status = "healthy" if all(
        status == "healthy" for status in services.values()
    ) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version="1.0.0",
        services=services
    )

@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with service connectivity"""
    checks = {}
    
    # Database connectivity check
    try:
        conn = await get_db_connection()
        result = await conn.fetchval("SELECT COUNT(*) FROM auth.users")
        await conn.close()
        checks["database"] = {
            "status": "healthy",
            "user_count": result,
            "response_time_ms": 0  # Would measure actual response time
        }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Redis connectivity check
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        info = await redis_client.info()
        checks["redis"] = {
            "status": "healthy",
            "connected_clients": info.get("connected_clients", 0),
            "used_memory": info.get("used_memory_human", "unknown")
        }
    except Exception as e:
        checks["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    return {
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "checks": checks
    }