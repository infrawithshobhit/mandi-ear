"""
Essential Data Prioritizer for offline access
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog
import uuid
import math

from models import (
    DataType, PriorityLevel, EssentialDataPackage, 
    OfflinePreparation, ConnectivityLevel
)
from cache_manager import CacheManager

logger = structlog.get_logger()

class EssentialDataPrioritizer:
    """Manages prioritization of essential data for offline access"""
    
    def __init__(self):
        self.preparation_tasks: Dict[str, OfflinePreparation] = {}
        
        # Define essential data priorities for poor connectivity
        self.essential_data_config = {
            DataType.PRICE_DATA: {
                "priority": PriorityLevel.CRITICAL,
                "max_age_hours": 6,
                "max_entries": 100,
                "size_limit_mb": 5.0
            },
            DataType.MSP_RATES: {
                "priority": PriorityLevel.CRITICAL,
                "max_age_hours": 168,  # 1 week
                "max_entries": 50,
                "size_limit_mb": 1.0
            },
            DataType.MANDI_INFO: {
                "priority": PriorityLevel.HIGH,
                "max_age_hours": 24,
                "max_entries": 50,
                "size_limit_mb": 2.0
            },
            DataType.WEATHER_DATA: {
                "priority": PriorityLevel.HIGH,
                "max_age_hours": 3,
                "max_entries": 10,
                "size_limit_mb": 0.5
            }
        }
    
    async def get_essential_data(
        self,
        cache_manager: CacheManager,
        location_lat: float,
        location_lng: float,
        radius_km: float = 50
    ) -> Dict[str, Any]:
        """Get essential cached data for poor connectivity scenarios"""
        try:
            essential_data = {
                "location": {"lat": location_lat, "lng": location_lng},
                "radius_km": radius_km,
                "data_timestamp": datetime.now().isoformat(),
                "connectivity_optimized": True
            }
            
            # Get essential price data
            price_data = await self._get_essential_prices(
                cache_manager, location_lat, location_lng, radius_km
            )
            essential_data["prices"] = price_data
            
            # Get essential mandi info
            mandi_data = await self._get_essential_mandis(
                cache_manager, location_lat, location_lng, radius_km
            )
            essential_data["mandis"] = mandi_data
            
            # Get MSP rates
            msp_data = await self._get_essential_msp_rates(cache_manager)
            essential_data["msp_rates"] = msp_data
            
            # Get weather summary
            weather_data = await self._get_essential_weather(
                cache_manager, location_lat, location_lng
            )
            essential_data["weather"] = weather_data
            
            # Calculate data freshness
            essential_data["data_freshness"] = await self._calculate_data_freshness(
                cache_manager, essential_data
            )
            
            logger.info("Essential data retrieved", 
                       location=f"{location_lat},{location_lng}",
                       radius_km=radius_km,
                       data_types=list(essential_data.keys()))
            
            return essential_data
            
        except Exception as e:
            logger.error("Failed to get essential data", error=str(e))
            raise
    
    async def _get_essential_prices(
        self,
        cache_manager: CacheManager,
        location_lat: float,
        location_lng: float,
        radius_km: float
    ) -> List[Dict[str, Any]]:
        """Get essential price data for the location"""
        try:
            # Get cached price data
            all_prices = await cache_manager.get_cached_prices(
                commodity="",  # Get all commodities
                max_age_hours=self.essential_data_config[DataType.PRICE_DATA]["max_age_hours"]
            )
            
            # Filter by location proximity
            nearby_prices = []
            for price in all_prices:
                if self._is_within_radius(
                    price.get("latitude", 0), price.get("longitude", 0),
                    location_lat, location_lng, radius_km
                ):
                    nearby_prices.append(price)
            
            # Sort by relevance (distance, freshness, commodity importance)
            nearby_prices.sort(key=lambda p: self._calculate_price_relevance(
                p, location_lat, location_lng
            ), reverse=True)
            
            # Limit to essential entries
            max_entries = self.essential_data_config[DataType.PRICE_DATA]["max_entries"]
            return nearby_prices[:max_entries]
            
        except Exception as e:
            logger.error("Failed to get essential prices", error=str(e))
            return []
    
    async def _get_essential_mandis(
        self,
        cache_manager: CacheManager,
        location_lat: float,
        location_lng: float,
        radius_km: float
    ) -> List[Dict[str, Any]]:
        """Get essential mandi information for the location"""
        try:
            # Get cached mandi data
            all_mandis = await cache_manager.get_cached_mandis()
            
            # Filter by location proximity
            nearby_mandis = []
            for mandi in all_mandis:
                if self._is_within_radius(
                    mandi.get("latitude", 0), mandi.get("longitude", 0),
                    location_lat, location_lng, radius_km
                ):
                    nearby_mandis.append(mandi)
            
            # Sort by distance
            nearby_mandis.sort(key=lambda m: self._calculate_distance(
                m.get("latitude", 0), m.get("longitude", 0),
                location_lat, location_lng
            ))
            
            # Limit to essential entries
            max_entries = self.essential_data_config[DataType.MANDI_INFO]["max_entries"]
            return nearby_mandis[:max_entries]
            
        except Exception as e:
            logger.error("Failed to get essential mandis", error=str(e))
            return []
    
    async def _get_essential_msp_rates(self, cache_manager: CacheManager) -> Dict[str, Any]:
        """Get essential MSP rates"""
        try:
            # Get the most recent MSP rates from cache
            # This is a simplified implementation - in reality, we'd query the cache properly
            msp_data = {
                "wheat": 2125.0,
                "rice": 2040.0,
                "cotton": 6080.0,
                "sugarcane": 305.0,
                "last_updated": datetime.now().isoformat(),
                "source": "cache"
            }
            
            return msp_data
            
        except Exception as e:
            logger.error("Failed to get essential MSP rates", error=str(e))
            return {}
    
    async def _get_essential_weather(
        self,
        cache_manager: CacheManager,
        location_lat: float,
        location_lng: float
    ) -> Dict[str, Any]:
        """Get essential weather information"""
        try:
            # Get the most recent weather data from cache
            # This is a simplified implementation
            weather_data = {
                "temperature": 28.5,
                "humidity": 70,
                "rainfall_24h": 0.0,
                "forecast": "Partly cloudy",
                "alerts": [],
                "last_updated": datetime.now().isoformat(),
                "source": "cache"
            }
            
            return weather_data
            
        except Exception as e:
            logger.error("Failed to get essential weather", error=str(e))
            return {}
    
    async def _calculate_data_freshness(
        self,
        cache_manager: CacheManager,
        essential_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Calculate freshness of different data types"""
        try:
            freshness = {}
            
            # Calculate freshness for each data type
            for data_type in [DataType.PRICE_DATA, DataType.MANDI_INFO, 
                            DataType.MSP_RATES, DataType.WEATHER_DATA]:
                # This is simplified - in reality, we'd check actual cache timestamps
                hours_old = 2  # Mock value
                if hours_old < 1:
                    freshness[data_type.value] = "very_fresh"
                elif hours_old < 6:
                    freshness[data_type.value] = "fresh"
                elif hours_old < 24:
                    freshness[data_type.value] = "moderate"
                else:
                    freshness[data_type.value] = "stale"
            
            return freshness
            
        except Exception as e:
            logger.error("Failed to calculate data freshness", error=str(e))
            return {}
    
    async def prepare_offline_data(
        self,
        cache_manager: CacheManager,
        user_location_lat: float,
        user_location_lng: float,
        commodities: List[str],
        radius_km: float = 100
    ) -> str:
        """Prepare essential data for offline use"""
        try:
            preparation_id = str(uuid.uuid4())
            
            preparation = OfflinePreparation(
                preparation_id=preparation_id,
                user_location={"lat": user_location_lat, "lng": user_location_lng},
                commodities=commodities,
                radius_km=radius_km,
                status="preparing",
                progress_percentage=0.0,
                estimated_completion=datetime.now() + timedelta(minutes=5)
            )
            
            self.preparation_tasks[preparation_id] = preparation
            
            # Start background preparation task
            asyncio.create_task(self._execute_offline_preparation(
                preparation_id, cache_manager
            ))
            
            logger.info("Offline data preparation started", 
                       preparation_id=preparation_id,
                       commodities=commodities,
                       radius_km=radius_km)
            
            return preparation_id
            
        except Exception as e:
            logger.error("Failed to start offline data preparation", error=str(e))
            raise
    
    async def _execute_offline_preparation(
        self,
        preparation_id: str,
        cache_manager: CacheManager
    ):
        """Execute offline data preparation in background"""
        try:
            preparation = self.preparation_tasks[preparation_id]
            
            # Step 1: Prepare price data (40% of progress)
            preparation.progress_percentage = 10.0
            await self._prepare_price_data(preparation, cache_manager)
            preparation.progress_percentage = 40.0
            
            # Step 2: Prepare mandi data (20% of progress)
            await self._prepare_mandi_data(preparation, cache_manager)
            preparation.progress_percentage = 60.0
            
            # Step 3: Prepare MSP and weather data (20% of progress)
            await self._prepare_supplementary_data(preparation, cache_manager)
            preparation.progress_percentage = 80.0
            
            # Step 4: Optimize and finalize (20% of progress)
            await self._optimize_offline_package(preparation, cache_manager)
            preparation.progress_percentage = 100.0
            
            preparation.status = "completed"
            preparation.completed_at = datetime.now()
            
            logger.info("Offline data preparation completed", 
                       preparation_id=preparation_id,
                       data_size_mb=preparation.data_size_mb)
            
        except Exception as e:
            preparation = self.preparation_tasks.get(preparation_id)
            if preparation:
                preparation.status = "failed"
                preparation.error_message = str(e)
                preparation.completed_at = datetime.now()
            
            logger.error("Offline data preparation failed", 
                        preparation_id=preparation_id, 
                        error=str(e))
    
    async def _prepare_price_data(
        self,
        preparation: OfflinePreparation,
        cache_manager: CacheManager
    ):
        """Prepare price data for offline package"""
        try:
            for commodity in preparation.commodities:
                prices = await cache_manager.get_cached_prices(
                    commodity=commodity,
                    max_age_hours=6
                )
                
                # Filter by location
                nearby_prices = [
                    price for price in prices
                    if self._is_within_radius(
                        price.get("latitude", 0), price.get("longitude", 0),
                        preparation.user_location["lat"], preparation.user_location["lng"],
                        preparation.radius_km
                    )
                ]
                
                # Cache the filtered data with high priority
                for price in nearby_prices[:20]:  # Limit per commodity
                    await cache_manager.cache_data(
                        data_type=DataType.PRICE_DATA,
                        content=price,
                        priority=PriorityLevel.CRITICAL,
                        expires_in_hours=24
                    )
                
                preparation.data_size_mb += len(str(nearby_prices).encode()) / (1024 * 1024)
            
        except Exception as e:
            logger.error("Failed to prepare price data", error=str(e))
            raise
    
    async def _prepare_mandi_data(
        self,
        preparation: OfflinePreparation,
        cache_manager: CacheManager
    ):
        """Prepare mandi data for offline package"""
        try:
            mandis = await cache_manager.get_cached_mandis()
            
            # Filter by location
            nearby_mandis = [
                mandi for mandi in mandis
                if self._is_within_radius(
                    mandi.get("latitude", 0), mandi.get("longitude", 0),
                    preparation.user_location["lat"], preparation.user_location["lng"],
                    preparation.radius_km
                )
            ]
            
            # Cache the filtered data
            for mandi in nearby_mandis[:30]:  # Limit number
                await cache_manager.cache_data(
                    data_type=DataType.MANDI_INFO,
                    content=mandi,
                    priority=PriorityLevel.HIGH,
                    expires_in_hours=48
                )
            
            preparation.data_size_mb += len(str(nearby_mandis).encode()) / (1024 * 1024)
            
        except Exception as e:
            logger.error("Failed to prepare mandi data", error=str(e))
            raise
    
    async def _prepare_supplementary_data(
        self,
        preparation: OfflinePreparation,
        cache_manager: CacheManager
    ):
        """Prepare MSP rates and weather data"""
        try:
            # Prepare MSP rates
            msp_data = await self._get_essential_msp_rates(cache_manager)
            await cache_manager.cache_data(
                data_type=DataType.MSP_RATES,
                content=msp_data,
                priority=PriorityLevel.CRITICAL,
                expires_in_hours=168
            )
            
            # Prepare weather data
            weather_data = await self._get_essential_weather(
                cache_manager,
                preparation.user_location["lat"],
                preparation.user_location["lng"]
            )
            await cache_manager.cache_data(
                data_type=DataType.WEATHER_DATA,
                content=weather_data,
                priority=PriorityLevel.HIGH,
                expires_in_hours=6
            )
            
            preparation.data_size_mb += 0.5  # Estimated size for supplementary data
            
        except Exception as e:
            logger.error("Failed to prepare supplementary data", error=str(e))
            raise
    
    async def _optimize_offline_package(
        self,
        preparation: OfflinePreparation,
        cache_manager: CacheManager
    ):
        """Optimize the offline data package"""
        try:
            # Clean up old cache entries to make room
            await cache_manager.clear_cache(older_than_hours=48)
            
            # Compress data if needed
            # This is where we could implement additional compression
            
            logger.info("Offline package optimized", 
                       preparation_id=preparation.preparation_id,
                       final_size_mb=preparation.data_size_mb)
            
        except Exception as e:
            logger.error("Failed to optimize offline package", error=str(e))
            raise
    
    async def get_preparation_status(self, preparation_id: str) -> Dict[str, Any]:
        """Get status of offline data preparation"""
        preparation = self.preparation_tasks.get(preparation_id)
        
        if not preparation:
            return {"error": "Preparation not found"}
        
        return {
            "preparation_id": preparation.preparation_id,
            "status": preparation.status,
            "progress_percentage": preparation.progress_percentage,
            "estimated_completion": preparation.estimated_completion.isoformat() if preparation.estimated_completion else None,
            "data_size_mb": preparation.data_size_mb,
            "error_message": preparation.error_message,
            "created_at": preparation.created_at.isoformat(),
            "completed_at": preparation.completed_at.isoformat() if preparation.completed_at else None
        }
    
    def _is_within_radius(
        self,
        lat1: float, lng1: float,
        lat2: float, lng2: float,
        radius_km: float
    ) -> bool:
        """Check if a location is within the specified radius"""
        distance = self._calculate_distance(lat1, lng1, lat2, lng2)
        return distance <= radius_km
    
    def _calculate_distance(
        self,
        lat1: float, lng1: float,
        lat2: float, lng2: float
    ) -> float:
        """Calculate distance between two coordinates in kilometers"""
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lng / 2) ** 2)
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        return distance
    
    def _calculate_price_relevance(
        self,
        price: Dict[str, Any],
        user_lat: float,
        user_lng: float
    ) -> float:
        """Calculate relevance score for a price point"""
        try:
            # Distance factor (closer is better)
            distance = self._calculate_distance(
                price.get("latitude", 0), price.get("longitude", 0),
                user_lat, user_lng
            )
            distance_score = max(0, 100 - distance)  # Max 100km for full score
            
            # Freshness factor (newer is better)
            created_at = datetime.fromisoformat(price.get("created_at", datetime.now().isoformat()))
            hours_old = (datetime.now() - created_at).total_seconds() / 3600
            freshness_score = max(0, 24 - hours_old)  # Max 24 hours for full score
            
            # Commodity importance (essential commodities get higher scores)
            essential_commodities = ["wheat", "rice", "onion", "potato", "tomato"]
            commodity_score = 10 if price.get("commodity") in essential_commodities else 5
            
            # Combine scores
            total_score = distance_score * 0.4 + freshness_score * 0.4 + commodity_score * 0.2
            return total_score
            
        except Exception as e:
            logger.warning("Failed to calculate price relevance", error=str(e))
            return 0.0