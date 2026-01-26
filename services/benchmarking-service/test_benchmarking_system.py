"""
Unit tests for Benchmarking System
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock

from models import (
    PriceFloor, FarmerBenchmark, PerformanceMetric, ConversationRecord,
    PerformanceCategory, BenchmarkStatus, PriceFloorRequest, BenchmarkRequest,
    PerformanceTrackingRequest
)
from benchmark_engine import BenchmarkEngine
from performance_tracker import PerformanceTracker
from historical_analyzer import HistoricalAnalyzer

class TestBenchmarkEngine:
    """Test cases for BenchmarkEngine"""
    
    @pytest.fixture
    def benchmark_engine(self):
        """Create benchmark engine instance"""
        return BenchmarkEngine()
    
    @pytest.fixture
    def sample_farmer_id(self):
        """Sample farmer ID"""
        return uuid4()
    
    @pytest.mark.asyncio
    async def test_set_price_floor(self, benchmark_engine, sample_farmer_id):
        """Test setting price floor"""
        # Arrange
        commodity = "wheat"
        floor_price = 2000.0
        unit = "per_quintal"
        reasoning = "Based on production costs"
        
        # Act
        price_floor = await benchmark_engine.set_price_floor(
            farmer_id=sample_farmer_id,
            commodity=commodity,
            floor_price=floor_price,
            unit=unit,
            reasoning=reasoning,
            db=None
        )
        
        # Assert
        assert price_floor.farmer_id == sample_farmer_id
        assert price_floor.commodity == commodity.lower()
        assert price_floor.floor_price == floor_price
        assert price_floor.unit == unit
        assert price_floor.reasoning == reasoning
        assert price_floor.is_active is True
        assert isinstance(price_floor.id, UUID)
        assert isinstance(price_floor.created_at, datetime)
    
    @pytest.mark.asyncio
    async def test_get_price_floors(self, benchmark_engine, sample_farmer_id):
        """Test getting price floors"""
        # Act
        price_floors = await benchmark_engine.get_price_floors(sample_farmer_id, db=None)
        
        # Assert
        assert isinstance(price_floors, list)
        assert len(price_floors) >= 0
        
        # Check structure of returned floors
        for floor in price_floors:
            assert isinstance(floor, PriceFloor)
            assert floor.farmer_id == sample_farmer_id
            assert floor.is_active is True
    
    @pytest.mark.asyncio
    async def test_get_farmer_benchmarks(self, benchmark_engine, sample_farmer_id):
        """Test getting farmer benchmarks"""
        # Act
        benchmarks = await benchmark_engine.get_farmer_benchmarks(
            sample_farmer_id, commodity="wheat", db=None
        )
        
        # Assert
        assert isinstance(benchmarks, list)
        
        # Check structure of returned benchmarks
        for benchmark in benchmarks:
            assert isinstance(benchmark, FarmerBenchmark)
            assert benchmark.farmer_id == sample_farmer_id
            assert benchmark.commodity == "wheat"
            assert benchmark.benchmark_price > 0
            assert 0.0 <= benchmark.confidence_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_get_farmer_analytics(self, benchmark_engine, sample_farmer_id):
        """Test getting farmer analytics"""
        # Act
        analytics = await benchmark_engine.get_farmer_analytics(
            sample_farmer_id, period="30d", db=None
        )
        
        # Assert
        assert isinstance(analytics, dict)
        assert "summary" in analytics
        assert "benchmarks" in analytics
        assert "price_floors" in analytics
        assert "performance" in analytics
        assert "trends" in analytics
        assert "recommendations" in analytics
        
        # Check summary structure
        summary = analytics["summary"]
        assert "total_benchmarks" in summary
        assert "active_price_floors" in summary
        assert "analysis_period" in summary

class TestPerformanceTracker:
    """Test cases for PerformanceTracker"""
    
    @pytest.fixture
    def performance_tracker(self):
        """Create performance tracker instance"""
        return PerformanceTracker()
    
    @pytest.fixture
    def sample_farmer_id(self):
        """Sample farmer ID"""
        return uuid4()
    
    @pytest.mark.asyncio
    async def test_track_performance(self, performance_tracker, sample_farmer_id):
        """Test tracking performance"""
        # Arrange
        commodity = "wheat"
        actual_price = 2200.0
        quantity_sold = 10.0
        sale_date = datetime.utcnow()
        location = "local_mandi"
        
        # Act
        performance = await performance_tracker.track_performance(
            farmer_id=sample_farmer_id,
            commodity=commodity,
            actual_price=actual_price,
            quantity_sold=quantity_sold,
            sale_date=sale_date,
            location=location,
            db=None
        )
        
        # Assert
        assert performance.farmer_id == sample_farmer_id
        assert performance.commodity == commodity.lower()
        assert performance.actual_price == actual_price
        assert performance.quantity_sold == quantity_sold
        assert performance.sale_date == sale_date
        assert performance.location == location
        assert 0.0 <= performance.performance_score <= 100.0
        assert isinstance(performance.category, PerformanceCategory)
        assert performance.total_revenue == actual_price * quantity_sold
        assert isinstance(performance.analysis, dict)
    
    @pytest.mark.asyncio
    async def test_get_performance_history(self, performance_tracker, sample_farmer_id):
        """Test getting performance history"""
        # Act
        history = await performance_tracker.get_performance_history(
            farmer_id=sample_farmer_id,
            commodity="wheat",
            days=30,
            db=None
        )
        
        # Assert
        assert isinstance(history, dict)
        assert "summary" in history
        assert "records" in history
        assert "trends" in history
        assert "recommendations" in history
        
        # Check summary structure
        summary = history["summary"]
        assert "total_sales" in summary
        assert "total_revenue" in summary
        assert "average_performance_score" in summary
        assert "benchmark_adherence_rate" in summary
        assert "floor_violation_count" in summary
        
        # Check records structure
        records = history["records"]
        assert isinstance(records, list)
        
        # Check trends structure
        trends = history["trends"]
        assert "trend_direction" in trends
        assert "improvement_rate" in trends
        assert "consistency" in trends
    
    def test_calculate_performance_score(self, performance_tracker):
        """Test performance score calculation"""
        # Create mock benchmark and price floor
        benchmark = FarmerBenchmark(
            farmer_id=uuid4(),
            commodity="wheat",
            benchmark_price=2000.0,
            price_range={"min": 1800.0, "max": 2200.0, "avg": 2000.0, "median": 1950.0},
            confidence_score=0.85,
            data_points_count=20,
            analysis_period="30 days"
        )
        
        price_floor = PriceFloor(
            farmer_id=uuid4(),
            commodity="wheat",
            floor_price=1800.0,
            unit="per_quintal",
            is_active=True
        )
        
        # Test above benchmark and floor
        score = performance_tracker._calculate_performance_score(2100.0, benchmark, price_floor)
        assert score > 70.0  # Should be good score
        
        # Test below benchmark but above floor
        score = performance_tracker._calculate_performance_score(1900.0, benchmark, price_floor)
        assert 60.0 <= score <= 80.0  # Should be moderate score (above floor gives +20)
        
        # Test below floor
        score = performance_tracker._calculate_performance_score(1700.0, benchmark, price_floor)
        assert score < 40.0  # Should be poor score
    
    def test_determine_performance_category(self, performance_tracker):
        """Test performance category determination"""
        # Test excellent performance
        category = performance_tracker._determine_performance_category(95.0)
        assert category == PerformanceCategory.EXCELLENT
        
        # Test good performance
        category = performance_tracker._determine_performance_category(80.0)
        assert category == PerformanceCategory.GOOD
        
        # Test average performance
        category = performance_tracker._determine_performance_category(65.0)
        assert category == PerformanceCategory.AVERAGE
        
        # Test below average performance
        category = performance_tracker._determine_performance_category(50.0)
        assert category == PerformanceCategory.BELOW_AVERAGE
        
        # Test poor performance
        category = performance_tracker._determine_performance_category(30.0)
        assert category == PerformanceCategory.POOR

class TestHistoricalAnalyzer:
    """Test cases for HistoricalAnalyzer"""
    
    @pytest.fixture
    def historical_analyzer(self):
        """Create historical analyzer instance"""
        return HistoricalAnalyzer()
    
    @pytest.fixture
    def sample_farmer_id(self):
        """Sample farmer ID"""
        return uuid4()
    
    @pytest.mark.asyncio
    async def test_create_benchmark_from_conversations(self, historical_analyzer, sample_farmer_id):
        """Test creating benchmark from conversations"""
        # Act
        benchmark = await historical_analyzer.create_benchmark_from_conversations(
            farmer_id=sample_farmer_id,
            commodity="wheat",
            analysis_period_days=30,
            location_filter=None,
            db=None
        )
        
        # Assert
        assert benchmark.farmer_id == sample_farmer_id
        assert benchmark.commodity == "wheat"
        assert benchmark.benchmark_price > 0
        assert 0.0 <= benchmark.confidence_score <= 1.0
        assert benchmark.data_points_count > 0
        assert benchmark.analysis_period == "30 days"
        assert isinstance(benchmark.price_range, dict)
        assert "min" in benchmark.price_range
        assert "max" in benchmark.price_range
        assert "avg" in benchmark.price_range
        assert "median" in benchmark.price_range
        assert isinstance(benchmark.metadata, dict)
    
    @pytest.mark.asyncio
    async def test_record_conversation(self, historical_analyzer, sample_farmer_id):
        """Test recording conversation"""
        # Arrange
        conversation_data = {
            "commodity": "wheat",
            "price": 2100.0,
            "quantity": 15.0,
            "intent": "selling",
            "location": "local_mandi",
            "confidence": 0.85,
            "text": "I want to sell wheat at 2100 per quintal",
            "segment_id": "segment_123",
            "processing_time": 0.5,
            "entities": [{"type": "commodity", "value": "wheat"}],
            "speaker_id": "farmer_1"
        }
        
        # Act
        record = await historical_analyzer.record_conversation(
            farmer_id=sample_farmer_id,
            conversation_data=conversation_data,
            db=None
        )
        
        # Assert
        assert record.farmer_id == sample_farmer_id
        assert record.commodity == "wheat"
        assert record.price_extracted == 2100.0
        assert record.quantity_extracted == 15.0
        assert record.intent == "selling"
        assert record.location == "local_mandi"
        assert record.confidence == 0.85
        assert record.conversation_text == "I want to sell wheat at 2100 per quintal"
        assert record.audio_segment_id == "segment_123"
        assert isinstance(record.metadata, dict)
    
    def test_calculate_confidence_score(self, historical_analyzer):
        """Test confidence score calculation"""
        from models import PriceDataPoint
        
        # Create sample price points
        price_points = [
            PriceDataPoint(
                price=2000.0,
                quantity=10.0,
                date=datetime.utcnow() - timedelta(days=1),
                location="mandi_1",
                confidence=0.9,
                source="conversation"
            ),
            PriceDataPoint(
                price=2050.0,
                quantity=15.0,
                date=datetime.utcnow() - timedelta(days=3),
                location="mandi_2",
                confidence=0.8,
                source="conversation"
            ),
            PriceDataPoint(
                price=1980.0,
                quantity=12.0,
                date=datetime.utcnow() - timedelta(days=5),
                location="mandi_1",
                confidence=0.85,
                source="conversation"
            )
        ]
        
        # Create sample conversations (simplified)
        conversations = []
        
        # Act
        confidence_score = historical_analyzer._calculate_confidence_score(
            price_points, conversations
        )
        
        # Assert
        assert 0.0 <= confidence_score <= 1.0
        assert confidence_score > 0.5  # Should have reasonable confidence with good data

class TestModels:
    """Test cases for data models"""
    
    def test_price_floor_request_validation(self):
        """Test PriceFloorRequest validation"""
        # Valid request
        request = PriceFloorRequest(
            farmer_id=uuid4(),
            commodity="wheat",
            floor_price=2000.0,
            unit="per_quintal",
            reasoning="Based on production costs"
        )
        assert request.commodity == "wheat"
        assert request.floor_price == 2000.0
        
        # Test commodity normalization
        request = PriceFloorRequest(
            farmer_id=uuid4(),
            commodity="  WHEAT  ",
            floor_price=2000.0
        )
        assert request.commodity == "wheat"
        
        # Test invalid price
        with pytest.raises(ValueError):
            PriceFloorRequest(
                farmer_id=uuid4(),
                commodity="wheat",
                floor_price=-100.0  # Negative price should fail
            )
    
    def test_benchmark_request_validation(self):
        """Test BenchmarkRequest validation"""
        # Valid request
        request = BenchmarkRequest(
            farmer_id=uuid4(),
            commodity="rice",
            analysis_period_days=30,
            location_filter="local_mandi"
        )
        assert request.commodity == "rice"
        assert request.analysis_period_days == 30
        
        # Test period bounds
        with pytest.raises(ValueError):
            BenchmarkRequest(
                farmer_id=uuid4(),
                commodity="rice",
                analysis_period_days=5  # Below minimum
            )
        
        with pytest.raises(ValueError):
            BenchmarkRequest(
                farmer_id=uuid4(),
                commodity="rice",
                analysis_period_days=400  # Above maximum
            )
    
    def test_performance_tracking_request_validation(self):
        """Test PerformanceTrackingRequest validation"""
        # Valid request
        request = PerformanceTrackingRequest(
            farmer_id=uuid4(),
            commodity="wheat",
            actual_price=2200.0,
            quantity_sold=10.0,
            sale_date=datetime.utcnow(),
            location="local_mandi"
        )
        assert request.commodity == "wheat"
        assert request.actual_price == 2200.0
        assert request.quantity_sold == 10.0
        
        # Test invalid price
        with pytest.raises(ValueError):
            PerformanceTrackingRequest(
                farmer_id=uuid4(),
                commodity="wheat",
                actual_price=0.0,  # Zero price should fail
                quantity_sold=10.0
            )
        
        # Test invalid quantity
        with pytest.raises(ValueError):
            PerformanceTrackingRequest(
                farmer_id=uuid4(),
                commodity="wheat",
                actual_price=2200.0,
                quantity_sold=-5.0  # Negative quantity should fail
            )

class TestIntegration:
    """Integration tests for benchmarking system"""
    
    @pytest.fixture
    def benchmark_engine(self):
        return BenchmarkEngine()
    
    @pytest.fixture
    def performance_tracker(self):
        return PerformanceTracker()
    
    @pytest.fixture
    def historical_analyzer(self):
        return HistoricalAnalyzer()
    
    @pytest.fixture
    def sample_farmer_id(self):
        return uuid4()
    
    @pytest.mark.asyncio
    async def test_complete_benchmarking_workflow(
        self, 
        benchmark_engine, 
        performance_tracker, 
        historical_analyzer, 
        sample_farmer_id
    ):
        """Test complete benchmarking workflow"""
        commodity = "wheat"
        
        # Step 1: Record conversations
        conversation_data = {
            "commodity": commodity,
            "price": 2100.0,
            "quantity": 15.0,
            "intent": "selling",
            "location": "local_mandi",
            "confidence": 0.85,
            "text": "Selling wheat at 2100 per quintal"
        }
        
        conversation_record = await historical_analyzer.record_conversation(
            farmer_id=sample_farmer_id,
            conversation_data=conversation_data,
            db=None
        )
        assert conversation_record.commodity == commodity
        
        # Step 2: Create benchmark from conversations
        benchmark = await historical_analyzer.create_benchmark_from_conversations(
            farmer_id=sample_farmer_id,
            commodity=commodity,
            analysis_period_days=30,
            db=None
        )
        assert benchmark.commodity == commodity
        assert benchmark.benchmark_price > 0
        
        # Step 3: Set price floor
        price_floor = await benchmark_engine.set_price_floor(
            farmer_id=sample_farmer_id,
            commodity=commodity,
            floor_price=2000.0,
            reasoning="Based on production costs",
            db=None
        )
        assert price_floor.commodity == commodity
        assert price_floor.floor_price == 2000.0
        
        # Step 4: Track performance
        performance = await performance_tracker.track_performance(
            farmer_id=sample_farmer_id,
            commodity=commodity,
            actual_price=2200.0,
            quantity_sold=10.0,
            sale_date=datetime.utcnow(),
            db=None
        )
        assert performance.commodity == commodity
        assert performance.actual_price == 2200.0
        assert performance.performance_score > 0
        
        # Step 5: Get analytics
        analytics = await benchmark_engine.get_farmer_analytics(
            farmer_id=sample_farmer_id,
            period="30d",
            db=None
        )
        assert "summary" in analytics
        assert "benchmarks" in analytics
        assert "performance" in analytics

if __name__ == "__main__":
    pytest.main([__file__, "-v"])