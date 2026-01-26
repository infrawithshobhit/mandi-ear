"""
Progressive Synchronization Engine for offline cache service
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog
import json

from models import (
    SyncStatus, SyncResult, DataType, PriorityLevel, 
    SyncConfiguration, ConnectivityLevel
)
from cache_manager import CacheManager

logger = structlog.get_logger()

class ProgressiveSyncEngine:
    """Manages progressive data synchronization for offline cache"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.config = SyncConfiguration()
        self.current_status = SyncStatus.IDLE
        self.sync_task: Optional[asyncio.Task] = None
        self.last_sync: Optional[datetime] = None
        self.sync_history: List[SyncResult] = []
        self.connectivity_level = ConnectivityLevel.GOOD
        
        # Service endpoints
        self.service_endpoints = {
            "price_discovery": "http://price-discovery-service:8000",
            "msp_enforcement": "http://msp-enforcement-service:8000",
            "weather": "http://weather-service:8000",
            "crop_planning": "http://crop-planning-service:8000"
        }
    
    async def initialize(self):
        """Initialize the sync engine"""
        try:
            await self._detect_connectivity()
            logger.info("Sync engine initialized", connectivity=self.connectivity_level.value)
        except Exception as e:
            logger.error("Failed to initialize sync engine", error=str(e))
            raise
    
    async def shutdown(self):
        """Shutdown the sync engine"""
        if self.sync_task and not self.sync_task.done():
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass
        logger.info("Sync engine shutdown")
    
    async def start_background_sync(self):
        """Start background synchronization task"""
        if self.sync_task and not self.sync_task.done():
            logger.warning("Background sync already running")
            return
        
        self.sync_task = asyncio.create_task(self._background_sync_loop())
        logger.info("Background sync started")
    
    async def _background_sync_loop(self):
        """Background synchronization loop"""
        while True:
            try:
                await self._detect_connectivity()
                
                if self.connectivity_level != ConnectivityLevel.OFFLINE:
                    await self.run_sync_cycle()
                
                # Wait for next sync interval
                if self.connectivity_level == ConnectivityLevel.POOR:
                    wait_time = self.config.sync_interval_minutes * 2  # Longer intervals for poor connectivity
                else:
                    wait_time = self.config.sync_interval_minutes
                
                await asyncio.sleep(wait_time * 60)
                
            except asyncio.CancelledError:
                logger.info("Background sync cancelled")
                break
            except Exception as e:
                logger.error("Error in background sync loop", error=str(e))
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def run_sync_cycle(self) -> SyncResult:
        """Run a complete synchronization cycle"""
        sync_id = f"sync_{int(datetime.now().timestamp())}"
        sync_result = SyncResult(
            sync_id=sync_id,
            status=SyncStatus.SYNCING,
            started_at=datetime.now()
        )
        
        try:
            self.current_status = SyncStatus.SYNCING
            logger.info("Starting sync cycle", sync_id=sync_id)
            
            # Determine what to sync based on connectivity
            sync_priorities = await self._determine_sync_priorities()
            
            # Sync data by priority
            for priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH, PriorityLevel.MEDIUM]:
                if priority in sync_priorities:
                    await self._sync_priority_data(priority, sync_result)
                
                # Check if we should continue based on connectivity
                if self.connectivity_level == ConnectivityLevel.POOR and priority == PriorityLevel.HIGH:
                    logger.info("Stopping sync due to poor connectivity", sync_id=sync_id)
                    break
            
            # Clean up expired entries
            await self.cache_manager.cleanup_expired_entries()
            
            sync_result.status = SyncStatus.COMPLETED
            sync_result.completed_at = datetime.now()
            self.current_status = SyncStatus.COMPLETED
            self.last_sync = datetime.now()
            
            logger.info("Sync cycle completed", 
                       sync_id=sync_id, 
                       items_synced=sync_result.items_synced,
                       bytes_transferred=sync_result.bytes_transferred)
            
        except Exception as e:
            sync_result.status = SyncStatus.FAILED
            sync_result.errors.append(str(e))
            self.current_status = SyncStatus.FAILED
            logger.error("Sync cycle failed", sync_id=sync_id, error=str(e))
        
        finally:
            sync_result.completed_at = datetime.now()
            self.sync_history.append(sync_result)
            
            # Keep only last 100 sync results
            if len(self.sync_history) > 100:
                self.sync_history = self.sync_history[-100:]
        
        return sync_result
    
    async def _determine_sync_priorities(self) -> List[PriorityLevel]:
        """Determine what priorities to sync based on connectivity and cache state"""
        priorities = []
        
        if self.connectivity_level == ConnectivityLevel.OFFLINE:
            return priorities
        
        # Always sync critical data
        priorities.append(PriorityLevel.CRITICAL)
        
        if self.connectivity_level in [ConnectivityLevel.MODERATE, ConnectivityLevel.GOOD]:
            priorities.append(PriorityLevel.HIGH)
        
        if self.connectivity_level == ConnectivityLevel.GOOD:
            priorities.append(PriorityLevel.MEDIUM)
            priorities.append(PriorityLevel.LOW)
        
        return priorities
    
    async def _sync_priority_data(self, priority: PriorityLevel, sync_result: SyncResult):
        """Sync data for a specific priority level"""
        try:
            # Define what data types to sync for each priority
            priority_data_types = {
                PriorityLevel.CRITICAL: [DataType.PRICE_DATA, DataType.MSP_RATES],
                PriorityLevel.HIGH: [DataType.MANDI_INFO, DataType.WEATHER_DATA],
                PriorityLevel.MEDIUM: [DataType.CROP_RECOMMENDATIONS, DataType.MARKET_TRENDS],
                PriorityLevel.LOW: [DataType.USER_PREFERENCES]
            }
            
            data_types = priority_data_types.get(priority, [])
            
            for data_type in data_types:
                try:
                    await self._sync_data_type(data_type, priority, sync_result)
                except Exception as e:
                    sync_result.errors.append(f"Failed to sync {data_type.value}: {str(e)}")
                    sync_result.items_failed += 1
                    logger.error("Failed to sync data type", 
                               data_type=data_type.value, 
                               priority=priority.value, 
                               error=str(e))
        
        except Exception as e:
            logger.error("Failed to sync priority data", priority=priority.value, error=str(e))
            raise
    
    async def _sync_data_type(self, data_type: DataType, priority: PriorityLevel, sync_result: SyncResult):
        """Sync a specific data type"""
        try:
            if data_type == DataType.PRICE_DATA:
                await self._sync_price_data(priority, sync_result)
            elif data_type == DataType.MANDI_INFO:
                await self._sync_mandi_info(priority, sync_result)
            elif data_type == DataType.MSP_RATES:
                await self._sync_msp_rates(priority, sync_result)
            elif data_type == DataType.WEATHER_DATA:
                await self._sync_weather_data(priority, sync_result)
            elif data_type == DataType.CROP_RECOMMENDATIONS:
                await self._sync_crop_recommendations(priority, sync_result)
            elif data_type == DataType.MARKET_TRENDS:
                await self._sync_market_trends(priority, sync_result)
            
            sync_result.data_types_synced.append(data_type)
            
        except Exception as e:
            logger.error("Failed to sync data type", data_type=data_type.value, error=str(e))
            raise
    
    async def _sync_price_data(self, priority: PriorityLevel, sync_result: SyncResult):
        """Sync price data from price discovery service"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get top commodities for critical data
                commodities = ["wheat", "rice", "onion", "potato", "tomato"] if priority == PriorityLevel.CRITICAL else []
                
                for commodity in commodities:
                    try:
                        url = f"{self.service_endpoints['price_discovery']}/prices/{commodity}"
                        async with session.get(url, timeout=30) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                for price_point in data:
                                    cache_id = await self.cache_manager.cache_data(
                                        data_type=DataType.PRICE_DATA,
                                        content=price_point,
                                        priority=priority,
                                        expires_in_hours=self.config.max_age_hours[DataType.PRICE_DATA]
                                    )
                                    sync_result.items_synced += 1
                                    sync_result.bytes_transferred += len(json.dumps(price_point).encode())
                    
                    except Exception as e:
                        logger.warning("Failed to sync commodity prices", commodity=commodity, error=str(e))
                        sync_result.items_failed += 1
        
        except Exception as e:
            logger.error("Failed to sync price data", error=str(e))
            raise
    
    async def _sync_mandi_info(self, priority: PriorityLevel, sync_result: SyncResult):
        """Sync mandi information"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.service_endpoints['price_discovery']}/mandis"
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        mandis = await response.json()
                        
                        for mandi in mandis:
                            cache_id = await self.cache_manager.cache_data(
                                data_type=DataType.MANDI_INFO,
                                content=mandi,
                                priority=priority,
                                expires_in_hours=self.config.max_age_hours[DataType.MANDI_INFO]
                            )
                            sync_result.items_synced += 1
                            sync_result.bytes_transferred += len(json.dumps(mandi).encode())
        
        except Exception as e:
            logger.error("Failed to sync mandi info", error=str(e))
            raise
    
    async def _sync_msp_rates(self, priority: PriorityLevel, sync_result: SyncResult):
        """Sync MSP rates"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.service_endpoints['msp_enforcement']}/msp/rates"
                async with session.get(url, timeout=30) as response:
                    if response.status == 200:
                        msp_data = await response.json()
                        
                        cache_id = await self.cache_manager.cache_data(
                            data_type=DataType.MSP_RATES,
                            content=msp_data,
                            priority=priority,
                            expires_in_hours=self.config.max_age_hours[DataType.MSP_RATES]
                        )
                        sync_result.items_synced += 1
                        sync_result.bytes_transferred += len(json.dumps(msp_data).encode())
        
        except Exception as e:
            logger.error("Failed to sync MSP rates", error=str(e))
            raise
    
    async def _sync_weather_data(self, priority: PriorityLevel, sync_result: SyncResult):
        """Sync weather data"""
        try:
            # Mock weather data sync - in real implementation, this would call weather service
            weather_data = {
                "temperature": 25.5,
                "humidity": 65,
                "rainfall": 0.0,
                "forecast": "Clear skies",
                "timestamp": datetime.now().isoformat()
            }
            
            cache_id = await self.cache_manager.cache_data(
                data_type=DataType.WEATHER_DATA,
                content=weather_data,
                priority=priority,
                expires_in_hours=self.config.max_age_hours[DataType.WEATHER_DATA]
            )
            sync_result.items_synced += 1
            sync_result.bytes_transferred += len(json.dumps(weather_data).encode())
        
        except Exception as e:
            logger.error("Failed to sync weather data", error=str(e))
            raise
    
    async def _sync_crop_recommendations(self, priority: PriorityLevel, sync_result: SyncResult):
        """Sync crop recommendations"""
        try:
            # Mock crop recommendations - in real implementation, this would call crop planning service
            recommendations = {
                "season": "kharif",
                "recommended_crops": ["rice", "cotton", "sugarcane"],
                "risk_factors": ["drought", "pest_attack"],
                "timestamp": datetime.now().isoformat()
            }
            
            cache_id = await self.cache_manager.cache_data(
                data_type=DataType.CROP_RECOMMENDATIONS,
                content=recommendations,
                priority=priority,
                expires_in_hours=self.config.max_age_hours[DataType.CROP_RECOMMENDATIONS]
            )
            sync_result.items_synced += 1
            sync_result.bytes_transferred += len(json.dumps(recommendations).encode())
        
        except Exception as e:
            logger.error("Failed to sync crop recommendations", error=str(e))
            raise
    
    async def _sync_market_trends(self, priority: PriorityLevel, sync_result: SyncResult):
        """Sync market trends"""
        try:
            # Mock market trends - in real implementation, this would call analytics service
            trends = {
                "trending_up": ["wheat", "rice"],
                "trending_down": ["onion", "potato"],
                "stable": ["tomato", "cotton"],
                "timestamp": datetime.now().isoformat()
            }
            
            cache_id = await self.cache_manager.cache_data(
                data_type=DataType.MARKET_TRENDS,
                content=trends,
                priority=priority,
                expires_in_hours=self.config.max_age_hours[DataType.MARKET_TRENDS]
            )
            sync_result.items_synced += 1
            sync_result.bytes_transferred += len(json.dumps(trends).encode())
        
        except Exception as e:
            logger.error("Failed to sync market trends", error=str(e))
            raise
    
    async def _detect_connectivity(self):
        """Detect current network connectivity level"""
        try:
            # Simple connectivity test - ping a reliable service
            async with aiohttp.ClientSession() as session:
                start_time = datetime.now()
                try:
                    async with session.get("http://api-gateway:8000/health", timeout=5) as response:
                        end_time = datetime.now()
                        response_time = (end_time - start_time).total_seconds()
                        
                        if response.status == 200:
                            if response_time < 1.0:
                                self.connectivity_level = ConnectivityLevel.GOOD
                            elif response_time < 3.0:
                                self.connectivity_level = ConnectivityLevel.MODERATE
                            else:
                                self.connectivity_level = ConnectivityLevel.POOR
                        else:
                            self.connectivity_level = ConnectivityLevel.POOR
                
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    self.connectivity_level = ConnectivityLevel.OFFLINE
        
        except Exception as e:
            logger.warning("Failed to detect connectivity", error=str(e))
            self.connectivity_level = ConnectivityLevel.OFFLINE
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        return {
            "current_status": self.current_status.value,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "connectivity_level": self.connectivity_level.value,
            "sync_interval_minutes": self.config.sync_interval_minutes,
            "recent_syncs": [
                {
                    "sync_id": result.sync_id,
                    "status": result.status.value,
                    "started_at": result.started_at.isoformat(),
                    "completed_at": result.completed_at.isoformat() if result.completed_at else None,
                    "items_synced": result.items_synced,
                    "items_failed": result.items_failed,
                    "errors": result.errors
                }
                for result in self.sync_history[-5:]  # Last 5 syncs
            ]
        }
    
    async def configure_sync(
        self, 
        sync_interval_minutes: int = 15,
        priority_data_interval_minutes: int = 5,
        max_cache_size_mb: int = 100
    ):
        """Configure synchronization settings"""
        self.config.sync_interval_minutes = sync_interval_minutes
        self.config.priority_data_interval_minutes = priority_data_interval_minutes
        self.config.max_cache_size_mb = max_cache_size_mb
        
        logger.info("Sync configuration updated", 
                   sync_interval=sync_interval_minutes,
                   priority_interval=priority_data_interval_minutes,
                   max_cache_size=max_cache_size_mb)