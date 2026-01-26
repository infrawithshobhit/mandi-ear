"""
Real-time Data Processing and Metadata Assignment for MANDI EAR™
Handles timestamp and geo-tagging system, weighted average price calculation,
and real-time streaming data pipeline
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
from dataclasses import dataclass, asdict
from enum import Enum
import json
import structlog
import numpy as np
from collections import defaultdict, deque
import uuid

logger = structlog.get_logger()

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class GeoLocation:
    """Represents geographical location"""
    latitude: float
    longitude: float
    accuracy: float  # meters
    source: str  # "gps", "network", "manual"
    timestamp: datetime

@dataclass
class MarketIntelligenceData:
    """Represents processed market intelligence with metadata"""
    id: str
    commodity: Optional[str]
    price: Optional[float]
    quantity: Optional[float]
    intent: str
    confidence: float
    location: Optional[GeoLocation]
    timestamp: datetime
    processing_time: float
    source_segment_id: str
    speaker_id: Optional[str]
    metadata: Dict[str, Any]

@dataclass
class StreamingDataPoint:
    """Represents a data point in the streaming pipeline"""
    id: str
    data: MarketIntelligenceData
    status: ProcessingStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class WeightedPriceCalculator:
    """
    Calculates weighted average prices with quantity and recency factors
    """
    
    def __init__(self, recency_window_hours: float = 24.0):
        """
        Initialize price calculator
        
        Args:
            recency_window_hours: Time window for price relevance
        """
        self.recency_window_hours = recency_window_hours
        self.price_history = defaultdict(deque)  # commodity -> deque of price points
        
    def add_price_point(self, commodity: str, price: float, quantity: float, 
                       timestamp: datetime, confidence: float = 1.0):
        """Add a new price point to the history"""
        price_point = {
            "price": price,
            "quantity": quantity,
            "timestamp": timestamp,
            "confidence": confidence
        }
        
        self.price_history[commodity].append(price_point)
        
        # Clean old data points
        self._cleanup_old_data(commodity)
    
    def _cleanup_old_data(self, commodity: str):
        """Remove price points older than the recency window"""
        cutoff_time = datetime.now(timezone.utc) - \
                     pd.Timedelta(hours=self.recency_window_hours)
        
        history = self.price_history[commodity]
        while history and history[0]["timestamp"] < cutoff_time:
            history.popleft()
    
    def calculate_weighted_average(self, commodity: str, 
                                 reference_time: datetime = None) -> Tuple[float, float, int]:
        """
        Calculate weighted average price for a commodity
        
        Args:
            commodity: Commodity name
            reference_time: Reference time for recency calculation
            
        Returns:
            Tuple of (weighted_price, confidence, data_points_count)
        """
        if commodity not in self.price_history:
            return 0.0, 0.0, 0
        
        history = self.price_history[commodity]
        if not history:
            return 0.0, 0.0, 0
        
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)
        
        total_weighted_value = 0.0
        total_weight = 0.0
        
        for point in history:
            # Quantity weight
            quantity_weight = point["quantity"]
            
            # Recency weight (exponential decay)
            hours_old = (reference_time - point["timestamp"]).total_seconds() / 3600
            recency_weight = np.exp(-hours_old / (self.recency_window_hours / 3))
            
            # Confidence weight
            confidence_weight = point["confidence"]
            
            # Combined weight
            combined_weight = quantity_weight * recency_weight * confidence_weight
            
            total_weighted_value += point["price"] * combined_weight
            total_weight += combined_weight
        
        if total_weight == 0:
            return 0.0, 0.0, len(history)
        
        weighted_price = total_weighted_value / total_weight
        confidence = min(1.0, total_weight / len(history))
        
        return weighted_price, confidence, len(history)

class MetadataAssigner:
    """
    Assigns timestamps and geo-tags to processed data
    """
    
    def __init__(self, default_location: Optional[GeoLocation] = None):
        """
        Initialize metadata assigner
        
        Args:
            default_location: Default location when GPS is unavailable
        """
        self.default_location = default_location
        self.processing_start_time = time.time()
    
    def assign_timestamp(self, data: MarketIntelligenceData) -> MarketIntelligenceData:
        """Assign precise timestamp to data"""
        if not data.timestamp:
            data.timestamp = datetime.now(timezone.utc)
        
        # Ensure timezone awareness
        if data.timestamp.tzinfo is None:
            data.timestamp = data.timestamp.replace(tzinfo=timezone.utc)
        
        return data
    
    def assign_geolocation(self, data: MarketIntelligenceData, 
                          location_hint: Optional[Dict[str, Any]] = None) -> MarketIntelligenceData:
        """
        Assign geo-location to data
        
        Args:
            data: Market intelligence data
            location_hint: Optional location information from client
        """
        if data.location:
            return data  # Already has location
        
        if location_hint:
            # Use provided location hint
            data.location = GeoLocation(
                latitude=location_hint.get("latitude", 0.0),
                longitude=location_hint.get("longitude", 0.0),
                accuracy=location_hint.get("accuracy", 1000.0),
                source=location_hint.get("source", "manual"),
                timestamp=datetime.now(timezone.utc)
            )
        elif self.default_location:
            # Use default location
            data.location = self.default_location
        else:
            # Create placeholder location (would integrate with actual GPS/location services)
            data.location = GeoLocation(
                latitude=28.6139,  # Delhi coordinates as default
                longitude=77.2090,
                accuracy=10000.0,  # 10km accuracy for default
                source="default",
                timestamp=datetime.now(timezone.utc)
            )
        
        return data
    
    def assign_processing_metadata(self, data: MarketIntelligenceData, 
                                 processing_start: float) -> MarketIntelligenceData:
        """Assign processing-related metadata"""
        current_time = time.time()
        data.processing_time = current_time - processing_start
        
        # Add additional metadata
        if not data.metadata:
            data.metadata = {}
        
        data.metadata.update({
            "processing_timestamp": datetime.now(timezone.utc).isoformat(),
            "processing_duration_ms": data.processing_time * 1000,
            "processor_version": "1.0.0",
            "data_quality_score": data.confidence
        })
        
        return data

class RealTimeDataProcessor:
    """
    Main real-time data processing pipeline
    Coordinates audio processing, conversation analysis, and metadata assignment
    """
    
    def __init__(self, max_queue_size: int = 1000, processing_timeout: float = 30.0):
        """
        Initialize real-time processor
        
        Args:
            max_queue_size: Maximum number of items in processing queue
            processing_timeout: Maximum time to process a single item (seconds)
        """
        self.max_queue_size = max_queue_size
        self.processing_timeout = processing_timeout
        
        # Processing components
        self.price_calculator = WeightedPriceCalculator()
        self.metadata_assigner = MetadataAssigner()
        
        # Processing queue and status tracking
        self.processing_queue = asyncio.Queue(maxsize=max_queue_size)
        self.active_streams = {}  # stream_id -> stream_info
        self.processing_stats = {
            "total_processed": 0,
            "total_failed": 0,
            "average_processing_time": 0.0,
            "queue_size": 0
        }
        
        logger.info("RealTimeDataProcessor initialized", 
                   max_queue_size=max_queue_size,
                   processing_timeout=processing_timeout)
    
    async def process_market_intelligence(self, raw_data: Dict[str, Any], 
                                        location_hint: Optional[Dict[str, Any]] = None) -> MarketIntelligenceData:
        """
        Process raw market intelligence data through the complete pipeline
        
        Args:
            raw_data: Raw extracted data from conversation analysis
            location_hint: Optional location information
            
        Returns:
            Processed market intelligence with metadata
        """
        processing_start = time.time()
        
        try:
            # Create market intelligence data object
            intelligence_data = MarketIntelligenceData(
                id=str(uuid.uuid4()),
                commodity=raw_data.get("commodity"),
                price=raw_data.get("price"),
                quantity=raw_data.get("quantity"),
                intent=raw_data.get("intent", "unknown"),
                confidence=raw_data.get("confidence", 0.0),
                location=None,
                timestamp=raw_data.get("timestamp"),
                processing_time=0.0,
                source_segment_id=raw_data.get("segment_id", ""),
                speaker_id=raw_data.get("speaker_id"),
                metadata={}
            )
            
            # Assign metadata
            intelligence_data = self.metadata_assigner.assign_timestamp(intelligence_data)
            intelligence_data = self.metadata_assigner.assign_geolocation(intelligence_data, location_hint)
            intelligence_data = self.metadata_assigner.assign_processing_metadata(intelligence_data, processing_start)
            
            # Update price history if we have price data
            if intelligence_data.commodity and intelligence_data.price and intelligence_data.quantity:
                self.price_calculator.add_price_point(
                    commodity=intelligence_data.commodity,
                    price=intelligence_data.price,
                    quantity=intelligence_data.quantity,
                    timestamp=intelligence_data.timestamp,
                    confidence=intelligence_data.confidence
                )
            
            # Update processing stats
            self._update_processing_stats(processing_start, success=True)
            
            logger.info("Market intelligence processed", 
                       id=intelligence_data.id,
                       commodity=intelligence_data.commodity,
                       processing_time=intelligence_data.processing_time)
            
            return intelligence_data
            
        except Exception as e:
            self._update_processing_stats(processing_start, success=False)
            logger.error("Market intelligence processing failed", error=str(e))
            raise
    
    async def add_to_stream(self, data: MarketIntelligenceData, stream_id: str = "default"):
        """Add processed data to streaming pipeline"""
        try:
            stream_point = StreamingDataPoint(
                id=str(uuid.uuid4()),
                data=data,
                status=ProcessingStatus.PENDING,
                created_at=datetime.now(timezone.utc)
            )
            
            await self.processing_queue.put(stream_point)
            
            # Update stream info
            if stream_id not in self.active_streams:
                self.active_streams[stream_id] = {
                    "created_at": datetime.now(timezone.utc),
                    "total_points": 0,
                    "last_update": datetime.now(timezone.utc)
                }
            
            self.active_streams[stream_id]["total_points"] += 1
            self.active_streams[stream_id]["last_update"] = datetime.now(timezone.utc)
            
            logger.debug("Data added to stream", 
                        stream_id=stream_id,
                        data_id=stream_point.id)
            
        except asyncio.QueueFull:
            logger.error("Processing queue full, dropping data point", 
                        stream_id=stream_id,
                        queue_size=self.processing_queue.qsize())
            raise
    
    async def get_streaming_data(self, stream_id: str = "default") -> AsyncGenerator[Dict[str, Any], None]:
        """
        Get streaming data for a specific stream
        
        Args:
            stream_id: Stream identifier
            
        Yields:
            Processed data points as JSON-serializable dictionaries
        """
        try:
            while True:
                # Get data from queue with timeout
                try:
                    stream_point = await asyncio.wait_for(
                        self.processing_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Update status
                stream_point.status = ProcessingStatus.PROCESSING
                stream_point.processed_at = datetime.now(timezone.utc)
                
                try:
                    # Convert to JSON-serializable format
                    data_dict = {
                        "id": stream_point.id,
                        "data": {
                            "id": stream_point.data.id,
                            "commodity": stream_point.data.commodity,
                            "price": stream_point.data.price,
                            "quantity": stream_point.data.quantity,
                            "intent": stream_point.data.intent,
                            "confidence": stream_point.data.confidence,
                            "location": {
                                "latitude": stream_point.data.location.latitude,
                                "longitude": stream_point.data.location.longitude,
                                "accuracy": stream_point.data.location.accuracy,
                                "source": stream_point.data.location.source,
                                "timestamp": stream_point.data.location.timestamp.isoformat()
                            } if stream_point.data.location else None,
                            "timestamp": stream_point.data.timestamp.isoformat(),
                            "processing_time": stream_point.data.processing_time,
                            "source_segment_id": stream_point.data.source_segment_id,
                            "speaker_id": stream_point.data.speaker_id,
                            "metadata": stream_point.data.metadata
                        },
                        "status": stream_point.status.value,
                        "created_at": stream_point.created_at.isoformat(),
                        "processed_at": stream_point.processed_at.isoformat() if stream_point.processed_at else None
                    }
                    
                    stream_point.status = ProcessingStatus.COMPLETED
                    yield data_dict
                    
                except Exception as e:
                    stream_point.status = ProcessingStatus.FAILED
                    stream_point.error_message = str(e)
                    logger.error("Failed to process streaming data point", 
                               error=str(e),
                               data_id=stream_point.id)
                
        except Exception as e:
            logger.error("Streaming data generator failed", error=str(e))
    
    def get_weighted_price(self, commodity: str) -> Dict[str, Any]:
        """Get current weighted average price for a commodity"""
        price, confidence, count = self.price_calculator.calculate_weighted_average(commodity)
        
        return {
            "commodity": commodity,
            "weighted_price": price,
            "confidence": confidence,
            "data_points": count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        self.processing_stats["queue_size"] = self.processing_queue.qsize()
        return self.processing_stats.copy()
    
    def get_active_streams(self) -> Dict[str, Any]:
        """Get information about active streams"""
        return {
            stream_id: {
                "created_at": info["created_at"].isoformat(),
                "total_points": info["total_points"],
                "last_update": info["last_update"].isoformat()
            }
            for stream_id, info in self.active_streams.items()
        }
    
    def _update_processing_stats(self, processing_start: float, success: bool):
        """Update internal processing statistics"""
        processing_time = time.time() - processing_start
        
        if success:
            self.processing_stats["total_processed"] += 1
        else:
            self.processing_stats["total_failed"] += 1
        
        # Update average processing time
        total_operations = self.processing_stats["total_processed"] + self.processing_stats["total_failed"]
        if total_operations > 0:
            current_avg = self.processing_stats["average_processing_time"]
            self.processing_stats["average_processing_time"] = \
                (current_avg * (total_operations - 1) + processing_time) / total_operations
    
    async def cleanup_old_streams(self, max_age_hours: float = 24.0):
        """Clean up old inactive streams"""
        cutoff_time = datetime.now(timezone.utc) - pd.Timedelta(hours=max_age_hours)
        
        streams_to_remove = []
        for stream_id, info in self.active_streams.items():
            if info["last_update"] < cutoff_time:
                streams_to_remove.append(stream_id)
        
        for stream_id in streams_to_remove:
            del self.active_streams[stream_id]
            logger.info("Cleaned up old stream", stream_id=stream_id)

# Fix the pandas import issue
try:
    import pandas as pd
except ImportError:
    # Create a simple timedelta replacement if pandas is not available
    class TimeDelta:
        def __init__(self, hours=0):
            self.hours = hours
        
        def __rsub__(self, other):
            from datetime import timedelta
            return other - timedelta(hours=self.hours)
    
    class pd:
        @staticmethod
        def Timedelta(hours=0):
            return TimeDelta(hours=hours)