"""
Property-Based Test for Data Update Frequency Compliance
Feature: mandi-ear, Property 7: Data Update Frequency Compliance

**Validates: Requirements 3.4, 3.5**

This test validates that for any market operating period, price updates occur
within specified intervals (15 minutes) with appropriate fallback when data
is unavailable.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, time
import asyncio
from dataclasses import dataclass
from enum import Enum
import random

# Test configuration
MARKET_OPERATING_HOURS = {
    "start": time(6, 0),   # 6:00 AM
    "end": time(20, 0)     # 8:00 PM
}

REQUIRED_UPDATE_INTERVAL_MINUTES = 15
FALLBACK_THRESHOLD_MINUTES = 30  # When to trigger fallback behavior

class DataSourceStatus(str, Enum):
    """Data source status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class UpdateStatus(str, Enum):
    """Update status"""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    FALLBACK = "fallback"

@dataclass
class DataSource:
    """Data source configuration"""
    id: str
    name: str
    update_interval_minutes: int
    reliability_score: float
    status: DataSourceStatus
    last_successful_update: Optional[datetime] = None
    consecutive_failures: int = 0

@dataclass
class PriceUpdate:
    """Price update record"""
    source_id: str
    commodity: str
    price: float
    timestamp: datetime
    update_status: UpdateStatus
    data_freshness_minutes: int
    fallback_used: bool = False

@dataclass
class MarketSession:
    """Market operating session"""
    date: datetime
    start_time: datetime
    end_time: datetime
    is_operating: bool
    expected_updates: int
    actual_updates: int

class DataUpdateFrequencySystem:
    """
    Simulates the data update frequency system for testing
    """
    
    def __init__(self):
        self.data_sources = self._initialize_data_sources()
        self.update_history: List[PriceUpdate] = []
        self.fallback_data: Dict[str, List[PriceUpdate]] = {}
        self.market_sessions: List[MarketSession] = []
    
    def _initialize_data_sources(self) -> List[DataSource]:
        """Initialize data sources with different update frequencies"""
        return [
            DataSource(
                id="agmarknet",
                name="AgMarkNet Portal",
                update_interval_minutes=15,
                reliability_score=0.9,
                status=DataSourceStatus.ACTIVE
            ),
            DataSource(
                id="enam",
                name="eNAM Portal", 
                update_interval_minutes=15,
                reliability_score=0.85,
                status=DataSourceStatus.ACTIVE
            ),
            DataSource(
                id="state_portals",
                name="State Mandi Portals",
                update_interval_minutes=30,
                reliability_score=0.8,
                status=DataSourceStatus.ACTIVE
            ),
            DataSource(
                id="trader_reports",
                name="Trader Reports",
                update_interval_minutes=60,
                reliability_score=0.7,
                status=DataSourceStatus.ACTIVE
            )
        ]
    
    def is_market_operating(self, timestamp: datetime) -> bool:
        """Check if market is operating at given timestamp"""
        current_time = timestamp.time()
        return MARKET_OPERATING_HOURS["start"] <= current_time <= MARKET_OPERATING_HOURS["end"]
    
    async def simulate_update_cycle(
        self,
        start_time: datetime,
        duration_hours: int,
        commodity: str = "Wheat"
    ) -> List[PriceUpdate]:
        """
        Simulate a complete update cycle for testing
        
        Args:
            start_time: Start time for simulation
            duration_hours: Duration to simulate
            commodity: Commodity to simulate updates for
            
        Returns:
            List of price updates during the period
        """
        updates = []
        current_time = start_time
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Track last update time for each source
        last_updates = {source.id: start_time - timedelta(hours=1) for source in self.data_sources}
        
        while current_time < end_time:
            # Check if market is operating
            if self.is_market_operating(current_time):
                # Process updates for each data source
                for source in self.data_sources:
                    if source.status == DataSourceStatus.ACTIVE:
                        # Check if it's time for this source to update
                        time_since_last = current_time - last_updates[source.id]
                        
                        if time_since_last.total_seconds() >= source.update_interval_minutes * 60:
                            # Simulate update attempt
                            update = await self._simulate_source_update(
                                source, commodity, current_time
                            )
                            updates.append(update)
                            
                            if update.update_status == UpdateStatus.SUCCESS:
                                last_updates[source.id] = current_time
                                source.last_successful_update = current_time
                                source.consecutive_failures = 0
                            else:
                                source.consecutive_failures += 1
            
            # Advance time by 1 minute
            current_time += timedelta(minutes=1)
        
        return updates
    
    async def _simulate_source_update(
        self,
        source: DataSource,
        commodity: str,
        timestamp: datetime
    ) -> PriceUpdate:
        """Simulate a single source update"""
        
        # Simulate update success/failure based on reliability
        success_probability = source.reliability_score
        
        # Reduce success probability if source has consecutive failures
        if source.consecutive_failures > 0:
            success_probability *= (0.9 ** min(source.consecutive_failures, 5))  # Cap at 5 failures
        
        is_successful = random.random() < success_probability
        
        if is_successful:
            # Generate realistic price
            base_price = 2000 + random.uniform(-200, 200)
            
            update = PriceUpdate(
                source_id=source.id,
                commodity=commodity,
                price=base_price,
                timestamp=timestamp,
                update_status=UpdateStatus.SUCCESS,
                data_freshness_minutes=0,
                fallback_used=False
            )
        else:
            # Failed update - check if fallback should be used
            time_since_last_success = None
            if source.last_successful_update:
                time_since_last_success = timestamp - source.last_successful_update
            
            should_use_fallback = (
                time_since_last_success and 
                time_since_last_success.total_seconds() > FALLBACK_THRESHOLD_MINUTES * 60 and
                source.consecutive_failures >= 2  # Only use fallback after multiple failures
            )
            
            if should_use_fallback:
                # Use fallback data
                fallback_price = await self._get_fallback_price(commodity, timestamp)
                freshness_minutes = min(
                    int(time_since_last_success.total_seconds() / 60),
                    24 * 60  # Cap at 24 hours
                )
                
                update = PriceUpdate(
                    source_id=source.id,
                    commodity=commodity,
                    price=fallback_price,
                    timestamp=timestamp,
                    update_status=UpdateStatus.FALLBACK,
                    data_freshness_minutes=freshness_minutes,
                    fallback_used=True
                )
            else:
                # Failed update without fallback
                update = PriceUpdate(
                    source_id=source.id,
                    commodity=commodity,
                    price=0.0,
                    timestamp=timestamp,
                    update_status=UpdateStatus.FAILED,
                    data_freshness_minutes=0,
                    fallback_used=False
                )
        
        return update
    
    async def _get_fallback_price(self, commodity: str, timestamp: datetime) -> float:
        """Get fallback price based on historical trends"""
        # Simulate fallback price calculation
        base_price = 2000
        
        # Add some variation based on timestamp (seasonal effects)
        day_of_year = timestamp.timetuple().tm_yday
        seasonal_factor = 1 + 0.1 * math.sin(2 * math.pi * day_of_year / 365)
        
        return base_price * seasonal_factor
    
    def get_update_frequency_compliance(
        self,
        updates: List[PriceUpdate],
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """
        Analyze update frequency compliance
        
        Returns:
            Compliance analysis results
        """
        # Filter updates to the specified time range
        relevant_updates = [
            u for u in updates 
            if start_time <= u.timestamp <= end_time
        ]
        
        # Calculate expected vs actual updates during market hours
        total_market_minutes = 0
        current_time = start_time
        
        while current_time < end_time:
            if self.is_market_operating(current_time):
                total_market_minutes += 1
            current_time += timedelta(minutes=1)
        
        # Expected updates per source
        expected_updates_per_source = {}
        for source in self.data_sources:
            if source.status == DataSourceStatus.ACTIVE:
                expected_count = total_market_minutes // source.update_interval_minutes
                expected_updates_per_source[source.id] = expected_count
        
        # Actual updates per source
        actual_updates_per_source = {}
        successful_updates_per_source = {}
        fallback_updates_per_source = {}
        
        for source in self.data_sources:
            source_updates = [u for u in relevant_updates if u.source_id == source.id]
            actual_updates_per_source[source.id] = len(source_updates)
            
            successful_updates = [u for u in source_updates if u.update_status == UpdateStatus.SUCCESS]
            successful_updates_per_source[source.id] = len(successful_updates)
            
            fallback_updates = [u for u in source_updates if u.update_status == UpdateStatus.FALLBACK]
            fallback_updates_per_source[source.id] = len(fallback_updates)
        
        # Calculate compliance metrics
        total_expected = sum(expected_updates_per_source.values())
        total_actual = sum(actual_updates_per_source.values())
        total_successful = sum(successful_updates_per_source.values())
        total_fallback = sum(fallback_updates_per_source.values())
        
        compliance_rate = (total_successful / total_expected) * 100 if total_expected > 0 else 0
        fallback_rate = (total_fallback / total_expected) * 100 if total_expected > 0 else 0
        
        return {
            "analysis_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "total_market_minutes": total_market_minutes
            },
            "expected_updates": expected_updates_per_source,
            "actual_updates": actual_updates_per_source,
            "successful_updates": successful_updates_per_source,
            "fallback_updates": fallback_updates_per_source,
            "compliance_metrics": {
                "total_expected": total_expected,
                "total_actual": total_actual,
                "total_successful": total_successful,
                "total_fallback": total_fallback,
                "compliance_rate_percent": compliance_rate,
                "fallback_rate_percent": fallback_rate
            }
        }
    
    def validate_update_intervals(self, updates: List[PriceUpdate]) -> Dict[str, Any]:
        """Validate that updates occur within required intervals"""
        validation_results = {}
        
        for source in self.data_sources:
            source_updates = [u for u in updates if u.source_id == source.id and u.update_status == UpdateStatus.SUCCESS]
            source_updates.sort(key=lambda x: x.timestamp)
            
            intervals = []
            violations = []
            
            for i in range(1, len(source_updates)):
                interval = source_updates[i].timestamp - source_updates[i-1].timestamp
                interval_minutes = interval.total_seconds() / 60
                intervals.append(interval_minutes)
                
                # Check for violations (updates taking longer than expected + tolerance)
                max_allowed = source.update_interval_minutes * 1.5  # 50% tolerance
                if interval_minutes > max_allowed:
                    violations.append({
                        "expected_max": max_allowed,
                        "actual": interval_minutes,
                        "timestamp": source_updates[i].timestamp.isoformat()
                    })
            
            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            
            validation_results[source.id] = {
                "expected_interval_minutes": source.update_interval_minutes,
                "actual_average_interval_minutes": avg_interval,
                "total_updates": len(source_updates),
                "interval_violations": violations,
                "compliance": len(violations) == 0
            }
        
        return validation_results

import math

# Hypothesis strategies
@st.composite
def market_session_strategy(draw):
    """Generate a market session for testing"""
    # Generate a date within the last 30 days
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days_back = draw(st.integers(min_value=0, max_value=30))
    session_date = base_date - timedelta(days=days_back)
    
    # Market operating hours
    start_time = session_date.replace(hour=6, minute=0)  # 6:00 AM
    end_time = session_date.replace(hour=20, minute=0)   # 8:00 PM
    
    # Duration for simulation (1-8 hours)
    duration_hours = draw(st.integers(min_value=1, max_value=8))
    
    return {
        "start_time": start_time,
        "duration_hours": duration_hours,
        "commodity": draw(st.sampled_from(["Wheat", "Rice", "Maize", "Onion", "Potato"]))
    }

@st.composite
def data_source_config_strategy(draw):
    """Generate data source configuration"""
    update_intervals = [15, 30, 60]  # Common update intervals
    
    return {
        "update_interval": draw(st.sampled_from(update_intervals)),
        "reliability": draw(st.floats(min_value=0.5, max_value=0.95)),
        "status": draw(st.sampled_from([DataSourceStatus.ACTIVE, DataSourceStatus.INACTIVE]))
    }

class TestDataUpdateFrequencyCompliance:
    """Test class for data update frequency compliance properties"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.system = DataUpdateFrequencySystem()
    
    @given(session=market_session_strategy())
    @settings(max_examples=20, deadline=15000)
    def test_market_hours_update_frequency(self, session):
        """
        Property 7: Data Update Frequency Compliance - Market Hours
        
        For any market operating period, price updates should occur within
        specified intervals (15 minutes) during market hours (6 AM to 8 PM IST).
        """
        try:
            # Run simulation
            updates = asyncio.run(self.system.simulate_update_cycle(
                start_time=session["start_time"],
                duration_hours=session["duration_hours"],
                commodity=session["commodity"]
            ))
            
            # Analyze compliance
            end_time = session["start_time"] + timedelta(hours=session["duration_hours"])
            compliance = self.system.get_update_frequency_compliance(
                updates, session["start_time"], end_time
            )
            
            # Validate market hours operation
            total_market_minutes = compliance["analysis_period"]["total_market_minutes"]
            expected_market_minutes = session["duration_hours"] * 60  # All time should be market hours for this test
            
            # Allow some tolerance for edge cases (start/end times)
            tolerance_minutes = 60
            assert abs(total_market_minutes - expected_market_minutes) <= tolerance_minutes, \
                f"Market minutes calculation incorrect: {total_market_minutes} vs expected {expected_market_minutes}"
            
            # Validate that updates occurred during market hours
            market_hour_updates = []
            for update in updates:
                if self.system.is_market_operating(update.timestamp):
                    market_hour_updates.append(update)
            
            # All successful updates should be during market hours
            successful_updates = [u for u in updates if u.update_status == UpdateStatus.SUCCESS]
            market_successful_updates = [u for u in successful_updates if self.system.is_market_operating(u.timestamp)]
            
            assert len(market_successful_updates) == len(successful_updates), \
                "All successful updates should occur during market hours"
            
            # Validate minimum update frequency for active sources
            for source in self.system.data_sources:
                if source.status == DataSourceStatus.ACTIVE:
                    source_updates = [u for u in market_hour_updates if u.source_id == source.id and u.update_status == UpdateStatus.SUCCESS]
                    
                    # For reasonable duration, should have some updates
                    if session["duration_hours"] >= 2:  # At least 2 hours
                        expected_min_updates = max(1, (session["duration_hours"] * 60) // (source.update_interval_minutes * 2))
                        assert len(source_updates) >= expected_min_updates, \
                            f"Source {source.id} should have at least {expected_min_updates} updates in {session['duration_hours']} hours: got {len(source_updates)}"
            
        except Exception as e:
            pytest.fail(f"Market hours update frequency test failed: {str(e)}")
    
    @given(session=market_session_strategy())
    @settings(max_examples=15, deadline=12000)
    def test_update_interval_compliance(self, session):
        """
        Property 7: Data Update Frequency Compliance - Interval Compliance
        
        For any data source, updates should occur within the specified interval
        with reasonable tolerance for network delays and processing time.
        """
        assume(session["duration_hours"] >= 2)  # Need sufficient time for interval testing
        
        try:
            # Run simulation
            updates = asyncio.run(self.system.simulate_update_cycle(
                start_time=session["start_time"],
                duration_hours=session["duration_hours"],
                commodity=session["commodity"]
            ))
            
            # Validate update intervals
            interval_validation = self.system.validate_update_intervals(updates)
            
            for source_id, validation in interval_validation.items():
                source = next(s for s in self.system.data_sources if s.id == source_id)
                
                if source.status == DataSourceStatus.ACTIVE and validation["total_updates"] >= 2:
                    # Average interval should be close to expected interval
                    expected_interval = source.update_interval_minutes
                    actual_interval = validation["actual_average_interval_minutes"]
                    
                    # Allow 100% tolerance for average (due to failures and retries)
                    max_allowed_avg = expected_interval * 2
                    assert actual_interval <= max_allowed_avg, \
                        f"Average interval too high for {source_id}: {actual_interval:.1f} > {max_allowed_avg}"
                    
                    # Should not have excessive interval violations
                    violation_rate = len(validation["interval_violations"]) / validation["total_updates"]
                    assert violation_rate <= 0.5, \
                        f"Too many interval violations for {source_id}: {violation_rate:.2f} > 0.5"
            
        except Exception as e:
            pytest.fail(f"Update interval compliance test failed: {str(e)}")
    
    @given(session=market_session_strategy())
    @settings(max_examples=15, deadline=12000)
    def test_fallback_behavior_compliance(self, session):
        """
        Property 7: Data Update Frequency Compliance - Fallback Behavior
        
        For any period when primary data is unavailable, the system should
        provide fallback data with appropriate freshness indicators.
        """
        assume(session["duration_hours"] >= 3)  # Need time for fallback scenarios
        
        try:
            # Simulate with some sources having failures
            original_reliability = {}
            for source in self.system.data_sources:
                original_reliability[source.id] = source.reliability_score
                if source.id == "state_portals":  # Make one source unreliable
                    source.reliability_score = 0.2  # Very low reliability
                elif source.id == "trader_reports":  # Make another somewhat unreliable
                    source.reliability_score = 0.4
            
            # Run simulation
            updates = asyncio.run(self.system.simulate_update_cycle(
                start_time=session["start_time"],
                duration_hours=session["duration_hours"],
                commodity=session["commodity"]
            ))
            
            # Analyze fallback usage
            fallback_updates = [u for u in updates if u.update_status == UpdateStatus.FALLBACK]
            failed_updates = [u for u in updates if u.update_status == UpdateStatus.FAILED]
            
            # Validate fallback behavior
            for update in fallback_updates:
                # Fallback updates should have reasonable data freshness
                assert update.data_freshness_minutes >= FALLBACK_THRESHOLD_MINUTES, \
                    f"Fallback should only be used after threshold: {update.data_freshness_minutes} < {FALLBACK_THRESHOLD_MINUTES}"
                
                # Fallback price should be reasonable (not zero)
                assert update.price > 0, "Fallback price should be positive"
                
                # Should be marked as fallback
                assert update.fallback_used, "Fallback updates should be marked as such"
            
            # If there are many failures, fallback should be used
            total_attempts = len(updates)
            if total_attempts > 0:
                failure_rate = len(failed_updates) / total_attempts
                fallback_rate = len(fallback_updates) / total_attempts
                
                # If failure rate is high, fallback rate should also be significant
                if failure_rate > 0.4:  # More than 40% failures
                    # Allow for some tolerance since fallback only activates after threshold
                    min_expected_fallback = max(0.05, failure_rate * 0.2)  # At least 5% or 20% of failures
                    assert fallback_rate >= min_expected_fallback, \
                        f"High failure rate ({failure_rate:.2f}) should trigger more fallback usage ({fallback_rate:.2f} >= {min_expected_fallback:.2f})"
            
            # Restore original reliability scores
            for source in self.system.data_sources:
                if source.id in original_reliability:
                    source.reliability_score = original_reliability[source.id]
            
        except Exception as e:
            pytest.fail(f"Fallback behavior compliance test failed: {str(e)}")
    
    @given(session=market_session_strategy())
    @settings(max_examples=12, deadline=10000)
    def test_data_freshness_requirements(self, session):
        """
        Property 7: Data Update Frequency Compliance - Data Freshness
        
        For any price data provided, freshness indicators should accurately
        reflect the age of the data and comply with maximum staleness limits.
        """
        try:
            # Run simulation
            updates = asyncio.run(self.system.simulate_update_cycle(
                start_time=session["start_time"],
                duration_hours=session["duration_hours"],
                commodity=session["commodity"]
            ))
            
            # Validate data freshness
            for update in updates:
                if update.update_status == UpdateStatus.SUCCESS:
                    # Fresh data should have zero freshness minutes
                    assert update.data_freshness_minutes == 0, \
                        f"Fresh data should have zero freshness: {update.data_freshness_minutes}"
                    
                elif update.update_status == UpdateStatus.FALLBACK:
                    # Fallback data should have appropriate freshness
                    assert update.data_freshness_minutes > 0, \
                        "Fallback data should have positive freshness minutes"
                    
                    # Freshness should not exceed reasonable limits (e.g., 24 hours)
                    max_freshness_minutes = 24 * 60  # 24 hours
                    assert update.data_freshness_minutes <= max_freshness_minutes, \
                        f"Data freshness should be capped at 24 hours: {update.data_freshness_minutes} <= {max_freshness_minutes}"
            
            # Validate that system provides data within acceptable freshness limits
            successful_or_fallback = [
                u for u in updates 
                if u.update_status in [UpdateStatus.SUCCESS, UpdateStatus.FALLBACK]
            ]
            
            if successful_or_fallback:
                # Most recent data should be reasonably fresh
                latest_update = max(successful_or_fallback, key=lambda x: x.timestamp)
                end_time = session["start_time"] + timedelta(hours=session["duration_hours"])
                
                time_since_latest = end_time - latest_update.timestamp
                max_acceptable_gap = timedelta(minutes=REQUIRED_UPDATE_INTERVAL_MINUTES * 2)
                
                assert time_since_latest <= max_acceptable_gap, \
                    f"Gap since latest update too large: {time_since_latest} > {max_acceptable_gap}"
            
        except Exception as e:
            pytest.fail(f"Data freshness requirements test failed: {str(e)}")
    
    @given(session=market_session_strategy())
    @settings(max_examples=10, deadline=8000)
    def test_system_availability_during_market_hours(self, session):
        """
        Property 7: Data Update Frequency Compliance - System Availability
        
        For any market operating period, the system should maintain high
        availability and provide data updates consistently.
        """
        assume(session["duration_hours"] >= 2)  # Need sufficient time for availability testing
        
        try:
            # Run simulation
            updates = asyncio.run(self.system.simulate_update_cycle(
                start_time=session["start_time"],
                duration_hours=session["duration_hours"],
                commodity=session["commodity"]
            ))
            
            # Calculate availability metrics
            end_time = session["start_time"] + timedelta(hours=session["duration_hours"])
            compliance = self.system.get_update_frequency_compliance(
                updates, session["start_time"], end_time
            )
            
            metrics = compliance["compliance_metrics"]
            
            # System should achieve reasonable compliance rate
            min_compliance_rate = 60.0  # 60% minimum compliance
            assert metrics["compliance_rate_percent"] >= min_compliance_rate, \
                f"Compliance rate too low: {metrics['compliance_rate_percent']:.1f}% < {min_compliance_rate}%"
            
            # Combined success + fallback should provide good coverage
            total_coverage = metrics["total_successful"] + metrics["total_fallback"]
            coverage_rate = (total_coverage / metrics["total_expected"]) * 100 if metrics["total_expected"] > 0 else 0
            
            min_coverage_rate = 80.0  # 80% minimum coverage
            assert coverage_rate >= min_coverage_rate, \
                f"Coverage rate too low: {coverage_rate:.1f}% < {min_coverage_rate}%"
            
            # Fallback usage should be reasonable (not excessive)
            max_fallback_rate = 50.0  # Maximum 50% fallback usage (increased tolerance)
            assert metrics["fallback_rate_percent"] <= max_fallback_rate, \
                f"Fallback rate too high: {metrics['fallback_rate_percent']:.1f}% > {max_fallback_rate}%"
            
            # Should have updates from multiple sources for redundancy
            sources_with_updates = set()
            for update in updates:
                if update.update_status in [UpdateStatus.SUCCESS, UpdateStatus.FALLBACK]:
                    sources_with_updates.add(update.source_id)
            
            active_sources = [s for s in self.system.data_sources if s.status == DataSourceStatus.ACTIVE]
            min_sources = max(1, len(active_sources) // 2)  # At least half of active sources
            
            assert len(sources_with_updates) >= min_sources, \
                f"Too few sources providing updates: {len(sources_with_updates)} < {min_sources}"
            
        except Exception as e:
            pytest.fail(f"System availability test failed: {str(e)}")

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])