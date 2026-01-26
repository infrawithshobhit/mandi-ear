"""
Property-Based Test for Price Aggregation Correctness
Feature: mandi-ear, Property 2: Price Aggregation Correctness

**Validates: Requirements 1.3**

This test validates that for any set of price points for the same commodity,
the weighted average calculation correctly factors quantity and recency 
according to the mathematical formula.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
import math

# Test configuration
MIN_PRICE = 1.0
MAX_PRICE = 10000.0
MIN_QUANTITY = 0.1
MAX_QUANTITY = 1000.0

class PricePoint:
    """Represents a price point with quantity and timestamp"""
    
    def __init__(self, price: float, quantity: float, timestamp: datetime, source_confidence: float = 1.0):
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp
        self.source_confidence = source_confidence
    
    def __repr__(self):
        return f"PricePoint(price={self.price}, quantity={self.quantity}, timestamp={self.timestamp})"

class PriceAggregator:
    """
    Implements weighted average price calculation with quantity and recency factors
    """
    
    def __init__(self, recency_decay_hours: float = 24.0):
        """
        Initialize price aggregator
        
        Args:
            recency_decay_hours: Hours after which price weight decays to ~37% (1/e)
        """
        self.recency_decay_hours = recency_decay_hours
    
    def calculate_weighted_average(self, price_points: List[PricePoint], 
                                 reference_time: datetime = None) -> Tuple[float, float]:
        """
        Calculate weighted average price considering quantity and recency
        
        Args:
            price_points: List of price points to aggregate
            reference_time: Reference time for recency calculation (defaults to latest timestamp)
            
        Returns:
            Tuple of (weighted_average_price, total_confidence)
        """
        if not price_points:
            return 0.0, 0.0
        
        if reference_time is None:
            reference_time = max(point.timestamp for point in price_points)
        
        total_weighted_value = 0.0
        total_weight = 0.0
        
        for point in price_points:
            # Quantity weight (linear)
            quantity_weight = point.quantity
            
            # Recency weight (exponential decay)
            hours_old = (reference_time - point.timestamp).total_seconds() / 3600
            recency_weight = math.exp(-hours_old / self.recency_decay_hours)
            
            # Source confidence weight
            confidence_weight = point.source_confidence
            
            # Combined weight
            combined_weight = quantity_weight * recency_weight * confidence_weight
            
            # Weighted value
            weighted_value = point.price * combined_weight
            
            total_weighted_value += weighted_value
            total_weight += combined_weight
        
        if total_weight == 0:
            return 0.0, 0.0
        
        weighted_average = total_weighted_value / total_weight
        confidence = min(1.0, total_weight / len(price_points))  # Normalize confidence
        
        return weighted_average, confidence
    
    def validate_price_points(self, price_points: List[PricePoint]) -> bool:
        """Validate that price points are reasonable"""
        for point in price_points:
            if point.price <= 0 or point.quantity <= 0:
                return False
            if point.source_confidence < 0 or point.source_confidence > 1:
                return False
        return True

# Hypothesis strategies for generating test data
@st.composite
def price_point_data(draw):
    """Generate a single price point"""
    price = draw(st.floats(min_value=MIN_PRICE, max_value=MAX_PRICE))
    quantity = draw(st.floats(min_value=MIN_QUANTITY, max_value=MAX_QUANTITY))
    
    # Generate timestamp within last 7 days
    base_time = datetime.now()
    hours_ago = draw(st.floats(min_value=0, max_value=168))  # 0-168 hours (7 days)
    timestamp = base_time - timedelta(hours=hours_ago)
    
    confidence = draw(st.floats(min_value=0.1, max_value=1.0))
    
    return {
        "price": price,
        "quantity": quantity,
        "timestamp": timestamp,
        "confidence": confidence
    }

@st.composite
def price_points_list(draw):
    """Generate a list of price points"""
    count = draw(st.integers(min_value=1, max_value=10))
    points_data = draw(st.lists(price_point_data(), min_size=count, max_size=count))
    
    price_points = []
    for data in points_data:
        point = PricePoint(
            price=data["price"],
            quantity=data["quantity"],
            timestamp=data["timestamp"],
            source_confidence=data["confidence"]
        )
        price_points.append(point)
    
    return price_points

@st.composite
def commodity_price_scenario(draw):
    """Generate a realistic commodity price scenario"""
    # Base price for the commodity
    base_price = draw(st.floats(min_value=100, max_value=5000))
    
    # Generate price points with realistic variations
    count = draw(st.integers(min_value=2, max_value=8))
    price_points = []
    
    base_time = datetime.now()
    
    for i in range(count):
        # Price variation (±20% of base price)
        price_variation = draw(st.floats(min_value=-0.2, max_value=0.2))
        price = base_price * (1 + price_variation)
        
        # Quantity (realistic agricultural quantities)
        quantity = draw(st.floats(min_value=10, max_value=500))
        
        # Timestamp (spread over last 48 hours)
        hours_ago = draw(st.floats(min_value=0, max_value=48))
        timestamp = base_time - timedelta(hours=hours_ago)
        
        # Confidence
        confidence = draw(st.floats(min_value=0.6, max_value=1.0))
        
        point = PricePoint(price, quantity, timestamp, confidence)
        price_points.append(point)
    
    return price_points, base_price

class TestPriceAggregation:
    """Test class for price aggregation properties"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.aggregator = PriceAggregator()
    
    @given(price_points=price_points_list())
    @settings(max_examples=50, deadline=15000)
    def test_weighted_average_basic_properties(self, price_points: List[PricePoint]):
        """
        Property 2: Price Aggregation Correctness - Basic Properties
        
        For any set of valid price points, the weighted average should satisfy
        basic mathematical properties and be within reasonable bounds.
        """
        assume(len(price_points) > 0)
        assume(all(p.price > 0 and p.quantity > 0 for p in price_points))
        
        try:
            # Validate input
            assert self.aggregator.validate_price_points(price_points), "Price points should be valid"
            
            # Calculate weighted average
            weighted_avg, confidence = self.aggregator.calculate_weighted_average(price_points)
            
            # Basic properties
            assert weighted_avg >= 0, "Weighted average should be non-negative"
            assert 0 <= confidence <= 1, f"Confidence should be between 0 and 1: {confidence}"
            
            # Weighted average should be within the range of input prices (with small tolerance for floating-point precision)
            min_price = min(p.price for p in price_points)
            max_price = max(p.price for p in price_points)
            tolerance = max(abs(min_price), abs(max_price)) * 1e-10  # Very small tolerance for floating-point precision
            
            assert min_price - tolerance <= weighted_avg <= max_price + tolerance, \
                f"Weighted average {weighted_avg:.10f} should be between min {min_price:.10f} and max {max_price:.10f}"
            
            # For single price point, weighted average should equal the price
            if len(price_points) == 1:
                expected_price = price_points[0].price
                tolerance = abs(expected_price * 0.001)  # 0.1% tolerance
                assert abs(weighted_avg - expected_price) <= tolerance, \
                    f"Single price point: expected {expected_price}, got {weighted_avg}"
            
        except Exception as e:
            pytest.fail(f"Basic properties test failed: {str(e)}")
    
    @given(scenario=commodity_price_scenario())
    @settings(max_examples=30, deadline=12000)
    def test_quantity_weighting_correctness(self, scenario: Tuple[List[PricePoint], float]):
        """
        Property 2: Price Aggregation Correctness - Quantity Weighting
        
        For any set of price points, higher quantity transactions should have
        proportionally more influence on the weighted average.
        """
        price_points, base_price = scenario
        assume(len(price_points) >= 2)
        
        # Skip test if all prices are identical (no meaningful weighting test possible)
        unique_prices = set(p.price for p in price_points)
        assume(len(unique_prices) > 1)
        
        try:
            # Calculate original weighted average
            original_avg, _ = self.aggregator.calculate_weighted_average(price_points)
            
            # Create a modified scenario where we increase the quantity of the highest price point
            modified_points = price_points.copy()
            highest_price_idx = max(range(len(price_points)), key=lambda i: price_points[i].price)
            
            # Double the quantity of the highest price point
            original_quantity = modified_points[highest_price_idx].quantity
            modified_points[highest_price_idx] = PricePoint(
                price=modified_points[highest_price_idx].price,
                quantity=original_quantity * 2,  # Double the quantity
                timestamp=modified_points[highest_price_idx].timestamp,
                source_confidence=modified_points[highest_price_idx].source_confidence
            )
            
            # Calculate new weighted average
            modified_avg, _ = self.aggregator.calculate_weighted_average(modified_points)
            
            # Use tolerance for floating-point comparison
            tolerance = 1e-10
            
            # The weighted average should move toward the higher price
            if price_points[highest_price_idx].price > original_avg + tolerance:
                assert modified_avg >= original_avg - tolerance, \
                    f"Increasing quantity of higher price should increase average: {original_avg:.10f} -> {modified_avg:.10f}"
            elif price_points[highest_price_idx].price < original_avg - tolerance:
                assert modified_avg <= original_avg + tolerance, \
                    f"Increasing quantity of lower price should decrease average: {original_avg:.10f} -> {modified_avg:.10f}"
            # If prices are very close to the average, the change might be minimal due to floating-point precision
            
        except Exception as e:
            pytest.fail(f"Quantity weighting test failed: {str(e)}")
    
    @given(price_points=price_points_list())
    @settings(max_examples=25, deadline=10000)
    def test_recency_weighting_correctness(self, price_points: List[PricePoint]):
        """
        Property 2: Price Aggregation Correctness - Recency Weighting
        
        For any set of price points, more recent prices should have higher
        influence on the weighted average than older prices.
        """
        assume(len(price_points) >= 2)
        assume(all(p.price > 0 and p.quantity > 0 for p in price_points))
        
        try:
            # Sort price points by timestamp
            sorted_points = sorted(price_points, key=lambda p: p.timestamp)
            
            # Ensure we have points with different timestamps
            if sorted_points[0].timestamp == sorted_points[-1].timestamp:
                # Modify timestamps to create time difference
                for i, point in enumerate(sorted_points):
                    point.timestamp = point.timestamp - timedelta(hours=i)
            
            # Calculate weighted average with different reference times
            latest_time = max(p.timestamp for p in price_points)
            
            # Test with current time as reference (all points are "old")
            current_time = datetime.now()
            avg_current, _ = self.aggregator.calculate_weighted_average(price_points, current_time)
            
            # Test with latest price time as reference (latest point has full weight)
            avg_latest, _ = self.aggregator.calculate_weighted_average(price_points, latest_time)
            
            # Both should be valid averages
            assert avg_current > 0, "Average with current time reference should be positive"
            assert avg_latest > 0, "Average with latest time reference should be positive"
            
            # Create scenario with extreme time differences to test recency effect
            base_time = datetime.now()
            test_points = [
                PricePoint(price=100, quantity=10, timestamp=base_time - timedelta(hours=48)),  # Old, low price
                PricePoint(price=200, quantity=10, timestamp=base_time)  # Recent, high price
            ]
            
            avg_with_recency, _ = self.aggregator.calculate_weighted_average(test_points, base_time)
            
            # The average should be closer to the recent price (200) than simple average (150)
            simple_average = (100 + 200) / 2  # 150
            assert avg_with_recency > simple_average, \
                f"Recency weighting should favor recent prices: {avg_with_recency:.2f} should be > {simple_average:.2f}"
            
        except Exception as e:
            pytest.fail(f"Recency weighting test failed: {str(e)}")
    
    @given(price_points=price_points_list())
    @settings(max_examples=20, deadline=8000)
    def test_confidence_weighting_correctness(self, price_points: List[PricePoint]):
        """
        Property 2: Price Aggregation Correctness - Confidence Weighting
        
        For any set of price points, higher confidence sources should have
        more influence on the weighted average.
        """
        assume(len(price_points) >= 2)
        assume(all(p.price > 0 and p.quantity > 0 for p in price_points))
        
        try:
            # Create test scenario with different confidence levels
            base_time = datetime.now()
            test_points = [
                PricePoint(price=100, quantity=10, timestamp=base_time, source_confidence=0.3),  # Low confidence, low price
                PricePoint(price=200, quantity=10, timestamp=base_time, source_confidence=0.9)   # High confidence, high price
            ]
            
            avg_with_confidence, total_confidence = self.aggregator.calculate_weighted_average(test_points)
            
            # The average should be closer to the high-confidence price
            simple_average = (100 + 200) / 2  # 150
            assert avg_with_confidence > simple_average, \
                f"Confidence weighting should favor high-confidence prices: {avg_with_confidence:.2f} should be > {simple_average:.2f}"
            
            # Total confidence should be reasonable
            assert 0 < total_confidence <= 1, f"Total confidence should be between 0 and 1: {total_confidence}"
            
            # Test with original price points
            original_avg, original_confidence = self.aggregator.calculate_weighted_average(price_points)
            
            # Modify one point to have very low confidence
            if len(price_points) > 1:
                modified_points = price_points.copy()
                modified_points[0] = PricePoint(
                    price=modified_points[0].price,
                    quantity=modified_points[0].quantity,
                    timestamp=modified_points[0].timestamp,
                    source_confidence=0.1  # Very low confidence
                )
                
                modified_avg, modified_confidence = self.aggregator.calculate_weighted_average(modified_points)
                
                # The influence of the low-confidence point should be reduced
                assert modified_confidence <= original_confidence or abs(modified_confidence - original_confidence) < 0.1, \
                    "Reducing confidence should not increase overall confidence significantly"
            
        except Exception as e:
            pytest.fail(f"Confidence weighting test failed: {str(e)}")
    
    @given(price_points=price_points_list())
    @settings(max_examples=15, deadline=6000)
    def test_mathematical_consistency(self, price_points: List[PricePoint]):
        """
        Property 2: Price Aggregation Correctness - Mathematical Consistency
        
        For any set of price points, the weighted average calculation should
        be mathematically consistent and reproducible.
        """
        assume(len(price_points) > 0)
        assume(all(p.price > 0 and p.quantity > 0 for p in price_points))
        
        try:
            reference_time = datetime.now()
            
            # Calculate weighted average multiple times - should be identical
            avg1, conf1 = self.aggregator.calculate_weighted_average(price_points, reference_time)
            avg2, conf2 = self.aggregator.calculate_weighted_average(price_points, reference_time)
            
            assert avg1 == avg2, f"Repeated calculations should be identical: {avg1} != {avg2}"
            assert conf1 == conf2, f"Repeated confidence calculations should be identical: {conf1} != {conf2}"
            
            # Order independence - shuffling should not change result
            import random
            shuffled_points = price_points.copy()
            random.shuffle(shuffled_points)
            
            avg_shuffled, conf_shuffled = self.aggregator.calculate_weighted_average(shuffled_points, reference_time)
            
            tolerance = 1e-10  # Very small tolerance for floating point comparison
            assert abs(avg1 - avg_shuffled) <= tolerance, \
                f"Order should not affect result: {avg1} != {avg_shuffled}"
            assert abs(conf1 - conf_shuffled) <= tolerance, \
                f"Order should not affect confidence: {conf1} != {conf_shuffled}"
            
            # Empty list should return zero
            empty_avg, empty_conf = self.aggregator.calculate_weighted_average([])
            assert empty_avg == 0.0, "Empty list should return zero average"
            assert empty_conf == 0.0, "Empty list should return zero confidence"
            
        except Exception as e:
            pytest.fail(f"Mathematical consistency test failed: {str(e)}")

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])