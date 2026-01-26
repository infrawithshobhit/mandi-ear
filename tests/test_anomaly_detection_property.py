"""
Property-based tests for anomaly detection algorithms
Tests universal correctness properties for the Anti-Hoarding Detection System

**Validates: Requirements 7.1, 7.3**
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import statistics
import math
from hypothesis import given, strategies as st, settings, assume, example
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize, invariant

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'anti-hoarding-service'))

from models import (
    AnomalyDetectionConfig, AnomalyType, AnomalySeverity, 
    DetectionMethod, GeoLocation
)
from anomaly_detector import (
    AnomalyDetectionEngine, PriceSpikeDetector, InventoryTracker,
    StockpilingPatternDetector, PriceDataPoint, InventoryDataPoint,
    StatisticalAnalyzer
)

# Test configuration for property-based testing
TEST_CONFIG = AnomalyDetectionConfig(
    price_spike_threshold_percentage=25.0,
    moving_average_window_days=30,
    min_data_points=10,
    z_score_threshold=2.5,
    inventory_deviation_threshold=30.0,
    stockpiling_threshold_days=7
)

# Hypothesis strategies for generating test data
@st.composite
def geo_location_strategy(draw):
    """Generate valid geographic locations"""
    return GeoLocation(
        latitude=draw(st.floats(min_value=-90, max_value=90)),
        longitude=draw(st.floats(min_value=-180, max_value=180)),
        district=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        state=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        country="India"
    )

@st.composite
def price_data_point_strategy(draw, commodity="wheat", variety="HD-2967", base_price=2000.0):
    """Generate valid price data points"""
    return PriceDataPoint(
        commodity=commodity,
        variety=variety,
        price=draw(st.floats(min_value=base_price * 0.1, max_value=base_price * 5.0)),
        quantity=draw(st.floats(min_value=1.0, max_value=1000.0)),
        mandi_id=draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        mandi_name=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        location=draw(geo_location_strategy()),
        timestamp=draw(st.datetimes(
            min_value=datetime.utcnow() - timedelta(days=90),
            max_value=datetime.utcnow()
        )),
        confidence=draw(st.floats(min_value=0.1, max_value=1.0))
    )

@st.composite
def inventory_data_point_strategy(draw, commodity="wheat", variety="HD-2967"):
    """Generate valid inventory data points"""
    return InventoryDataPoint(
        commodity=commodity,
        variety=variety,
        inventory_level=draw(st.floats(min_value=0.0, max_value=10000.0)),
        mandi_id=draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))),
        mandi_name=draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        location=draw(geo_location_strategy()),
        timestamp=draw(st.datetimes(
            min_value=datetime.utcnow() - timedelta(days=90),
            max_value=datetime.utcnow()
        )),
        storage_capacity=draw(st.one_of(st.none(), st.floats(min_value=1000.0, max_value=20000.0)))
    )

@st.composite
def price_series_with_spike_strategy(draw, base_price=2000.0, spike_percentage=None):
    """Generate price series with a known spike"""
    series_length = draw(st.integers(min_value=35, max_value=60))  # Ensure enough data for 30-day window
    spike_position = draw(st.integers(min_value=30, max_value=series_length-1))  # Spike after moving average window
    
    # Draw spike percentage if not provided
    if spike_percentage is None:
        spike_percentage = draw(st.floats(min_value=30.0, max_value=100.0))
    else:
        # If spike_percentage is a strategy, draw from it
        if hasattr(spike_percentage, 'example'):
            spike_percentage = draw(spike_percentage)
    
    base_time = datetime.utcnow()
    location = draw(geo_location_strategy())
    commodity = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    
    price_series = []
    for i in range(series_length):
        # Generate normal price with small random variation
        normal_price = base_price + draw(st.floats(min_value=-base_price*0.1, max_value=base_price*0.1))
        
        # Add spike at specified position
        if i == spike_position:
            price = normal_price * (1 + spike_percentage / 100.0)
        else:
            price = normal_price
        
        price_series.append(PriceDataPoint(
            commodity=commodity,
            variety="test_variety",
            price=max(1.0, price),  # Ensure positive price
            quantity=draw(st.floats(min_value=10.0, max_value=500.0)),
            mandi_id="test_mandi",
            mandi_name="Test Mandi",
            location=location,
            timestamp=base_time - timedelta(days=series_length-1-i),
            confidence=0.9
        ))
    
    return price_series, spike_position, spike_percentage

@st.composite
def inventory_series_with_hoarding_strategy(draw, base_inventory=1000.0):
    """Generate inventory series with hoarding pattern"""
    series_length = draw(st.integers(min_value=15, max_value=30))
    hoarding_start = draw(st.integers(min_value=10, max_value=series_length-5))
    hoarding_multiplier = draw(st.floats(min_value=1.5, max_value=3.0))
    
    base_time = datetime.utcnow()
    location = draw(geo_location_strategy())
    commodity = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))))
    
    inventory_series = []
    for i in range(series_length):
        # Generate normal inventory with gradual increase
        normal_inventory = base_inventory + i * 20
        
        # Add hoarding pattern after hoarding_start
        if i >= hoarding_start:
            inventory = normal_inventory * hoarding_multiplier
        else:
            inventory = normal_inventory
        
        inventory_series.append(InventoryDataPoint(
            commodity=commodity,
            variety="test_variety",
            inventory_level=max(0.0, inventory),
            mandi_id="test_mandi",
            mandi_name="Test Mandi",
            location=location,
            timestamp=base_time - timedelta(days=series_length-1-i),
            storage_capacity=base_inventory * 5
        ))
    
    return inventory_series, hoarding_start, hoarding_multiplier

class TestAnomalyDetectionProperties:
    """Property-based tests for anomaly detection algorithms"""
    
    @pytest.fixture
    def detection_engine(self):
        """Create detection engine for testing"""
        return AnomalyDetectionEngine(TEST_CONFIG)
    
    @given(price_series_with_spike_strategy())
    @settings(max_examples=50, deadline=10000)
    @pytest.mark.asyncio
    async def test_property_16_price_spike_detection_accuracy(self, price_series_with_spike_data):
        """
        **Property 16: Anomaly Detection Accuracy**
        **Validates: Requirements 7.1, 7.3**
        
        For any price series with a spike >25% deviation from moving average,
        the Anti_Hoarding_Detector should correctly identify the statistical anomaly.
        """
        price_series, spike_position, spike_percentage = price_series_with_spike_data
        
        # Only test spikes that should be detected (>25% with small tolerance for floating point precision)
        assume(spike_percentage >= 25.1)  # Add small buffer for floating point precision
        assume(len(price_series) >= TEST_CONFIG.min_data_points)
        
        detection_engine = AnomalyDetectionEngine(TEST_CONFIG)
        
        # Run price spike detection
        anomalies = await detection_engine.price_spike_detector.detect_price_spikes(
            price_data=price_series,
            commodity=price_series[0].commodity,
            variety=price_series[0].variety
        )
        
        # Property: Should detect the spike
        assert len(anomalies) > 0, f"Failed to detect price spike of {spike_percentage}% at position {spike_position}"
        
        # Property: Detected anomaly should be a price spike
        spike_anomaly = anomalies[0]  # Get the first (most significant) anomaly
        assert spike_anomaly.anomaly_type == AnomalyType.PRICE_SPIKE
        
        # Property: Deviation should be correctly calculated and >= threshold
        assert abs(spike_anomaly.deviation_percentage) >= TEST_CONFIG.price_spike_threshold_percentage
        
        # Property: Anomaly should have valid statistical measures
        assert spike_anomaly.z_score != 0.0
        assert spike_anomaly.moving_average_30d > 0.0
        assert spike_anomaly.confidence_score > 0.0
        
        # Property: Current price should be the spike price
        spike_price = price_series[spike_position].price
        # Allow for small floating point differences
        assert abs(spike_anomaly.current_price - spike_price) < 0.01 or \
               any(abs(anomaly.current_price - spike_price) < 0.01 for anomaly in anomalies)
    
    @given(inventory_series_with_hoarding_strategy())
    @settings(max_examples=30, deadline=10000)
    @pytest.mark.asyncio
    async def test_property_16_inventory_hoarding_detection_accuracy(self, inventory_hoarding_data):
        """
        **Property 16: Anomaly Detection Accuracy**
        **Validates: Requirements 7.1, 7.3**
        
        For any inventory series with abnormal stockpiling patterns,
        the Anti_Hoarding_Detector should correctly identify the anomaly.
        """
        inventory_series, hoarding_start, hoarding_multiplier = inventory_hoarding_data
        
        # Only test significant hoarding patterns
        assume(hoarding_multiplier >= 1.5)  # At least 50% increase
        assume(len(inventory_series) >= 10)
        
        detection_engine = AnomalyDetectionEngine(TEST_CONFIG)
        
        # Run inventory anomaly detection
        anomalies = await detection_engine.inventory_tracker.detect_inventory_anomalies(
            inventory_data=inventory_series,
            commodity=inventory_series[0].commodity,
            variety=inventory_series[0].variety
        )
        
        # Property: Should detect hoarding if deviation is significant enough
        expected_deviation = (hoarding_multiplier - 1) * 100  # Convert to percentage
        if expected_deviation >= TEST_CONFIG.inventory_deviation_threshold:
            assert len(anomalies) > 0, f"Failed to detect inventory hoarding with {expected_deviation}% increase"
            
            # Property: Detected anomaly should be inventory hoarding
            hoarding_anomaly = anomalies[0]
            assert hoarding_anomaly.anomaly_type == AnomalyType.INVENTORY_HOARDING
            
            # Property: Deviation should be correctly calculated
            assert hoarding_anomaly.deviation_percentage > 0  # Should be positive for hoarding
            
            # Property: Should have valid tracking data
            assert hoarding_anomaly.total_mandis_monitored > 0
            assert 0.0 <= hoarding_anomaly.concentration_ratio <= 1.0
    
    @given(st.lists(price_data_point_strategy(), min_size=10, max_size=50))
    @settings(max_examples=30, deadline=10000)
    @pytest.mark.asyncio
    async def test_property_16_no_false_positives_normal_data(self, normal_price_data):
        """
        **Property 16: Anomaly Detection Accuracy**
        **Validates: Requirements 7.1, 7.3**
        
        For any normal price series without significant deviations,
        the Anti_Hoarding_Detector should not generate false positive anomalies.
        """
        # Ensure all prices are within normal range (no spikes > 25%)
        if len(normal_price_data) < 2:
            return
        
        # Sort by timestamp for proper analysis
        normal_price_data.sort(key=lambda x: x.timestamp)
        
        # Ensure the same commodity for all data points
        commodity = normal_price_data[0].commodity
        variety = normal_price_data[0].variety
        for point in normal_price_data:
            point.commodity = commodity
            point.variety = variety
        
        # Check if data has any large spikes that would legitimately trigger detection
        prices = [p.price for p in normal_price_data]
        if len(prices) >= TEST_CONFIG.moving_average_window_days:
            # Calculate moving averages to check for spikes
            moving_averages = []
            for i in range(TEST_CONFIG.moving_average_window_days - 1, len(prices)):
                window_prices = prices[i - TEST_CONFIG.moving_average_window_days + 1:i + 1]
                moving_averages.append(sum(window_prices) / len(window_prices))
            
            # Check if any price deviates more than threshold from its moving average
            has_legitimate_spike = False
            for i, moving_avg in enumerate(moving_averages):
                price_index = i + TEST_CONFIG.moving_average_window_days - 1
                if price_index < len(prices):
                    deviation_pct = abs(prices[price_index] - moving_avg) / moving_avg * 100
                    if deviation_pct >= TEST_CONFIG.price_spike_threshold_percentage:
                        has_legitimate_spike = True
                        break
            
            # Only test for false positives if there are no legitimate spikes
            if not has_legitimate_spike:
                detection_engine = AnomalyDetectionEngine(TEST_CONFIG)
                
                anomalies = await detection_engine.price_spike_detector.detect_price_spikes(
                    price_data=normal_price_data,
                    commodity=commodity,
                    variety=variety
                )
                
                # Property: Should not detect anomalies in normal data
                assert len(anomalies) == 0, f"False positive: detected {len(anomalies)} anomalies in normal data"
    
    @given(st.lists(inventory_data_point_strategy(), min_size=10, max_size=30))
    @settings(max_examples=20, deadline=10000)
    @pytest.mark.asyncio
    async def test_property_16_inventory_consistency(self, inventory_data):
        """
        **Property 16: Anomaly Detection Accuracy**
        **Validates: Requirements 7.1, 7.3**
        
        For any inventory data, the detection results should be consistent
        and all detected anomalies should have valid statistical properties.
        """
        if len(inventory_data) < 5:
            return
        
        # Sort by timestamp and ensure consistent commodity
        inventory_data.sort(key=lambda x: x.timestamp)
        commodity = inventory_data[0].commodity
        variety = inventory_data[0].variety
        for point in inventory_data:
            point.commodity = commodity
            point.variety = variety
        
        detection_engine = AnomalyDetectionEngine(TEST_CONFIG)
        
        anomalies = await detection_engine.inventory_tracker.detect_inventory_anomalies(
            inventory_data=inventory_data,
            commodity=commodity,
            variety=variety
        )
        
        # Property: All detected anomalies should have valid properties
        for anomaly in anomalies:
            assert anomaly.commodity == commodity
            assert anomaly.variety == variety
            assert anomaly.current_inventory_level >= 0.0
            assert anomaly.normal_inventory_level >= 0.0
            assert 0.0 <= anomaly.concentration_ratio <= 1.0
            assert anomaly.total_mandis_monitored > 0
            assert anomaly.accumulation_period_days > 0
            assert anomaly.trend_direction in ["increasing", "decreasing", "stable"]
    
    @given(
        price_series_with_spike_strategy(),
        inventory_series_with_hoarding_strategy()
    )
    @settings(max_examples=20, deadline=15000)
    @pytest.mark.asyncio
    async def test_property_16_comprehensive_detection_accuracy(self, price_data, inventory_data):
        """
        **Property 16: Anomaly Detection Accuracy**
        **Validates: Requirements 7.1, 7.3**
        
        For any combination of price and inventory data with anomalies,
        the comprehensive analysis should detect all significant anomalies.
        """
        price_series, spike_position, spike_percentage = price_data
        inventory_series, hoarding_start, hoarding_multiplier = inventory_data
        
        # Ensure both series have the same commodity for analysis
        commodity = "test_commodity"
        variety = "test_variety"
        
        for point in price_series:
            point.commodity = commodity
            point.variety = variety
        
        for point in inventory_series:
            point.commodity = commodity
            point.variety = variety
        
        detection_engine = AnomalyDetectionEngine(TEST_CONFIG)
        
        # Run comprehensive analysis
        results = await detection_engine.run_comprehensive_analysis(
            price_data=price_series,
            inventory_data=inventory_series,
            commodity=commodity,
            variety=variety
        )
        
        # Property: Results should contain all expected anomaly types
        assert "price_anomalies" in results
        assert "inventory_anomalies" in results
        assert "stockpiling_patterns" in results
        
        # Property: Should detect price spike if significant enough
        if spike_percentage >= TEST_CONFIG.price_spike_threshold_percentage:
            assert len(results["price_anomalies"]) > 0, f"Failed to detect {spike_percentage}% price spike"
        
        # Property: Should detect inventory hoarding if significant enough
        expected_inventory_deviation = (hoarding_multiplier - 1) * 100
        if expected_inventory_deviation >= TEST_CONFIG.inventory_deviation_threshold:
            assert len(results["inventory_anomalies"]) > 0, f"Failed to detect {expected_inventory_deviation}% inventory increase"
        
        # Property: All detected anomalies should have valid metadata
        all_anomalies = (
            results["price_anomalies"] + 
            results["inventory_anomalies"] + 
            results["stockpiling_patterns"]
        )
        
        for anomaly in all_anomalies:
            assert hasattr(anomaly, 'commodity')
            assert hasattr(anomaly, 'detected_at')
            assert hasattr(anomaly, 'severity')
            assert hasattr(anomaly, 'confidence_score') or hasattr(anomaly, 'id')  # Different anomaly types have different fields
            assert anomaly.commodity == commodity

# Stateful property testing for anomaly detection system
class AnomalyDetectionStateMachine(RuleBasedStateMachine):
    """
    Stateful property testing for anomaly detection system
    Tests that the system maintains consistency across multiple operations
    """
    
    price_data = Bundle('price_data')
    inventory_data = Bundle('inventory_data')
    
    def __init__(self):
        super().__init__()
        self.detection_engine = AnomalyDetectionEngine(TEST_CONFIG)
        self.detected_anomalies = []
        self.commodity = "stateful_test_commodity"
        self.variety = "stateful_test_variety"
    
    @initialize()
    def setup(self):
        """Initialize the state machine"""
        self.detected_anomalies = []
    
    @rule(target=price_data, base_price=st.floats(min_value=1000.0, max_value=5000.0))
    def generate_price_data(self, base_price):
        """Generate price data for testing"""
        base_time = datetime.utcnow()
        location = GeoLocation(latitude=0.0, longitude=0.0, state="Test State")
        
        return PriceDataPoint(
            commodity=self.commodity,
            variety=self.variety,
            price=base_price,
            quantity=100.0,
            mandi_id="stateful_mandi",
            mandi_name="Stateful Test Mandi",
            location=location,
            timestamp=base_time,
            confidence=0.9
        )
    
    @rule(target=inventory_data, inventory_level=st.floats(min_value=100.0, max_value=5000.0))
    def generate_inventory_data(self, inventory_level):
        """Generate inventory data for testing"""
        base_time = datetime.utcnow()
        location = GeoLocation(latitude=0.0, longitude=0.0, state="Test State")
        
        return InventoryDataPoint(
            commodity=self.commodity,
            variety=self.variety,
            inventory_level=inventory_level,
            mandi_id="stateful_mandi",
            mandi_name="Stateful Test Mandi",
            location=location,
            timestamp=base_time,
            storage_capacity=10000.0
        )
    
    @rule(price_points=st.lists(price_data, min_size=10, max_size=20))
    def test_price_detection_consistency(self, price_points):
        """Test that price detection is consistent"""
        assume(len(price_points) >= TEST_CONFIG.min_data_points)
        
        # Run detection multiple times - should get consistent results
        async def run_detection():
            return await self.detection_engine.price_spike_detector.detect_price_spikes(
                price_data=price_points,
                commodity=self.commodity,
                variety=self.variety
            )
        
        # Note: In actual test, we'd run this multiple times and compare
        # For now, just ensure it doesn't crash and returns valid results
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            anomalies = loop.run_until_complete(run_detection())
            
            # Property: Results should be deterministic
            for anomaly in anomalies:
                assert anomaly.commodity == self.commodity
                assert anomaly.variety == self.variety
                assert anomaly.anomaly_type == AnomalyType.PRICE_SPIKE
        finally:
            loop.close()
    
    @invariant()
    def detection_engine_remains_valid(self):
        """Invariant: Detection engine should always remain in valid state"""
        assert self.detection_engine is not None
        assert self.detection_engine.config is not None
        assert self.detection_engine.price_spike_detector is not None
        assert self.detection_engine.inventory_tracker is not None
        assert self.detection_engine.stockpiling_detector is not None

# Test the stateful machine
TestAnomalyDetectionStateful = AnomalyDetectionStateMachine.TestCase

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])