"""
Historical Analyzer for MANDI EAR™
Analyzes conversation history to create performance benchmarks
"""

import asyncio
import statistics
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import structlog
from models import (
    ConversationRecord, FarmerBenchmark, BenchmarkAnalysis, 
    PriceDataPoint, TrendAnalysis
)

logger = structlog.get_logger()

class HistoricalAnalyzer:
    """
    Analyzes historical conversation data to create benchmarks
    """
    
    def __init__(self):
        """Initialize the historical analyzer"""
        logger.info("HistoricalAnalyzer initialized")
    
    async def create_benchmark_from_conversations(
        self,
        farmer_id: UUID,
        commodity: str,
        analysis_period_days: int = 30,
        location_filter: Optional[str] = None,
        db=None
    ) -> FarmerBenchmark:
        """
        Create historical benchmark from conversation data
        
        Args:
            farmer_id: Farmer's unique identifier
            commodity: Commodity to analyze
            analysis_period_days: Days to analyze
            location_filter: Optional location filter
            db: Database connection
            
        Returns:
            Created FarmerBenchmark
        """
        try:
            logger.info("Creating benchmark from conversations", 
                       farmer_id=str(farmer_id),
                       commodity=commodity,
                       analysis_period=analysis_period_days)
            
            # Fetch conversation records
            start_date = datetime.utcnow() - timedelta(days=analysis_period_days)
            conversations = await self._fetch_conversation_records(
                farmer_id, commodity, start_date, location_filter, db
            )
            
            if not conversations:
                raise ValueError(f"No conversation data found for {commodity} in the specified period")
            
            # Extract price data points
            price_points = self._extract_price_data_points(conversations)
            
            if not price_points:
                raise ValueError(f"No price data found in conversations for {commodity}")
            
            # Analyze price data
            analysis = self._analyze_price_data(price_points, commodity)
            
            # Calculate benchmark price
            benchmark_price = self._calculate_benchmark_price(price_points, analysis)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(price_points, conversations)
            
            # Create benchmark
            benchmark = FarmerBenchmark(
                farmer_id=farmer_id,
                commodity=commodity.lower().strip(),
                benchmark_price=benchmark_price,
                price_range=analysis.price_range,
                confidence_score=confidence_score,
                data_points_count=len(price_points),
                analysis_period=f"{analysis_period_days} days",
                location_context=location_filter or "all_locations",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={
                    "analysis": analysis.dict(),
                    "conversation_count": len(conversations),
                    "price_points_count": len(price_points),
                    "location_breakdown": analysis.location_breakdown,
                    "quality_indicators": analysis.quality_indicators
                }
            )
            
            # Store benchmark
            await self._store_benchmark(benchmark, db)
            
            logger.info("Benchmark created successfully", 
                       benchmark_id=str(benchmark.id),
                       benchmark_price=benchmark_price,
                       confidence=confidence_score)
            
            return benchmark
            
        except Exception as e:
            logger.error("Failed to create benchmark from conversations", error=str(e))
            raise
    
    async def record_conversation(
        self,
        farmer_id: UUID,
        conversation_data: Dict[str, Any],
        db=None
    ) -> ConversationRecord:
        """
        Record conversation data for future benchmark analysis
        
        Args:
            farmer_id: Farmer's unique identifier
            conversation_data: Processed conversation data from ambient AI
            db: Database connection
            
        Returns:
            Created ConversationRecord
        """
        try:
            logger.info("Recording conversation", 
                       farmer_id=str(farmer_id),
                       commodity=conversation_data.get("commodity"))
            
            # Extract relevant data
            conversation_record = ConversationRecord(
                farmer_id=farmer_id,
                commodity=conversation_data.get("commodity", "").lower().strip() or None,
                price_extracted=conversation_data.get("price"),
                quantity_extracted=conversation_data.get("quantity"),
                intent=conversation_data.get("intent"),
                location=conversation_data.get("location"),
                confidence=conversation_data.get("confidence", 0.0),
                conversation_text=conversation_data.get("text"),
                audio_segment_id=conversation_data.get("segment_id"),
                recorded_at=datetime.utcnow(),
                metadata={
                    "processing_time": conversation_data.get("processing_time"),
                    "source": conversation_data.get("source", "ambient_ai"),
                    "entities": conversation_data.get("entities", []),
                    "speaker_id": conversation_data.get("speaker_id")
                }
            )
            
            # Store conversation record
            await self._store_conversation_record(conversation_record, db)
            
            logger.info("Conversation recorded successfully", 
                       record_id=str(conversation_record.id),
                       commodity=conversation_record.commodity)
            
            return conversation_record
            
        except Exception as e:
            logger.error("Failed to record conversation", error=str(e))
            raise
    
    def _extract_price_data_points(self, conversations: List[ConversationRecord]) -> List[PriceDataPoint]:
        """Extract price data points from conversations"""
        price_points = []
        
        for conversation in conversations:
            if conversation.price_extracted and conversation.price_extracted > 0:
                price_point = PriceDataPoint(
                    price=conversation.price_extracted,
                    quantity=conversation.quantity_extracted,
                    date=conversation.recorded_at,
                    location=conversation.location,
                    confidence=conversation.confidence,
                    source="conversation"
                )
                price_points.append(price_point)
        
        logger.debug("Extracted price data points", count=len(price_points))
        return price_points
    
    def _analyze_price_data(self, price_points: List[PriceDataPoint], commodity: str) -> BenchmarkAnalysis:
        """Analyze price data to create comprehensive analysis"""
        prices = [p.price for p in price_points]
        
        # Basic statistics
        average_price = statistics.mean(prices)
        median_price = statistics.median(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        price_range = {
            "min": min_price,
            "max": max_price,
            "avg": average_price,
            "median": median_price,
            "std_dev": statistics.stdev(prices) if len(prices) > 1 else 0.0
        }
        
        # Confidence factors
        confidence_factors = {
            "data_volume": min(1.0, len(price_points) / 20),  # More data = higher confidence
            "price_consistency": 1.0 - (statistics.stdev(prices) / average_price) if average_price > 0 else 0.0,
            "time_distribution": self._calculate_time_distribution_score(price_points),
            "location_diversity": self._calculate_location_diversity_score(price_points)
        }
        
        # Location breakdown
        location_breakdown = self._analyze_location_breakdown(price_points)
        
        # Time trend analysis
        time_trend = self._analyze_time_trends(price_points)
        
        # Quality indicators
        quality_indicators = {
            "high_confidence_points": len([p for p in price_points if p.confidence > 0.8]),
            "recent_data_points": len([p for p in price_points 
                                     if (datetime.utcnow() - p.date).days <= 7]),
            "location_coverage": len(set(p.location for p in price_points if p.location)),
            "price_volatility": "low" if price_range["std_dev"] / average_price < 0.1 else "high"
        }
        
        return BenchmarkAnalysis(
            commodity=commodity,
            total_conversations=len(price_points),  # Simplified
            price_data_points=len(price_points),
            average_price=average_price,
            median_price=median_price,
            price_range=price_range,
            confidence_factors=confidence_factors,
            location_breakdown=location_breakdown,
            time_trend=time_trend,
            quality_indicators=quality_indicators
        )
    
    def _calculate_benchmark_price(
        self, 
        price_points: List[PriceDataPoint], 
        analysis: BenchmarkAnalysis
    ) -> float:
        """Calculate the benchmark price using weighted approach"""
        if not price_points:
            return 0.0
        
        # Weight prices by confidence and recency
        weighted_prices = []
        total_weight = 0.0
        
        now = datetime.utcnow()
        
        for point in price_points:
            # Confidence weight
            confidence_weight = point.confidence
            
            # Recency weight (more recent = higher weight)
            days_old = (now - point.date).days
            recency_weight = max(0.1, 1.0 - (days_old / 30))  # Decay over 30 days
            
            # Quantity weight (if available)
            quantity_weight = 1.0
            if point.quantity and point.quantity > 0:
                # Normalize quantity weight (larger quantities get slightly higher weight)
                quantity_weight = min(2.0, 1.0 + (point.quantity / 100))
            
            # Combined weight
            combined_weight = confidence_weight * recency_weight * quantity_weight
            
            weighted_prices.append(point.price * combined_weight)
            total_weight += combined_weight
        
        if total_weight > 0:
            benchmark_price = sum(weighted_prices) / total_weight
        else:
            benchmark_price = analysis.median_price  # Fallback to median
        
        logger.debug("Calculated benchmark price", 
                    benchmark_price=benchmark_price,
                    total_weight=total_weight)
        
        return benchmark_price
    
    def _calculate_confidence_score(
        self, 
        price_points: List[PriceDataPoint], 
        conversations: List[ConversationRecord]
    ) -> float:
        """Calculate overall confidence score for the benchmark"""
        if not price_points:
            return 0.0
        
        # Data volume factor
        volume_score = min(1.0, len(price_points) / 15)  # Optimal at 15+ points
        
        # Average confidence of individual points
        avg_confidence = statistics.mean([p.confidence for p in price_points])
        
        # Price consistency factor
        prices = [p.price for p in price_points]
        if len(prices) > 1:
            cv = statistics.stdev(prices) / statistics.mean(prices)
            consistency_score = max(0.0, 1.0 - cv)  # Lower CV = higher consistency
        else:
            consistency_score = 0.5
        
        # Recency factor
        now = datetime.utcnow()
        recent_points = len([p for p in price_points if (now - p.date).days <= 7])
        recency_score = min(1.0, recent_points / 5)  # Optimal at 5+ recent points
        
        # Location diversity factor
        unique_locations = len(set(p.location for p in price_points if p.location))
        location_score = min(1.0, unique_locations / 3)  # Optimal at 3+ locations
        
        # Weighted combination
        confidence_score = (
            volume_score * 0.3 +
            avg_confidence * 0.3 +
            consistency_score * 0.2 +
            recency_score * 0.1 +
            location_score * 0.1
        )
        
        return min(1.0, max(0.0, confidence_score))
    
    def _calculate_time_distribution_score(self, price_points: List[PriceDataPoint]) -> float:
        """Calculate how well distributed the data points are over time"""
        if len(price_points) < 2:
            return 0.5
        
        # Calculate time gaps between consecutive points
        sorted_points = sorted(price_points, key=lambda p: p.date)
        gaps = []
        
        for i in range(1, len(sorted_points)):
            gap = (sorted_points[i].date - sorted_points[i-1].date).days
            gaps.append(gap)
        
        # Ideal gap is around 1-3 days
        ideal_gap = 2.0
        gap_scores = [max(0.0, 1.0 - abs(gap - ideal_gap) / 10) for gap in gaps]
        
        return statistics.mean(gap_scores) if gap_scores else 0.5
    
    def _calculate_location_diversity_score(self, price_points: List[PriceDataPoint]) -> float:
        """Calculate location diversity score"""
        locations = [p.location for p in price_points if p.location]
        unique_locations = len(set(locations))
        
        if not locations:
            return 0.0
        
        # Score based on number of unique locations
        return min(1.0, unique_locations / 5)  # Optimal at 5+ locations
    
    def _analyze_location_breakdown(self, price_points: List[PriceDataPoint]) -> Dict[str, Any]:
        """Analyze price breakdown by location"""
        location_data = {}
        
        for point in price_points:
            location = point.location or "unknown"
            if location not in location_data:
                location_data[location] = {
                    "prices": [],
                    "count": 0,
                    "avg_confidence": 0.0
                }
            
            location_data[location]["prices"].append(point.price)
            location_data[location]["count"] += 1
        
        # Calculate statistics for each location
        for location, data in location_data.items():
            prices = data["prices"]
            data["average_price"] = statistics.mean(prices)
            data["min_price"] = min(prices)
            data["max_price"] = max(prices)
            data["price_range"] = max(prices) - min(prices)
            
            # Calculate average confidence for this location
            location_points = [p for p in price_points if (p.location or "unknown") == location]
            data["avg_confidence"] = statistics.mean([p.confidence for p in location_points])
        
        return location_data
    
    def _analyze_time_trends(self, price_points: List[PriceDataPoint]) -> List[Dict[str, Any]]:
        """Analyze price trends over time"""
        if len(price_points) < 3:
            return []
        
        # Sort by date
        sorted_points = sorted(price_points, key=lambda p: p.date)
        
        # Group by week
        weekly_data = {}
        for point in sorted_points:
            # Get week start (Monday)
            week_start = point.date - timedelta(days=point.date.weekday())
            week_key = week_start.strftime("%Y-%W")
            
            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    "prices": [],
                    "week_start": week_start,
                    "count": 0
                }
            
            weekly_data[week_key]["prices"].append(point.price)
            weekly_data[week_key]["count"] += 1
        
        # Calculate weekly averages
        trend_data = []
        for week_key, data in sorted(weekly_data.items()):
            avg_price = statistics.mean(data["prices"])
            trend_data.append({
                "period": week_key,
                "week_start": data["week_start"].isoformat(),
                "average_price": avg_price,
                "data_points": data["count"],
                "price_range": {
                    "min": min(data["prices"]),
                    "max": max(data["prices"])
                }
            })
        
        return trend_data
    
    # Database simulation methods
    async def _fetch_conversation_records(
        self,
        farmer_id: UUID,
        commodity: str,
        start_date: datetime,
        location_filter: Optional[str],
        db
    ) -> List[ConversationRecord]:
        """Fetch conversation records from database"""
        # Simulate database query
        await asyncio.sleep(0.01)
        
        # Return simulated conversation records
        base_date = datetime.utcnow()
        records = []
        
        # Generate sample conversation records
        for i in range(15):  # 15 sample records
            record_date = base_date - timedelta(days=i*2, hours=i*3)
            
            # Vary prices realistically
            base_price = 2100 + (i % 5) * 50 - 100  # Price variation
            price = base_price + (i % 3) * 25  # Additional variation
            
            record = ConversationRecord(
                farmer_id=farmer_id,
                commodity=commodity.lower(),
                price_extracted=price,
                quantity_extracted=10 + (i % 5) * 5,  # 10-30 quantity
                intent="selling" if i % 3 == 0 else "inquiry",
                location=f"mandi_{i % 3 + 1}" if not location_filter else location_filter,
                confidence=0.7 + (i % 4) * 0.075,  # 0.7-0.925 confidence
                conversation_text=f"Sample conversation {i} about {commodity}",
                audio_segment_id=f"segment_{i}",
                recorded_at=record_date,
                metadata={
                    "source": "ambient_ai",
                    "processing_time": 0.5 + (i % 3) * 0.2
                }
            )
            records.append(record)
        
        # Filter by location if specified
        if location_filter:
            records = [r for r in records if r.location == location_filter]
        
        logger.debug("Fetched conversation records", 
                    count=len(records),
                    commodity=commodity,
                    location_filter=location_filter)
        
        return records
    
    async def _store_benchmark(self, benchmark: FarmerBenchmark, db):
        """Store benchmark in database"""
        # Simulate database operation
        await asyncio.sleep(0.01)
        logger.debug("Stored benchmark", benchmark_id=str(benchmark.id))
    
    async def _store_conversation_record(self, record: ConversationRecord, db):
        """Store conversation record in database"""
        # Simulate database operation
        await asyncio.sleep(0.01)
        logger.debug("Stored conversation record", record_id=str(record.id))