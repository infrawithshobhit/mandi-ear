"""
Unit tests for anomaly detection algorithms
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List
import statistics

from models import (
    AnomalyDetectionConfig, AnomalyType, AnomalySeverity, 
    DetectionMethod, GeoLocation
)
from anomaly_detector import (
    AnomalyDetectionEngine, PriceSpikeDetector, InventoryTracker,
    StockpilingPatternDetector, PriceDataPoint, InventoryDataPoint,
    StatisticalAnalyzer
)

class TestStatisticalAnalyzer:
    """Test statistical analysis functions"""
    
    def test_calculate_statistics(self):
        """Test statistical calculations"""
        values = [10, 20, 30, 40, 50]
        stats = StatisticalAnalyzer.calculate_statistics(values)
        
        assert stats.mean == 30.0
        assert stats.median == 30.0
        assert stats.min_value == 10
        assert stats.max_value == 50
        assert stats.std_dev > 0
    
    def test_calculate_moving_average(self):
        """Test moving average calculation"""
        values = [10, 20, 30, 40, 50]
        window = 3
        
        moving_avg = StatisticalAnalyzer.calculate_moving_average(values, window)
        
        assert len(moving_avg) == 3  # 5 - 3 + 1
        assert moving_avg[0] == 20.0  # (10+20+30)/3
        assert moving_avg[1] == 30.0  # (20+30+40)/3
        assert moving_avg[2] == 40.0  # (30+40+50)/3
    
    def test_calculate_z_score(self):
        """Test z-score calculation"""
        mean = 30.0
        std_dev = 10.0
        value = 50.0
        
        z_score = StatisticalAnalyzer.calculate_z_score(value, mean, std_dev)
        
        assert z_score == 2.0  # (50-30)/10
    
    def test_detect_outliers_z_score(self):
        """Test outlier detection using z-score"""
        values = [10, 12, 11, 13, 12, 50, 11, 10]  # 50 is an outlier
        
        outliers = StatisticalAnalyzer.detect_outliers_z_score(values, threshold=2.0)
        
        assert len(outliers) > 0
        assert 5 in outliers  # Index of value 50

class TestPriceSpikeDetector:
    """Test price spike detection algorithms"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return AnomalyDetectionConfig(
            price_spike_threshold_percentage=25.0,
            moving_average_window_days=7,  # Must be >= 7 per validation
            min_data_points=5,
            z_score_threshold=2.0
        )
    
    @pytest.fixture
    def detector(self, config):
        """Price spike detector instance"""
        return PriceSpikeDetector(config)
    
    @pytest.fixture
    def normal_price_data(self):
        """Normal price data without spikes"""
        base_time = datetime.utcnow()
        location = GeoLocation(latitude=0.0, longitude=0.0, state="Test State")
        
        return [
            PriceDataPoint(
                commodity="wheat",
                variety="HD-2967",
                price=2000.0 + i * 10,  # Gradual increase
                quantity=100.0,
                mandi_id="mandi_1",
                mandi_name="Test Mandi",
                location=location,
                timestamp=base_time - timedelta(days=15-i),
                confidence=0.9
            )
            for i in range(15)  # Increased from 10 to 15
        ]
    
    @pytest.fixture
    def spike_price_data(self):
        """Price data with a spike"""
        base_time = datetime.utcnow()
        location = GeoLocation(latitude=0.0, longitude=0.0, state="Test State")
        
        data = []
        for i in range(15):  # Increased from 10 to 15 for better moving average
            price = 2000.0 + i * 10
            if i == 12:  # Add spike at index 12
                price *= 1.6  # 60% spike (more significant)
            
            data.append(PriceDataPoint(
                commodity="wheat",
                variety="HD-2967",
                price=price,
                quantity=100.0,
                mandi_id="mandi_1",
                mandi_name="Test Mandi",
                location=location,
                timestamp=base_time - timedelta(days=15-i),
                confidence=0.9
            ))
        
        return data
    
    @pytest.mark.asyncio
    async def test_no_spike_detection(self, detector, normal_price_data):
        """Test that normal price data doesn't trigger spike detection"""
        anomalies = await detector.detect_price_spikes(
            normal_price_data, "wheat", "HD-2967"
        )
        
        assert len(anomalies) == 0
    
    @pytest.mark.asyncio
    async def test_spike_detection(self, detector, spike_price_data):
        """Test that price spike is detected"""
        anomalies = await detector.detect_price_spikes(
            spike_price_data, "wheat", "HD-2967"
        )
        
        assert len(anomalies) > 0
        anomaly = anomalies[0]
        assert anomaly.anomaly_type == AnomalyType.PRICE_SPIKE
        assert anomaly.commodity == "wheat"
        assert anomaly.deviation_percentage > 25.0
    
    @pytest.mark.asyncio
    async def test_insufficient_data(self, detector):
        """Test behavior with insufficient data"""
        base_time = datetime.utcnow()
        location = GeoLocation(latitude=0.0, longitude=0.0, state="Test State")
        
        # Only 2 data points (less than min_data_points=5)
        insufficient_data = [
            PriceDataPoint(
                commodity="wheat",
                variety="HD-2967",
                price=2000.0,
                quantity=100.0,
                mandi_id="mandi_1",
                mandi_name="Test Mandi",
                location=location,
                timestamp=base_time - timedelta(days=1),
                confidence=0.9
            ),
            PriceDataPoint(
                commodity="wheat",
                variety="HD-2967",
                price=2100.0,
                quantity=100.0,
                mandi_id="mandi_1",
                mandi_name="Test Mandi",
                location=location,
                timestamp=base_time,
                confidence=0.9
            )
        ]
        
        anomalies = await detector.detect_price_spikes(
            insufficient_data, "wheat", "HD-2967"
        )
        
        assert len(anomalies) == 0

class TestInventoryTracker:
    """Test inventory anomaly detection"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return AnomalyDetectionConfig(
            inventory_deviation_threshold=30.0,
            stockpiling_threshold_days=7
        )
    
    @pytest.fixture
    def tracker(self, config):
        """Inventory tracker instance"""
        return InventoryTracker(config)
    
    @pytest.fixture
    def normal_inventory_data(self):
        """Normal inventory data"""
        base_time = datetime.utcnow()
        location = GeoLocation(latitude=0.0, longitude=0.0, state="Test State")
        
        return [
            InventoryDataPoint(
                commodity="wheat",
                variety="HD-2967",
                inventory_level=1000.0 + i * 50,  # Gradual increase
                mandi_id="mandi_1",
                mandi_name="Test Mandi",
                location=location,
                timestamp=base_time - timedelta(days=10-i),
                storage_capacity=2000.0
            )
            for i in range(10)
        ]
    
    @pytest.fixture
    def hoarding_inventory_data(self):
        """Inventory data with hoarding pattern"""
        base_time = datetime.utcnow()
        location = GeoLocation(latitude=0.0, longitude=0.0, state="Test State")
        
        data = []
        for i in range(10):
            inventory = 1000.0 + i * 50
            if i >= 7:  # Sudden accumulation in last 3 days
                inventory *= 2.0  # Double the inventory
            
            data.append(InventoryDataPoint(
                commodity="wheat",
                variety="HD-2967",
                inventory_level=inventory,
                mandi_id="mandi_1",
                mandi_name="Test Mandi",
                location=location,
                timestamp=base_time - timedelta(days=10-i),
                storage_capacity=3000.0
            ))
        
        return data
    
    @pytest.mark.asyncio
    async def test_no_inventory_anomaly(self, tracker, normal_inventory_data):
        """Test that normal inventory data doesn't trigger anomaly detection"""
        anomalies = await tracker.detect_inventory_anomalies(
            normal_inventory_data, "wheat", "HD-2967"
        )
        
        assert len(anomalies) == 0
    
    @pytest.mark.asyncio
    async def test_hoarding_detection(self, tracker, hoarding_inventory_data):
        """Test that inventory hoarding is detected"""
        anomalies = await tracker.detect_inventory_anomalies(
            hoarding_inventory_data, "wheat", "HD-2967"
        )
        
        assert len(anomalies) > 0
        anomaly = anomalies[0]
        assert anomaly.anomaly_type == AnomalyType.INVENTORY_HOARDING
        assert anomaly.commodity == "wheat"
        assert anomaly.deviation_percentage > 30.0

class TestStockpilingPatternDetector:
    """Test stockpiling pattern detection"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return AnomalyDetectionConfig(
            pattern_confidence_threshold=0.6
        )
    
    @pytest.fixture
    def detector(self, config):
        """Stockpiling pattern detector instance"""
        return StockpilingPatternDetector(config)
    
    @pytest.fixture
    def coordinated_inventory_data(self):
        """Inventory data showing coordinated stockpiling"""
        base_time = datetime.utcnow()
        
        data = []
        # Create data for 3 different locations with similar accumulation patterns
        for location_id in range(3):
            location = GeoLocation(
                latitude=0.0, 
                longitude=0.0, 
                state=f"State_{location_id}",
                district=f"District_{location_id}"
            )
            
            for i in range(10):
                # Similar accumulation rate across locations
                inventory = 1000.0 + i * 100  # Consistent accumulation
                
                data.append(InventoryDataPoint(
                    commodity="wheat",
                    variety="HD-2967",
                    inventory_level=inventory,
                    mandi_id=f"mandi_{location_id}",
                    mandi_name=f"Test Mandi {location_id}",
                    location=location,
                    timestamp=base_time - timedelta(days=10-i),
                    storage_capacity=2000.0
                ))
        
        return data
    
    @pytest.fixture
    def normal_price_data_for_pattern(self):
        """Normal price data for pattern analysis"""
        base_time = datetime.utcnow()
        location = GeoLocation(latitude=0.0, longitude=0.0, state="Test State")
        
        return [
            PriceDataPoint(
                commodity="wheat",
                variety="HD-2967",
                price=2000.0 + i * 10,
                quantity=100.0,
                mandi_id="mandi_1",
                mandi_name="Test Mandi",
                location=location,
                timestamp=base_time - timedelta(days=10-i),
                confidence=0.9
            )
            for i in range(10)
        ]
    
    @pytest.mark.asyncio
    async def test_coordinated_stockpiling_detection(
        self, 
        detector, 
        coordinated_inventory_data, 
        normal_price_data_for_pattern
    ):
        """Test detection of coordinated stockpiling patterns"""
        patterns = await detector.detect_stockpiling_patterns(
            coordinated_inventory_data,
            normal_price_data_for_pattern,
            "wheat",
            "HD-2967"
        )
        
        # Should detect coordinated pattern
        coordinated_patterns = [p for p in patterns if p.pattern_type == "coordinated"]
        assert len(coordinated_patterns) > 0
        
        pattern = coordinated_patterns[0]
        assert pattern.commodity == "wheat"
        assert len(pattern.involved_locations) >= 3
        assert pattern.confidence_score > 0.5

class TestAnomalyDetectionEngine:
    """Test the main anomaly detection engine"""
    
    @pytest.fixture
    def config(self):
        """Test configuration"""
        return AnomalyDetectionConfig()
    
    @pytest.fixture
    def engine(self, config):
        """Anomaly detection engine instance"""
        return AnomalyDetectionEngine(config)
    
    @pytest.fixture
    def mixed_data(self):
        """Mixed price and inventory data for comprehensive testing"""
        base_time = datetime.utcnow()
        location = GeoLocation(latitude=0.0, longitude=0.0, state="Test State")
        
        # Price data with a dramatic spike
        price_data = []
        for i in range(15):
            price = 2000.0  # Constant price
            if i == 12:  # Add dramatic spike
                price = 3200.0  # 60% spike from constant baseline
            
            price_data.append(PriceDataPoint(
                commodity="wheat",
                variety="HD-2967",
                price=price,
                quantity=100.0,
                mandi_id="mandi_1",
                mandi_name="Test Mandi",
                location=location,
                timestamp=base_time - timedelta(days=15-i),
                confidence=0.9
            ))
        
        # Inventory data with hoarding
        inventory_data = []
        for i in range(15):
            inventory = 1000.0 + i * 50
            if i >= 12:  # Sudden accumulation in last 3 days
                inventory *= 1.8
            
            inventory_data.append(InventoryDataPoint(
                commodity="wheat",
                variety="HD-2967",
                inventory_level=inventory,
                mandi_id="mandi_1",
                mandi_name="Test Mandi",
                location=location,
                timestamp=base_time - timedelta(days=15-i),
                storage_capacity=3000.0
            ))
        
        return price_data, inventory_data
    
    @pytest.mark.asyncio
    async def test_comprehensive_analysis(self, mixed_data):
        """Test comprehensive anomaly analysis"""
        # Use custom config for testing
        config = AnomalyDetectionConfig(
            price_spike_threshold_percentage=25.0,
            moving_average_window_days=7,
            min_data_points=5,
            z_score_threshold=2.0
        )
        engine = AnomalyDetectionEngine(config)
        
        price_data, inventory_data = mixed_data
        
        results = await engine.run_comprehensive_analysis(
            price_data=price_data,
            inventory_data=inventory_data,
            commodity="wheat",
            variety="HD-2967"
        )
        
        # Should detect both price and inventory anomalies
        assert "price_anomalies" in results
        assert "inventory_anomalies" in results
        assert "stockpiling_patterns" in results
        
        # Should have detected the price spike
        assert len(results["price_anomalies"]) > 0
        
        # Should have detected the inventory hoarding
        assert len(results["inventory_anomalies"]) > 0
        
        # Verify anomaly details
        price_anomaly = results["price_anomalies"][0]
        assert price_anomaly.commodity == "wheat"
        assert price_anomaly.anomaly_type == AnomalyType.PRICE_SPIKE
        
        inventory_anomaly = results["inventory_anomalies"][0]
        assert inventory_anomaly.commodity == "wheat"
        assert inventory_anomaly.anomaly_type == AnomalyType.INVENTORY_HOARDING

# Integration tests
class TestAnomalyDetectionIntegration:
    """Integration tests for the complete anomaly detection system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_detection_workflow(self):
        """Test complete detection workflow from data input to anomaly output"""
        # Create test configuration
        config = AnomalyDetectionConfig(
            price_spike_threshold_percentage=20.0,  # Lower threshold for testing
            inventory_deviation_threshold=25.0,     # Lower threshold for testing
            min_data_points=5,
            moving_average_window_days=7  # Add this to fix validation
        )
        
        # Create detection engine
        engine = AnomalyDetectionEngine(config)
        
        # Create test data with known anomalies
        base_time = datetime.utcnow()
        location = GeoLocation(latitude=0.0, longitude=0.0, state="Test State")
        
        # Price data with clear spike
        price_data = []
        for i in range(15):
            price = 2000.0
            if i == 12:  # Clear spike at the end
                price = 2600.0  # 30% spike
            
            price_data.append(PriceDataPoint(
                commodity="rice",
                variety="Basmati",
                price=price,
                quantity=100.0,
                mandi_id="mandi_test",
                mandi_name="Integration Test Mandi",
                location=location,
                timestamp=base_time - timedelta(days=15-i),
                confidence=0.95
            ))
        
        # Inventory data with clear hoarding
        inventory_data = []
        for i in range(15):
            inventory = 1000.0
            if i >= 12:  # Sudden accumulation in last 3 days
                inventory = 1600.0  # 60% increase
            
            inventory_data.append(InventoryDataPoint(
                commodity="rice",
                variety="Basmati",
                inventory_level=inventory,
                mandi_id="mandi_test",
                mandi_name="Integration Test Mandi",
                location=location,
                timestamp=base_time - timedelta(days=15-i),
                storage_capacity=2500.0
            ))
        
        # Run comprehensive analysis
        results = await engine.run_comprehensive_analysis(
            price_data=price_data,
            inventory_data=inventory_data,
            commodity="rice",
            variety="Basmati"
        )
        
        # Verify results
        assert len(results["price_anomalies"]) > 0, "Should detect price spike"
        assert len(results["inventory_anomalies"]) > 0, "Should detect inventory hoarding"
        
        # Verify price anomaly details
        price_anomaly = results["price_anomalies"][0]
        assert price_anomaly.commodity == "rice"
        assert price_anomaly.variety == "Basmati"
        assert price_anomaly.current_price == 2600.0
        assert price_anomaly.deviation_percentage > 20.0
        assert price_anomaly.severity in [AnomalySeverity.MEDIUM, AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]
        
        # Verify inventory anomaly details
        inventory_anomaly = results["inventory_anomalies"][0]
        assert inventory_anomaly.commodity == "rice"
        assert inventory_anomaly.variety == "Basmati"
        assert inventory_anomaly.current_inventory_level == 1600.0
        assert inventory_anomaly.deviation_percentage > 25.0
        assert inventory_anomaly.severity in [AnomalySeverity.MEDIUM, AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])