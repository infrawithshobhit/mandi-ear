"""
Data Ingestion Pipeline for Price Discovery Service
Handles multiple data sources and real-time streaming
"""

import asyncio
import aiohttp
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import re
from urllib.parse import urljoin

from models import (
    DataSource, DataSourceType, PricePoint, MandiInfo, 
    ValidationResult, IngestionStats, QualityGrade
)
from database import store_price_point, cache_price_data, get_cached_data
from validators import PriceDataValidator

logger = structlog.get_logger()

class DataIngestionPipeline:
    """Main data ingestion pipeline"""
    
    def __init__(self):
        self.data_sources: List[DataSource] = []
        self.validator = PriceDataValidator()
        self.session: Optional[aiohttp.ClientSession] = None
        self.ingestion_tasks: List[asyncio.Task] = []
        self.is_running = False
    
    async def initialize(self):
        """Initialize the pipeline"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        await self._load_data_sources()
        await self._start_ingestion_tasks()
        self.is_running = True
        logger.info("Data ingestion pipeline initialized")
    
    async def shutdown(self):
        """Shutdown the pipeline"""
        self.is_running = False
        
        # Cancel all ingestion tasks
        for task in self.ingestion_tasks:
            task.cancel()
        
        if self.ingestion_tasks:
            await asyncio.gather(*self.ingestion_tasks, return_exceptions=True)
        
        if self.session:
            await self.session.close()
        
        logger.info("Data ingestion pipeline shutdown")
    
    async def _load_data_sources(self):
        """Load configured data sources"""
        # Default government data sources
        self.data_sources = [
            DataSource(
                id="agmarknet",
                name="AgMarkNet Portal",
                type=DataSourceType.GOVERNMENT_PORTAL,
                url="https://agmarknet.gov.in/",
                update_frequency=15,
                reliability_score=0.9
            ),
            DataSource(
                id="enam",
                name="eNAM Portal",
                type=DataSourceType.GOVERNMENT_PORTAL,
                url="https://enam.gov.in/",
                update_frequency=15,
                reliability_score=0.85
            ),
            DataSource(
                id="state_portals",
                name="State Mandi Portals",
                type=DataSourceType.GOVERNMENT_PORTAL,
                url="",  # Multiple URLs
                update_frequency=30,
                reliability_score=0.8
            )
        ]
        logger.info("Loaded data sources", count=len(self.data_sources))
    
    async def _start_ingestion_tasks(self):
        """Start background ingestion tasks"""
        for source in self.data_sources:
            if source.is_active:
                task = asyncio.create_task(
                    self._ingestion_loop(source)
                )
                self.ingestion_tasks.append(task)
        
        logger.info("Started ingestion tasks", count=len(self.ingestion_tasks))
    
    async def _ingestion_loop(self, source: DataSource):
        """Main ingestion loop for a data source"""
        while self.is_running:
            try:
                await self._ingest_from_source(source)
                source.last_updated = datetime.utcnow()
                
                # Wait for next cycle
                await asyncio.sleep(source.update_frequency * 60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Error in ingestion loop", 
                    source_id=source.id, 
                    error=str(e)
                )
                await asyncio.sleep(60)  # Wait before retry
    
    async def _ingest_from_source(self, source: DataSource) -> IngestionStats:
        """Ingest data from a specific source"""
        start_time = datetime.utcnow()
        stats = IngestionStats(
            source_id=source.id,
            records_processed=0,
            records_validated=0,
            records_stored=0,
            errors=0,
            processing_time=0.0,
            timestamp=start_time
        )
        
        try:
            logger.info("Starting data ingestion", source_id=source.id)
            
            if source.type == DataSourceType.GOVERNMENT_PORTAL:
                raw_data = await self._fetch_government_data(source)
            else:
                logger.warning("Unsupported source type", source_type=source.type)
                return stats
            
            stats.records_processed = len(raw_data)
            
            # Process each record
            for record in raw_data:
                try:
                    # Validate data
                    validation_result = await self.validator.validate_price_data(record)
                    if validation_result.is_valid:
                        stats.records_validated += 1
                        
                        # Convert to PricePoint
                        price_point = await self._convert_to_price_point(
                            record, source, validation_result
                        )
                        
                        # Store in database
                        if await store_price_point(price_point):
                            stats.records_stored += 1
                        else:
                            stats.errors += 1
                    else:
                        stats.errors += 1
                        logger.warning(
                            "Data validation failed",
                            source_id=source.id,
                            issues=validation_result.issues
                        )
                
                except Exception as e:
                    stats.errors += 1
                    logger.error("Error processing record", error=str(e))
            
            # Update processing time
            stats.processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info(
                "Data ingestion completed",
                source_id=source.id,
                processed=stats.records_processed,
                stored=stats.records_stored,
                errors=stats.errors
            )
            
        except Exception as e:
            stats.errors += 1
            logger.error("Failed to ingest data", source_id=source.id, error=str(e))
        
        return stats
    
    async def _fetch_government_data(self, source: DataSource) -> List[Dict[str, Any]]:
        """Fetch data from government portals"""
        if not self.session:
            return []
        
        try:
            # Simulate government portal data fetching
            # In production, this would use actual APIs
            mock_data = await self._generate_mock_government_data(source)
            return mock_data
            
        except Exception as e:
            logger.error("Failed to fetch government data", source_id=source.id, error=str(e))
            return []
    
    async def _generate_mock_government_data(self, source: DataSource) -> List[Dict[str, Any]]:
        """Generate mock data for testing (replace with actual API calls)"""
        import random
        
        commodities = [
            "Wheat", "Rice", "Maize", "Bajra", "Jowar", "Barley",
            "Gram", "Tur", "Moong", "Urad", "Masoor", "Groundnut",
            "Mustard", "Sunflower", "Soybean", "Cotton", "Sugarcane",
            "Onion", "Potato", "Tomato", "Chilli", "Turmeric", "Coriander"
        ]
        
        states = [
            "Andhra Pradesh", "Telangana", "Karnataka", "Tamil Nadu", "Kerala",
            "Maharashtra", "Gujarat", "Rajasthan", "Madhya Pradesh", "Uttar Pradesh",
            "Bihar", "West Bengal", "Odisha", "Jharkhand", "Chhattisgarh",
            "Punjab", "Haryana", "Himachal Pradesh", "Uttarakhand", "Assam"
        ]
        
        mock_data = []
        for _ in range(random.randint(50, 200)):
            commodity = random.choice(commodities)
            state = random.choice(states)
            base_price = random.uniform(1000, 5000)
            
            record = {
                "commodity": commodity,
                "variety": f"{commodity} Grade A",
                "price": round(base_price + random.uniform(-200, 200), 2),
                "unit": "quintal",
                "quantity": random.uniform(10, 1000),
                "quality": random.choice(["premium", "good", "average"]),
                "mandi_name": f"{random.choice(['Central', 'Main', 'New'])} Mandi {state}",
                "district": f"District {random.randint(1, 10)}",
                "state": state,
                "latitude": random.uniform(8.0, 37.0),
                "longitude": random.uniform(68.0, 97.0),
                "timestamp": datetime.utcnow().isoformat(),
                "source": source.id
            }
            mock_data.append(record)
        
        return mock_data
    
    async def _convert_to_price_point(
        self, 
        record: Dict[str, Any], 
        source: DataSource,
        validation_result: ValidationResult
    ) -> PricePoint:
        """Convert raw data to PricePoint model"""
        
        # Create or get mandi info
        mandi_id = f"mandi_{record['state'].lower().replace(' ', '_')}_{hash(record['mandi_name']) % 10000}"
        
        # Use corrected data if available
        data = validation_result.corrected_data or record
        
        price_point = PricePoint(
            commodity=data["commodity"],
            variety=data.get("variety"),
            price=float(data["price"]),
            unit=data.get("unit", "quintal"),
            quantity=float(data["quantity"]) if data.get("quantity") else None,
            quality=QualityGrade(data.get("quality", "average")),
            mandi_id=mandi_id,
            timestamp=datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00')) if isinstance(data["timestamp"], str) else data["timestamp"],
            source_id=source.id,
            confidence=validation_result.confidence_score,
            metadata={
                "district": data.get("district"),
                "state": data.get("state"),
                "mandi_name": data.get("mandi_name"),
                "original_source": source.name
            }
        )
        
        return price_point
    
    async def run_ingestion_cycle(self):
        """Manually run a single ingestion cycle for all sources"""
        tasks = []
        for source in self.data_sources:
            if source.is_active:
                task = asyncio.create_task(self._ingest_from_source(source))
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def get_commodity_prices(
        self, 
        commodity: str, 
        state: Optional[str] = None, 
        limit: int = 100
    ) -> List[Any]:
        """Get commodity prices (delegated to database layer)"""
        from database import get_commodity_prices
        return await get_commodity_prices(commodity, state, limit)
    
    async def get_mandis(self, state: Optional[str] = None) -> List[MandiInfo]:
        """Get mandis (delegated to database layer)"""
        from database import get_mandis
        return await get_mandis(state)
    
    async def get_data_sources(self) -> List[DataSource]:
        """Get configured data sources"""
        return self.data_sources