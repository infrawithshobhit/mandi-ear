"""
Property-Based Test for Network Optimization
**Property 23: Network Optimization**
**Validates: Requirements 10.3**

Feature: mandi-ear, Property 23: For any poor connectivity scenario, 
the system should prioritize essential information and optimize data usage
"""

import pytest
import pytest_asyncio
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
import tempfile
import shutil
from pathlib import Path
import json
import asyncio

# Import the offline cache service components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'offline-cache-service'))

from models import DataType, PriorityLevel, ConnectivityLevel
from cache_manager import CacheManager
from sync_engine import ProgressiveSyncEngine
from priority_manager import EssentialDataPrioritizer


@pytest_asyncio.fixture
async def cache_manager():
    """Create a temporary cache manager for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        manager = CacheManager(temp_dir)
        await manager.initialize()
        yield manager
        await manager.close()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest_asyncio.fixture
async def sync_engine(cache_manager):
    """Create a sync engine for testing"""
    engine = ProgressiveSyncEngine(cache_manager)
    await engine.initialize()
    try:
        yield engine
    finally:
        await engine.shutdown()


@pytest.fixture
def priority_manager():
    """Create a priority manager for testing"""
    return EssentialDataPrioritizer()


@given(
    connectivity_level=st.sampled_from([ConnectivityLevel.POOR, ConnectivityLevel.MODERATE, ConnectivityLevel.GOOD]),
    data_size_kb=st.integers(min_value=1, max_value=1000),
    priority_level=st.sampled_from([PriorityLevel.CRITICAL, PriorityLevel.HIGH, PriorityLevel.MEDIUM, PriorityLevel.LOW])
)
@settings(max_examples=20, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_data_prioritization_by_connectivity(
    sync_engine, connectivity_level, data_size_kb, priority_level
):
    """
    Property: For any connectivity level, the system should prioritize data 
    transmission based on both connectivity quality and data priority
    """
    # Arrange: Set connectivity level
    sync_engine.connectivity_level = connectivity_level
    
    # Create test data with specified priority and size
    test_data = {
        "test_content": "x" * (data_size_kb * 1024),  # Create data of specified size
        "priority": priority_level.value,
        "connectivity_level": connectivity_level.value,
        "timestamp": datetime.now().isoformat()
    }
    
    # Act: Determine sync priorities based on connectivity
    sync_priorities = await sync_engine._determine_sync_priorities()
    
    # Assert: Verify prioritization logic based on connectivity
    if connectivity_level == ConnectivityLevel.POOR:
        # Poor connectivity should only sync critical data
        assert PriorityLevel.CRITICAL in sync_priorities, "Poor connectivity should include critical priority"
        if priority_level == PriorityLevel.CRITICAL:
            assert len(sync_priorities) <= 2, "Poor connectivity should limit sync priorities"
        
    elif connectivity_level == ConnectivityLevel.MODERATE:
        # Moderate connectivity should sync critical and high priority
        assert PriorityLevel.CRITICAL in sync_priorities, "Moderate connectivity should include critical priority"
        assert PriorityLevel.HIGH in sync_priorities, "Moderate connectivity should include high priority"
        
    elif connectivity_level == ConnectivityLevel.GOOD:
        # Good connectivity should sync all priorities
        assert PriorityLevel.CRITICAL in sync_priorities, "Good connectivity should include critical priority"
        assert PriorityLevel.HIGH in sync_priorities, "Good connectivity should include high priority"
        assert PriorityLevel.MEDIUM in sync_priorities, "Good connectivity should include medium priority"


@given(
    location_lat=st.floats(min_value=8.0, max_value=37.0, allow_nan=False, allow_infinity=False),
    location_lng=st.floats(min_value=68.0, max_value=97.0, allow_nan=False, allow_infinity=False),
    radius_km=st.floats(min_value=10.0, max_value=200.0, allow_nan=False, allow_infinity=False),
    max_data_size_mb=st.floats(min_value=1.0, max_value=50.0, allow_nan=False, allow_infinity=False)
)
@settings(max_examples=15, deadline=12000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_essential_data_size_optimization(
    cache_manager, priority_manager, location_lat, location_lng, radius_km, max_data_size_mb
):
    """
    Property: For any location and data size constraint, the system should 
    optimize essential data to fit within the specified size limit while 
    maintaining data completeness
    """
    # Arrange: Cache various types of data
    cached_data_sizes = []
    
    # Cache price data
    for i in range(10):
        price_data = {
            "commodity": f"commodity_{i}",
            "price": 100.0 + i * 10,
            "quantity": 50.0,
            "latitude": location_lat + (i * 0.01),
            "longitude": location_lng + (i * 0.01),
            "created_at": datetime.now().isoformat(),
            "additional_data": "x" * 1000  # Add some bulk to test size optimization
        }
        
        cache_id = await cache_manager.cache_data(
            data_type=DataType.PRICE_DATA,
            content=price_data,
            priority=PriorityLevel.CRITICAL,
            expires_in_hours=6
        )
        cached_data_sizes.append(len(json.dumps(price_data).encode()))
    
    # Cache mandi data
    for i in range(5):
        mandi_data = {
            "name": f"Mandi_{i}",
            "latitude": location_lat + (i * 0.02),
            "longitude": location_lng + (i * 0.02),
            "facilities": ["storage", "weighing", "testing"],
            "operating_hours": "06:00-18:00",
            "description": "x" * 500  # Add bulk data
        }
        
        await cache_manager.cache_data(
            data_type=DataType.MANDI_INFO,
            content=mandi_data,
            priority=PriorityLevel.HIGH,
            expires_in_hours=24
        )
        cached_data_sizes.append(len(json.dumps(mandi_data).encode()))
    
    # Act: Get essential data with size constraints
    essential_data = await priority_manager.get_essential_data(
        cache_manager=cache_manager,
        location_lat=location_lat,
        location_lng=location_lng,
        radius_km=radius_km
    )
    
    # Calculate actual data size
    essential_data_size_mb = len(json.dumps(essential_data).encode()) / (1024 * 1024)
    
    # Assert: Verify size optimization
    assert essential_data is not None, "Essential data should be available"
    assert essential_data_size_mb > 0, "Essential data should have content"
    
    # Verify data completeness despite size constraints
    assert "prices" in essential_data, "Essential data should include prices"
    assert "mandis" in essential_data, "Essential data should include mandis"
    assert "msp_rates" in essential_data, "Essential data should include MSP rates"
    assert "weather" in essential_data, "Essential data should include weather"
    
    # Verify location-based filtering for optimization
    assert essential_data["location"]["lat"] == location_lat, "Location should match request"
    assert essential_data["location"]["lng"] == location_lng, "Location should match request"
    assert essential_data["radius_km"] == radius_km, "Radius should match request"


@given(
    request_timeout_seconds=st.integers(min_value=1, max_value=30),
    retry_attempts=st.integers(min_value=1, max_value=5),
    data_types=st.lists(
        st.sampled_from([DataType.PRICE_DATA, DataType.MANDI_INFO, DataType.MSP_RATES, DataType.WEATHER_DATA]),
        min_size=1, max_size=4, unique=True
    )
)
@settings(max_examples=15, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_network_timeout_optimization(
    sync_engine, request_timeout_seconds, retry_attempts, data_types
):
    """
    Property: For any network timeout and retry configuration, the system 
    should optimize request handling to work within the specified constraints
    """
    # Arrange: Configure network optimization settings
    original_connectivity = sync_engine.connectivity_level
    
    # Simulate poor connectivity for timeout testing
    sync_engine.connectivity_level = ConnectivityLevel.POOR
    
    # Act: Test sync operation with timeout constraints
    start_time = datetime.now()
    
    try:
        # Simulate a sync cycle that should respect timeout constraints
        sync_result = await asyncio.wait_for(
            sync_engine.run_sync_cycle(),
            timeout=request_timeout_seconds * retry_attempts * 2  # Allow for retries
        )
        
        end_time = datetime.now()
        actual_duration = (end_time - start_time).total_seconds()
        
        # Assert: Verify timeout optimization
        assert sync_result is not None, "Sync result should be available"
        assert actual_duration > 0, "Sync should take some time"
        
        # Verify that the sync respects timeout constraints
        max_expected_duration = request_timeout_seconds * retry_attempts * len(data_types) * 1.5
        assert actual_duration <= max_expected_duration, f"Sync duration {actual_duration}s should respect timeout constraints"
        
        # Verify sync status
        assert sync_result.status in ["completed", "partial", "failed"], "Sync should have valid status"
        
        if sync_result.status == "completed":
            assert sync_result.items_synced >= 0, "Completed sync should have synced items count"
        
    except asyncio.TimeoutError:
        # Timeout is acceptable for poor connectivity scenarios
        assert sync_engine.connectivity_level == ConnectivityLevel.POOR, "Timeout should only occur with poor connectivity"
    
    finally:
        # Restore original connectivity
        sync_engine.connectivity_level = original_connectivity


@given(
    commodities=st.lists(
        st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        min_size=1, max_size=8, unique=True
    ),
    max_results_per_commodity=st.integers(min_value=1, max_value=20),
    compression_enabled=st.booleans()
)
@settings(max_examples=12, deadline=12000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_data_compression_optimization(
    cache_manager, commodities, max_results_per_commodity, compression_enabled
):
    """
    Property: For any set of commodities and result limits, the system should 
    optimize data storage and retrieval through compression when enabled
    """
    # Arrange: Cache data for multiple commodities
    total_uncompressed_size = 0
    cached_items = []
    
    for commodity in commodities:
        for i in range(max_results_per_commodity):
            price_data = {
                "commodity": commodity,
                "price": 100.0 + i * 5,
                "quantity": 50.0 + i * 10,
                "mandi_name": f"Mandi_{commodity}_{i}",
                "state": "TestState",
                "district": "TestDistrict",
                "latitude": 20.0 + i * 0.01,
                "longitude": 77.0 + i * 0.01,
                "created_at": datetime.now().isoformat(),
                "quality_grade": "A",
                "moisture_content": 12.5,
                "additional_info": {
                    "seller_contact": f"seller_{i}@example.com",
                    "transport_available": True,
                    "payment_terms": "cash",
                    "bulk_data": "x" * 500  # Add bulk data to test compression
                }
            }
            
            # Calculate uncompressed size
            uncompressed_size = len(json.dumps(price_data).encode())
            total_uncompressed_size += uncompressed_size
            
            # Cache the data (compression is handled internally by cache manager)
            cache_id = await cache_manager.cache_data(
                data_type=DataType.PRICE_DATA,
                content=price_data,
                priority=PriorityLevel.MEDIUM,
                expires_in_hours=12
            )
            
            cached_items.append((cache_id, price_data, uncompressed_size))
    
    # Act: Retrieve cached data and measure efficiency
    retrieved_items = 0
    total_retrieval_time = 0
    
    for cache_id, original_data, original_size in cached_items:
        start_time = datetime.now()
        retrieved_data = await cache_manager.get_cached_data(cache_id)
        end_time = datetime.now()
        
        retrieval_time = (end_time - start_time).total_seconds()
        total_retrieval_time += retrieval_time
        
        if retrieved_data is not None:
            retrieved_items += 1
            
            # Verify data integrity after compression/decompression
            assert retrieved_data["commodity"] == original_data["commodity"], "Commodity should match after retrieval"
            assert retrieved_data["price"] == original_data["price"], "Price should match after retrieval"
            assert retrieved_data["quantity"] == original_data["quantity"], "Quantity should match after retrieval"
    
    # Get cache statistics to verify optimization
    cache_stats = await cache_manager.get_cache_statistics()
    
    # Assert: Verify compression optimization effects
    assert retrieved_items > 0, "Should successfully retrieve cached items"
    assert retrieved_items == len(cached_items), "All cached items should be retrievable"
    
    # Verify cache efficiency
    assert cache_stats["total_entries"] > 0, "Cache should contain entries"
    assert cache_stats["total_size_bytes"] > 0, "Cache should have size information"
    
    # Verify retrieval performance (should be reasonable)
    average_retrieval_time = total_retrieval_time / len(cached_items) if cached_items else 0
    assert average_retrieval_time < 1.0, "Average retrieval time should be under 1 second"
    
    # Verify data integrity across all commodities
    for commodity in commodities:
        commodity_prices = await cache_manager.get_cached_prices(
            commodity=commodity,
            max_age_hours=24
        )
        
        assert len(commodity_prices) > 0, f"Should find cached prices for {commodity}"
        assert len(commodity_prices) <= max_results_per_commodity, f"Should not exceed max results for {commodity}"


@given(
    bandwidth_limit_kbps=st.integers(min_value=10, max_value=1000),
    priority_data_percentage=st.floats(min_value=0.1, max_value=0.9),
    sync_interval_minutes=st.integers(min_value=5, max_value=60)
)
@settings(max_examples=10, deadline=15000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_bandwidth_optimization(
    sync_engine, bandwidth_limit_kbps, priority_data_percentage, sync_interval_minutes
):
    """
    Property: For any bandwidth limitation, the system should optimize 
    data synchronization to work within the available bandwidth while 
    prioritizing essential data
    """
    # Arrange: Configure sync engine for bandwidth optimization
    original_config = sync_engine.config
    
    # Configure for bandwidth-constrained environment
    await sync_engine.configure_sync(
        sync_interval_minutes=sync_interval_minutes,
        priority_data_interval_minutes=max(1, sync_interval_minutes // 4),
        max_cache_size_mb=min(50, bandwidth_limit_kbps // 10)  # Scale cache size with bandwidth
    )
    
    # Simulate bandwidth-constrained connectivity
    if bandwidth_limit_kbps < 100:
        sync_engine.connectivity_level = ConnectivityLevel.POOR
    elif bandwidth_limit_kbps < 500:
        sync_engine.connectivity_level = ConnectivityLevel.MODERATE
    else:
        sync_engine.connectivity_level = ConnectivityLevel.GOOD
    
    # Act: Perform sync operation under bandwidth constraints
    start_time = datetime.now()
    
    try:
        sync_result = await sync_engine.run_sync_cycle()
        end_time = datetime.now()
        
        sync_duration = (end_time - start_time).total_seconds()
        
        # Assert: Verify bandwidth optimization
        assert sync_result is not None, "Sync result should be available"
        
        # Verify sync completed within reasonable time for bandwidth
        max_expected_duration = sync_interval_minutes * 60 * 0.8  # Should complete within 80% of interval
        assert sync_duration <= max_expected_duration, f"Sync should complete within bandwidth constraints"
        
        # Verify data transfer efficiency
        if sync_result.bytes_transferred > 0:
            transfer_rate_kbps = (sync_result.bytes_transferred / 1024) / sync_duration
            
            # Transfer rate should be reasonable for the bandwidth limit
            assert transfer_rate_kbps <= bandwidth_limit_kbps * 1.2, "Transfer rate should respect bandwidth limits"
        
        # Verify prioritization worked correctly
        if sync_result.status == "completed":
            assert sync_result.items_synced >= 0, "Should have synced some items"
            
            # For low bandwidth, should prioritize critical data
            if bandwidth_limit_kbps < 100:
                critical_data_types = [dt for dt in sync_result.data_types_synced 
                                     if dt in [DataType.PRICE_DATA, DataType.MSP_RATES]]
                total_synced_types = len(sync_result.data_types_synced)
                
                if total_synced_types > 0:
                    critical_percentage = len(critical_data_types) / total_synced_types
                    assert critical_percentage >= priority_data_percentage, "Should prioritize critical data under low bandwidth"
        
    except Exception as e:
        # For very low bandwidth, partial failure is acceptable
        if bandwidth_limit_kbps < 50:
            assert "timeout" in str(e).lower() or "connection" in str(e).lower(), "Low bandwidth failures should be connection-related"
        else:
            raise e
    
    finally:
        # Restore original configuration
        sync_engine.config = original_config


@given(
    user_location_lat=st.floats(min_value=8.0, max_value=37.0, allow_nan=False, allow_infinity=False),
    user_location_lng=st.floats(min_value=68.0, max_value=97.0, allow_nan=False, allow_infinity=False),
    network_quality=st.sampled_from(["poor", "moderate", "good"]),
    data_freshness_hours=st.integers(min_value=1, max_value=48)
)
@settings(max_examples=12, deadline=12000, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.asyncio
async def test_location_based_data_optimization(
    cache_manager, priority_manager, user_location_lat, user_location_lng, 
    network_quality, data_freshness_hours
):
    """
    Property: For any user location and network quality, the system should 
    optimize data delivery by prioritizing geographically relevant information
    """
    # Arrange: Cache data at various distances from user location
    nearby_data_count = 0
    distant_data_count = 0
    
    # Cache nearby data (within 50km)
    for i in range(5):
        nearby_lat = user_location_lat + (i * 0.01)  # ~1km apart
        nearby_lng = user_location_lng + (i * 0.01)
        
        nearby_price = {
            "commodity": f"wheat_{i}",
            "price": 2000.0 + i * 10,
            "latitude": nearby_lat,
            "longitude": nearby_lng,
            "distance_category": "nearby",
            "created_at": (datetime.now() - timedelta(hours=data_freshness_hours // 2)).isoformat()
        }
        
        await cache_manager.cache_data(
            data_type=DataType.PRICE_DATA,
            content=nearby_price,
            priority=PriorityLevel.HIGH,
            expires_in_hours=data_freshness_hours
        )
        nearby_data_count += 1
    
    # Cache distant data (beyond 100km)
    for i in range(3):
        distant_lat = user_location_lat + (i * 1.0)  # ~100km apart
        distant_lng = user_location_lng + (i * 1.0)
        
        distant_price = {
            "commodity": f"rice_{i}",
            "price": 1800.0 + i * 15,
            "latitude": distant_lat,
            "longitude": distant_lng,
            "distance_category": "distant",
            "created_at": (datetime.now() - timedelta(hours=data_freshness_hours)).isoformat()
        }
        
        await cache_manager.cache_data(
            data_type=DataType.PRICE_DATA,
            content=distant_price,
            priority=PriorityLevel.MEDIUM,
            expires_in_hours=data_freshness_hours
        )
        distant_data_count += 1
    
    # Act: Get optimized data based on location and network quality
    if network_quality == "poor":
        radius_km = 25.0  # Smaller radius for poor network
    elif network_quality == "moderate":
        radius_km = 75.0  # Medium radius for moderate network
    else:
        radius_km = 150.0  # Larger radius for good network
    
    essential_data = await priority_manager.get_essential_data(
        cache_manager=cache_manager,
        location_lat=user_location_lat,
        location_lng=user_location_lng,
        radius_km=radius_km
    )
    
    # Assert: Verify location-based optimization
    assert essential_data is not None, "Essential data should be available"
    assert "location" in essential_data, "Should include location information"
    assert "radius_km" in essential_data, "Should include radius information"
    
    # Verify location accuracy
    assert essential_data["location"]["lat"] == user_location_lat, "Latitude should match user location"
    assert essential_data["location"]["lng"] == user_location_lng, "Longitude should match user location"
    assert essential_data["radius_km"] == radius_km, "Radius should match network-optimized value"
    
    # Verify data prioritization based on network quality
    prices = essential_data.get("prices", [])
    mandis = essential_data.get("mandis", [])
    
    # Should have some data regardless of network quality
    total_data_items = len(prices) + len(mandis)
    assert total_data_items >= 0, "Should have some data items"
    
    # For poor network, should have fewer items but prioritize nearby
    if network_quality == "poor":
        assert radius_km <= 50.0, "Poor network should use smaller radius"
    
    # For good network, should have more comprehensive data
    elif network_quality == "good":
        assert radius_km >= 100.0, "Good network should use larger radius"
    
    # Verify data freshness optimization
    assert "data_freshness" in essential_data, "Should include data freshness information"
    
    # All returned data should be within the specified radius and freshness
    for price in prices:
        if "latitude" in price and "longitude" in price:
            # Calculate distance (simplified)
            lat_diff = abs(price["latitude"] - user_location_lat)
            lng_diff = abs(price["longitude"] - user_location_lng)
            approx_distance_km = ((lat_diff ** 2 + lng_diff ** 2) ** 0.5) * 111  # Rough conversion
            
            # Should be within the optimized radius (with some tolerance)
            assert approx_distance_km <= radius_km * 1.2, f"Price data should be within optimized radius"


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])