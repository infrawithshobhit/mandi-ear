"""
MANDI EAR™ Offline Cache Service
Local data caching and progressive synchronization for offline access
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from contextlib import asynccontextmanager
import structlog
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
import sqlite3
import aiosqlite
from pathlib import Path

from models import CachedData, SyncStatus, PriorityLevel, OfflineQuery
from cache_manager import CacheManager
from sync_engine import ProgressiveSyncEngine
from priority_manager import EssentialDataPrioritizer

logger = structlog.get_logger()

# Global service instances
cache_manager: Optional[CacheManager] = None
sync_engine: Optional[ProgressiveSyncEngine] = None
priority_manager: Optional[EssentialDataPrioritizer] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global cache_manager, sync_engine, priority_manager
    
    # Startup
    logger.info("Starting Offline Cache Service")
    
    # Initialize cache directory
    cache_dir = Path("./cache")
    cache_dir.mkdir(exist_ok=True)
    
    # Initialize services
    cache_manager = CacheManager(cache_dir)
    await cache_manager.initialize()
    
    sync_engine = ProgressiveSyncEngine(cache_manager)
    await sync_engine.initialize()
    
    priority_manager = EssentialDataPrioritizer()
    
    # Start background sync task
    asyncio.create_task(sync_engine.start_background_sync())
    
    yield
    
    # Shutdown
    logger.info("Shutting down Offline Cache Service")
    if sync_engine:
        await sync_engine.shutdown()
    if cache_manager:
        await cache_manager.close()

app = FastAPI(
    title="MANDI EAR™ Offline Cache Service",
    description="Local data caching and offline access management",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "service": "Offline Cache Service",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not cache_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    cache_stats = await cache_manager.get_cache_statistics()
    sync_status = await sync_engine.get_sync_status() if sync_engine else None
    
    return {
        "status": "healthy",
        "cache_stats": cache_stats,
        "sync_status": sync_status
    }

@app.get("/cache/prices/{commodity}")
async def get_cached_prices(
    commodity: str,
    state: Optional[str] = None,
    max_age_hours: int = 24
) -> List[Dict[str, Any]]:
    """Get cached price data for offline access"""
    if not cache_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        cached_data = await cache_manager.get_cached_prices(
            commodity=commodity,
            state=state,
            max_age_hours=max_age_hours
        )
        return cached_data
    except Exception as e:
        logger.error("Failed to get cached prices", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/cache/mandis")
async def get_cached_mandis(state: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get cached mandi information"""
    if not cache_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        cached_mandis = await cache_manager.get_cached_mandis(state)
        return cached_mandis
    except Exception as e:
        logger.error("Failed to get cached mandis", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/cache/query")
async def cache_offline_query(query: OfflineQuery):
    """Cache a query for offline processing"""
    if not cache_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        query_id = await cache_manager.cache_query(query)
        return {"query_id": query_id, "status": "cached"}
    except Exception as e:
        logger.error("Failed to cache query", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/cache/essential")
async def get_essential_data(
    location_lat: float,
    location_lng: float,
    radius_km: float = 50
) -> Dict[str, Any]:
    """Get essential cached data for poor connectivity scenarios"""
    if not priority_manager or not cache_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        essential_data = await priority_manager.get_essential_data(
            cache_manager=cache_manager,
            location_lat=location_lat,
            location_lng=location_lng,
            radius_km=radius_km
        )
        return essential_data
    except Exception as e:
        logger.error("Failed to get essential data", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/sync/trigger")
async def trigger_sync(background_tasks: BackgroundTasks):
    """Manually trigger data synchronization"""
    if not sync_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    background_tasks.add_task(sync_engine.run_sync_cycle)
    return {"message": "Sync triggered"}

@app.get("/sync/status")
async def get_sync_status() -> Dict[str, Any]:
    """Get current synchronization status"""
    if not sync_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        status = await sync_engine.get_sync_status()
        return status
    except Exception as e:
        logger.error("Failed to get sync status", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/sync/configure")
async def configure_sync(
    sync_interval_minutes: int = 15,
    priority_data_interval_minutes: int = 5,
    max_cache_size_mb: int = 100
):
    """Configure synchronization settings"""
    if not sync_engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        await sync_engine.configure_sync(
            sync_interval_minutes=sync_interval_minutes,
            priority_data_interval_minutes=priority_data_interval_minutes,
            max_cache_size_mb=max_cache_size_mb
        )
        return {"message": "Sync configuration updated"}
    except Exception as e:
        logger.error("Failed to configure sync", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/cache/stats")
async def get_cache_statistics() -> Dict[str, Any]:
    """Get detailed cache statistics"""
    if not cache_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        stats = await cache_manager.get_detailed_statistics()
        return stats
    except Exception as e:
        logger.error("Failed to get cache statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/cache/clear")
async def clear_cache(
    older_than_hours: Optional[int] = None,
    data_type: Optional[str] = None
):
    """Clear cached data"""
    if not cache_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        cleared_count = await cache_manager.clear_cache(
            older_than_hours=older_than_hours,
            data_type=data_type
        )
        return {"message": f"Cleared {cleared_count} cache entries"}
    except Exception as e:
        logger.error("Failed to clear cache", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/offline/prepare")
async def prepare_offline_data(
    user_location_lat: float,
    user_location_lng: float,
    commodities: List[str],
    radius_km: float = 100
):
    """Prepare essential data for offline use"""
    if not cache_manager or not priority_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        preparation_id = await priority_manager.prepare_offline_data(
            cache_manager=cache_manager,
            user_location_lat=user_location_lat,
            user_location_lng=user_location_lng,
            commodities=commodities,
            radius_km=radius_km
        )
        return {"preparation_id": preparation_id, "status": "preparing"}
    except Exception as e:
        logger.error("Failed to prepare offline data", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/offline/status/{preparation_id}")
async def get_offline_preparation_status(preparation_id: str):
    """Get status of offline data preparation"""
    if not priority_manager:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    try:
        status = await priority_manager.get_preparation_status(preparation_id)
        return status
    except Exception as e:
        logger.error("Failed to get preparation status", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")