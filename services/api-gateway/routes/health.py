"""
Health check routes with comprehensive service monitoring
"""

from fastapi import APIRouter, HTTPException, status
from datetime import datetime
import asyncio
import structlog

from models import HealthResponse
from database import get_db_connection, get_redis_client
from health_monitor import health_monitor

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

@router.get("/services")
async def get_services_health():
    """Get health status of all microservices"""
    services_status = health_monitor.get_all_services_status()
    system_healthy = health_monitor.is_system_healthy()
    
    return {
        "timestamp": datetime.utcnow(),
        "system_healthy": system_healthy,
        "services": services_status,
        "summary": {
            "total_services": len(services_status),
            "healthy_services": sum(1 for s in services_status.values() if s["status"] == "healthy"),
            "unhealthy_services": sum(1 for s in services_status.values() if s["status"] == "unhealthy")
        }
    }

@router.get("/services/{service_name}")
async def get_service_health(service_name: str):
    """Get health status of a specific service"""
    service_health = health_monitor.get_service_status(service_name)
    
    if not service_health:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found"
        )
    
    return {
        "service": service_name,
        "status": service_health.status.value,
        "last_check": service_health.last_check.isoformat() if service_health.last_check else None,
        "response_time": service_health.response_time,
        "error_message": service_health.error_message,
        "consecutive_failures": service_health.consecutive_failures,
        "uptime_percentage": service_health.uptime_percentage,
        "url": service_health.url
    }

@router.post("/services/check")
async def trigger_health_check():
    """Manually trigger health check for all services"""
    await health_monitor.check_all_services()
    return {
        "message": "Health check triggered",
        "timestamp": datetime.utcnow()
    }

@router.get("/readiness")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    system_healthy = health_monitor.is_system_healthy()
    
    if not system_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System not ready"
        )
    
    return {"status": "ready"}

@router.get("/liveness")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    # Simple check that the API gateway itself is alive
    return {"status": "alive", "timestamp": datetime.utcnow()}

@router.post("/validate-flows")
async def validate_data_flows():
    """Validate end-to-end data flows across all services"""
    from data_flow_validator import data_flow_validator
    
    try:
        flows_results = await data_flow_validator.validate_all_flows()
        
        # Calculate summary statistics
        total_flows = len(flows_results)
        successful_flows = 0
        total_steps = 0
        successful_steps = 0
        
        for flow_name, results in flows_results.items():
            total_steps += len(results)
            flow_success_count = sum(1 for r in results if r.status.value == "success")
            successful_steps += flow_success_count
            
            # Consider flow successful if all steps succeed
            if flow_success_count == len(results):
                successful_flows += 1
        
        return {
            "timestamp": datetime.utcnow(),
            "summary": {
                "total_flows": total_flows,
                "successful_flows": successful_flows,
                "total_steps": total_steps,
                "successful_steps": successful_steps,
                "flow_success_rate": f"{(successful_flows/total_flows)*100:.1f}%",
                "step_success_rate": f"{(successful_steps/total_steps)*100:.1f}%"
            },
            "flows": {
                flow_name: [
                    {
                        "service": r.step.service,
                        "endpoint": r.step.endpoint,
                        "status": r.status.value,
                        "response_time_ms": r.response_time,
                        "error": r.error_message
                    }
                    for r in results
                ]
                for flow_name, results in flows_results.items()
            }
        }
        
    except Exception as e:
        logger.error("Data flow validation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Flow validation failed: {str(e)}"
        )