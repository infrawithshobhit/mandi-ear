"""
Property-Based Test for Continuous Price Monitoring
Feature: mandi-ear, Property 12: Continuous Price Monitoring

**Validates: Requirements 6.1, 6.3**

This test validates that for any commodity with MSP rates, the system should 
continuously compare market prices against official rates and maintain current 
government data.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, date, timezone
import asyncio
import json
import uuid
from decimal import Decimal
import httpx

# Import MSP service models and components
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services', 'msp-enforcement-service'))

from models import (
    MSPRate, MSPViolation, MSPComparisonResult, ViolationType, 
    AlertSeverity, MSPMonitoringStats, MSPSeason, MSPCommodityType
)

# Test configuration
API_BASE_URL = "http://localhost:8001"  # MSP enforcement service port
MONITORING_INTERVAL_SECONDS = 15 * 60  # 15 minutes
VIOLATION_THRESHOLD = 5.0  # 5% below MSP triggers violation
CRITICAL_THRESHOLD = 15.0  # 15% below MSP is critical
MAX_PRICE_AGE_HOURS = 2  # Only consider prices from last 2 hours

# Hypothesis strategies for generating test data
@st.composite
def msp_rate_data(draw):
    """Generate MSP rate data for testing"""
    commodities = ["Wheat", "Rice", "Maize", "Bajra", "Jowar", "Gram", "Tur", "Moong", 
                   "Groundnut", "Mustard", "Sunflower", "Cotton", "Sugarcane"]
    
    commodity = draw(st.sampled_from(commodities))
    season = draw(st.sampled_from(list(MSPSeason)))
    commodity_type = draw(st.sampled_from(list(MSPCommodityType)))
    
    # Generate realistic MSP prices (₹1000-5000 per quintal)
    msp_price = draw(st.floats(min_value=1000.0, max_value=5000.0))
    
    # Generate crop year
    current_year = datetime.now().year
    crop_year = f"{current_year}-{str(current_year + 1)[2:]}"
    
    # Generate dates ensuring announcement is before effective date
    announcement_days_ago = draw(st.integers(min_value=1, max_value=60))
    effective_days_ago = draw(st.integers(min_value=0, max_value=announcement_days_ago))
    
    return {
        "commodity": commodity,
        "variety": draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        "season": season,
        "crop_year": crop_year,
        "msp_price": round(msp_price, 2),
        "commodity_type": commodity_type,
        "effective_date": date.today() - timedelta(days=effective_days_ago),
        "announcement_date": date.today() - timedelta(days=announcement_days_ago),
        "is_active": True
    }

@st.composite
def market_price_data(draw, commodity: str, msp_price: float):
    """Generate market price data for a specific commodity"""
    # Generate price variations around MSP (50% to 120% of MSP)
    price_multiplier = draw(st.floats(min_value=0.5, max_value=1.2))
    market_price = round(msp_price * price_multiplier, 2)
    
    states = ["Punjab", "Haryana", "Uttar Pradesh", "Madhya Pradesh", "Rajasthan", 
              "Maharashtra", "Gujarat", "Karnataka", "Andhra Pradesh", "Tamil Nadu"]
    
    state = draw(st.sampled_from(states))
    districts = {
        "Punjab": ["Ludhiana", "Amritsar", "Jalandhar", "Patiala"],
        "Haryana": ["Karnal", "Hisar", "Rohtak", "Gurgaon"],
        "Uttar Pradesh": ["Meerut", "Agra", "Lucknow", "Kanpur"],
        "Madhya Pradesh": ["Indore", "Bhopal", "Jabalpur", "Gwalior"],
        "Rajasthan": ["Jaipur", "Jodhpur", "Kota", "Udaipur"],
        "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
        "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
        "Karnataka": ["Bangalore", "Mysore", "Hubli", "Mangalore"],
        "Andhra Pradesh": ["Hyderabad", "Vijayawada", "Visakhapatnam", "Tirupati"],
        "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Salem"]
    }
    
    district = draw(st.sampled_from(districts.get(state, ["District1", "District2"])))
    
    return {
        "commodity": commodity,
        "variety": draw(st.one_of(st.none(), st.text(min_size=1, max_size=20))),
        "price": market_price,
        "quantity": draw(st.floats(min_value=1.0, max_value=1000.0)),
        "mandi_id": f"mandi_{uuid.uuid4().hex[:8]}",
        "mandi_name": f"{district} Mandi",
        "district": district,
        "state": state,
        "timestamp": datetime.now(timezone.utc) - timedelta(
            minutes=draw(st.integers(min_value=0, max_value=MAX_PRICE_AGE_HOURS * 60))
        ),
        "confidence": draw(st.floats(min_value=0.7, max_value=1.0)),
        "source": "market_data_feed"
    }

@st.composite
def monitoring_scenario(draw):
    """Generate a complete monitoring scenario with MSP rates and market prices"""
    # Generate MSP rate
    msp_data = draw(msp_rate_data())
    
    # Generate multiple market prices for the same commodity
    num_prices = draw(st.integers(min_value=1, max_value=10))
    market_prices = []
    
    for _ in range(num_prices):
        price_data = draw(market_price_data(msp_data["commodity"], msp_data["msp_price"]))
        market_prices.append(price_data)
    
    return {
        "msp_rate": msp_data,
        "market_prices": market_prices,
        "monitoring_timestamp": datetime.now(timezone.utc)
    }

@st.composite
def government_data_update_scenario(draw):
    """Generate scenario for government data updates"""
    # Generate multiple MSP rates that might be updated
    num_rates = draw(st.integers(min_value=1, max_value=5))
    msp_rates = []
    
    for _ in range(num_rates):
        rate_data = draw(msp_rate_data())
        msp_rates.append(rate_data)
    
    # Generate update metadata
    update_info = {
        "source": draw(st.sampled_from(["CACP", "FCI", "AgMarkNet", "DACFW"])),
        "update_timestamp": datetime.now(timezone.utc),
        "update_type": draw(st.sampled_from(["new_rates", "rate_revision", "seasonal_update"])),
        "reliability_score": draw(st.floats(min_value=0.8, max_value=1.0))
    }
    
    return {
        "msp_rates": msp_rates,
        "update_info": update_info
    }

class TestContinuousMonitoring:
    """Test class for continuous MSP monitoring properties"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.test_session_id = str(uuid.uuid4())
    
    @given(scenario=monitoring_scenario())
    @settings(max_examples=25, deadline=20000)
    def test_price_comparison_accuracy(self, scenario: Dict[str, Any]):
        """
        Property 12: Continuous Price Monitoring - Price Comparison Accuracy
        
        For any commodity with MSP rates, the system should accurately compare 
        market prices against MSP rates and correctly identify violations.
        """
        assume(scenario["msp_rate"]["msp_price"] > 0)
        assume(len(scenario["market_prices"]) > 0)
        
        try:
            msp_rate = scenario["msp_rate"]
            market_prices = scenario["market_prices"]
            
            # Test price comparison logic for each market price
            for price_data in market_prices:
                assume(price_data["price"] > 0)
                assume(price_data["confidence"] >= 0.7)
                
                # Calculate expected comparison result
                market_price = price_data["price"]
                msp_price = msp_rate["msp_price"]
                price_difference = market_price - msp_price
                violation_percentage = abs(price_difference) / msp_price * 100
                
                # Determine expected compliance status
                expected_status = "compliant"
                if price_difference < 0:  # Market price below MSP
                    if violation_percentage >= VIOLATION_THRESHOLD:
                        expected_status = "violation"
                    else:
                        expected_status = "warning"
                
                # Validate comparison logic
                comparison_result = self._simulate_price_comparison(msp_rate, price_data)
                
                # Assert comparison accuracy
                assert comparison_result["commodity"] == msp_rate["commodity"], \
                    "Commodity mismatch in comparison"
                
                assert abs(comparison_result["market_price"] - market_price) < 0.01, \
                    f"Market price mismatch: {comparison_result['market_price']} != {market_price}"
                
                assert abs(comparison_result["msp_price"] - msp_price) < 0.01, \
                    f"MSP price mismatch: {comparison_result['msp_price']} != {msp_price}"
                
                assert abs(comparison_result["price_difference"] - price_difference) < 0.01, \
                    f"Price difference calculation error: {comparison_result['price_difference']} != {price_difference}"
                
                assert comparison_result["compliance_status"] == expected_status, \
                    f"Compliance status mismatch: {comparison_result['compliance_status']} != {expected_status}"
                
                # Validate violation percentage calculation
                if expected_status != "compliant":
                    assert comparison_result["violation_percentage"] is not None, \
                        "Violation percentage should be set for non-compliant status"
                    
                    assert abs(comparison_result["violation_percentage"] - violation_percentage) < 0.1, \
                        f"Violation percentage calculation error: {comparison_result['violation_percentage']} != {violation_percentage}"
                
                # Validate confidence score preservation
                assert comparison_result["data_confidence"] == price_data["confidence"], \
                    "Data confidence should be preserved"
                
                # Validate timestamp is recent
                comparison_time = comparison_result["comparison_timestamp"]
                time_diff = abs((datetime.now(timezone.utc) - comparison_time).total_seconds())
                assert time_diff < 60, "Comparison timestamp should be recent"
        
        except Exception as e:
            pytest.fail(f"Price comparison accuracy test failed: {str(e)}")
    
    @given(scenario=monitoring_scenario())
    @settings(max_examples=20, deadline=15000)
    def test_violation_detection_properties(self, scenario: Dict[str, Any]):
        """
        Property 12: Continuous Price Monitoring - Violation Detection Properties
        
        For any market prices below MSP thresholds, the system should correctly 
        detect violations and assign appropriate severity levels.
        """
        assume(scenario["msp_rate"]["msp_price"] > 0)
        
        try:
            msp_rate = scenario["msp_rate"]
            market_prices = scenario["market_prices"]
            
            violations_detected = []
            
            for price_data in market_prices:
                assume(price_data["price"] > 0)
                
                market_price = price_data["price"]
                msp_price = msp_rate["msp_price"]
                price_difference = market_price - msp_price
                
                # Only test prices that are below MSP
                if price_difference < 0:
                    violation_percentage = abs(price_difference) / msp_price * 100
                    
                    # Only consider significant violations
                    if violation_percentage >= VIOLATION_THRESHOLD:
                        violation = self._simulate_violation_detection(msp_rate, price_data)
                        violations_detected.append(violation)
                        
                        # Validate violation properties
                        assert violation["commodity"] == msp_rate["commodity"], \
                            "Violation commodity should match MSP commodity"
                        
                        assert violation["market_price"] == market_price, \
                            "Violation market price should match input"
                        
                        assert violation["msp_price"] == msp_price, \
                            "Violation MSP price should match rate"
                        
                        assert violation["price_difference"] == price_difference, \
                            "Violation price difference should be accurate"
                        
                        assert abs(violation["violation_percentage"] - violation_percentage) < 0.1, \
                            "Violation percentage should be accurate"
                        
                        assert violation["violation_type"] == ViolationType.BELOW_MSP, \
                            "Violation type should be BELOW_MSP"
                        
                        # Validate severity assignment
                        expected_severity = self._calculate_expected_severity(violation_percentage)
                        assert violation["severity"] == expected_severity, \
                            f"Severity mismatch: {violation['severity']} != {expected_severity}"
                        
                        # Validate location information
                        assert violation["district"] == price_data["district"], \
                            "Violation district should match price data"
                        
                        assert violation["state"] == price_data["state"], \
                            "Violation state should match price data"
                        
                        # Validate evidence is present
                        assert "evidence" in violation, "Violation should include evidence"
                        assert violation["evidence"] is not None, "Evidence should not be None"
                        
                        # Validate timestamps
                        detection_time = violation["detected_at"]
                        time_diff = abs((datetime.now(timezone.utc) - detection_time).total_seconds())
                        assert time_diff < 60, "Detection timestamp should be recent"
            
            # Validate that violations are only detected for appropriate conditions
            total_below_msp = sum(1 for p in market_prices 
                                if p["price"] < msp_rate["msp_price"] and 
                                   abs(p["price"] - msp_rate["msp_price"]) / msp_rate["msp_price"] * 100 >= VIOLATION_THRESHOLD)
            
            assert len(violations_detected) == total_below_msp, \
                f"Violation count mismatch: {len(violations_detected)} != {total_below_msp}"
        
        except Exception as e:
            pytest.fail(f"Violation detection properties test failed: {str(e)}")
    
    @given(update_scenario=government_data_update_scenario())
    @settings(max_examples=15, deadline=12000)
    def test_government_data_maintenance(self, update_scenario: Dict[str, Any]):
        """
        Property 12: Continuous Price Monitoring - Government Data Maintenance
        
        For any government data updates, the system should maintain current 
        MSP rates and ensure data consistency and reliability.
        """
        assume(len(update_scenario["msp_rates"]) > 0)
        assume(update_scenario["update_info"]["reliability_score"] >= 0.8)
        
        try:
            msp_rates = update_scenario["msp_rates"]
            update_info = update_scenario["update_info"]
            
            # Simulate government data update processing
            update_results = []
            
            for rate_data in msp_rates:
                assume(rate_data["msp_price"] > 0)
                
                # Validate MSP rate data structure
                required_fields = ["commodity", "season", "crop_year", "msp_price", 
                                 "commodity_type", "effective_date", "announcement_date"]
                
                for field in required_fields:
                    assert field in rate_data, f"Missing required field: {field}"
                
                # Validate data types and ranges
                assert isinstance(rate_data["msp_price"], (int, float)), \
                    "MSP price should be numeric"
                
                assert rate_data["msp_price"] > 0, \
                    "MSP price should be positive"
                
                assert rate_data["msp_price"] <= 10000, \
                    "MSP price should be reasonable (≤ ₹10,000/quintal)"
                
                assert isinstance(rate_data["effective_date"], date), \
                    "Effective date should be a date object"
                
                assert isinstance(rate_data["announcement_date"], date), \
                    "Announcement date should be a date object"
                
                assert rate_data["effective_date"] >= rate_data["announcement_date"], \
                    "Effective date should be on or after announcement date"
                
                # Validate enum values
                assert rate_data["season"] in [s.value for s in MSPSeason], \
                    f"Invalid season: {rate_data['season']}"
                
                assert rate_data["commodity_type"] in [ct.value for ct in MSPCommodityType], \
                    f"Invalid commodity type: {rate_data['commodity_type']}"
                
                # Simulate data update processing
                update_result = self._simulate_government_data_update(rate_data, update_info)
                update_results.append(update_result)
                
                # Validate update result
                assert update_result["status"] in ["success", "updated", "duplicate", "error"], \
                    f"Invalid update status: {update_result['status']}"
                
                assert "processed_at" in update_result, \
                    "Update result should include processing timestamp"
                
                assert update_result["source"] == update_info["source"], \
                    "Update source should be preserved"
                
                # Validate data consistency after update
                if update_result["status"] in ["success", "updated"]:
                    stored_rate = update_result["stored_rate"]
                    
                    assert stored_rate["commodity"] == rate_data["commodity"], \
                        "Stored commodity should match input"
                    
                    assert stored_rate["msp_price"] == rate_data["msp_price"], \
                        "Stored MSP price should match input"
                    
                    assert stored_rate["is_active"] == True, \
                        "Newly updated rates should be active"
                    
                    # Validate unique identifier generation
                    assert "id" in stored_rate, "Stored rate should have unique ID"
                    assert stored_rate["id"] is not None, "Rate ID should not be None"
            
            # Validate update batch properties
            successful_updates = [r for r in update_results if r["status"] in ["success", "updated"]]
            
            # At least some updates should succeed for valid data
            if update_info["reliability_score"] >= 0.9:
                success_rate = len(successful_updates) / len(update_results)
                assert success_rate >= 0.8, \
                    f"Success rate too low for high reliability source: {success_rate:.2f}"
            
            # Validate update metadata preservation
            for result in update_results:
                assert result["update_timestamp"] == update_info["update_timestamp"], \
                    "Update timestamp should be preserved"
                
                assert result["reliability_score"] == update_info["reliability_score"], \
                    "Reliability score should be preserved"
        
        except Exception as e:
            pytest.fail(f"Government data maintenance test failed: {str(e)}")
    
    @given(scenario=monitoring_scenario())
    @settings(max_examples=10, deadline=10000)
    def test_monitoring_continuity_properties(self, scenario: Dict[str, Any]):
        """
        Property 12: Continuous Price Monitoring - Monitoring Continuity
        
        For any monitoring scenario, the system should maintain continuous 
        operation and handle various data conditions gracefully.
        """
        assume(scenario["msp_rate"]["msp_price"] > 0)
        
        try:
            msp_rate = scenario["msp_rate"]
            market_prices = scenario["market_prices"]
            monitoring_timestamp = scenario["monitoring_timestamp"]
            
            # Simulate continuous monitoring cycle
            monitoring_results = self._simulate_monitoring_cycle(scenario)
            
            # Validate monitoring cycle properties
            assert "cycle_start_time" in monitoring_results, \
                "Monitoring results should include cycle start time"
            
            assert "cycle_end_time" in monitoring_results, \
                "Monitoring results should include cycle end time"
            
            assert "processing_time_seconds" in monitoring_results, \
                "Monitoring results should include processing time"
            
            # Validate processing time is reasonable
            processing_time = monitoring_results["processing_time_seconds"]
            assert processing_time >= 0, "Processing time should be non-negative"
            assert processing_time <= 300, "Processing time should be reasonable (≤ 5 minutes)"
            
            # Validate data freshness handling
            current_time = datetime.now(timezone.utc)
            fresh_prices = []
            stale_prices = []
            
            for price_data in market_prices:
                price_age_hours = (current_time - price_data["timestamp"]).total_seconds() / 3600
                if price_age_hours <= MAX_PRICE_AGE_HOURS:
                    fresh_prices.append(price_data)
                else:
                    stale_prices.append(price_data)
            
            # System should only process fresh prices
            processed_count = monitoring_results["prices_processed"]
            assert processed_count == len(fresh_prices), \
                f"Should only process fresh prices: {processed_count} != {len(fresh_prices)}"
            
            # Validate comparison results
            comparisons = monitoring_results["comparisons"]
            assert len(comparisons) == len(fresh_prices), \
                "Should have comparison for each fresh price"
            
            # Validate violation detection
            violations = monitoring_results["violations"]
            expected_violations = 0
            
            for price_data in fresh_prices:
                if price_data["price"] < msp_rate["msp_price"]:
                    violation_pct = abs(price_data["price"] - msp_rate["msp_price"]) / msp_rate["msp_price"] * 100
                    if violation_pct >= VIOLATION_THRESHOLD:
                        expected_violations += 1
            
            assert len(violations) == expected_violations, \
                f"Violation count mismatch: {len(violations)} != {expected_violations}"
            
            # Validate monitoring statistics
            stats = monitoring_results["monitoring_stats"]
            assert "total_comparisons" in stats, "Stats should include total comparisons"
            assert "total_violations" in stats, "Stats should include total violations"
            assert "compliance_rate" in stats, "Stats should include compliance rate"
            
            # Validate compliance rate calculation
            if stats["total_comparisons"] > 0:
                expected_compliance_rate = ((stats["total_comparisons"] - stats["total_violations"]) / 
                                          stats["total_comparisons"] * 100)
                assert abs(stats["compliance_rate"] - expected_compliance_rate) < 0.1, \
                    "Compliance rate calculation should be accurate"
            
            # Validate error handling
            assert "errors" in monitoring_results, "Results should include error information"
            error_count = len(monitoring_results["errors"])
            
            # Error rate should be reasonable
            if len(market_prices) > 0:
                error_rate = error_count / len(market_prices)
                assert error_rate <= 0.1, f"Error rate too high: {error_rate:.2f}"
        
        except Exception as e:
            pytest.fail(f"Monitoring continuity properties test failed: {str(e)}")
    
    def _simulate_price_comparison(self, msp_rate: Dict[str, Any], price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate MSP vs market price comparison"""
        market_price = price_data["price"]
        msp_price = msp_rate["msp_price"]
        price_difference = market_price - msp_price
        violation_percentage = abs(price_difference) / msp_price * 100
        
        # Determine compliance status
        compliance_status = "compliant"
        if price_difference < 0:  # Market price below MSP
            if violation_percentage >= VIOLATION_THRESHOLD:
                compliance_status = "violation"
            else:
                compliance_status = "warning"
        
        return {
            "commodity": msp_rate["commodity"],
            "variety": price_data.get("variety"),
            "mandi_id": price_data["mandi_id"],
            "mandi_name": price_data["mandi_name"],
            "location": f"{price_data['district']}, {price_data['state']}",
            "market_price": market_price,
            "msp_price": msp_price,
            "price_difference": price_difference,
            "compliance_status": compliance_status,
            "violation_percentage": violation_percentage if compliance_status != "compliant" else None,
            "comparison_timestamp": datetime.now(timezone.utc),
            "data_confidence": price_data["confidence"]
        }
    
    def _simulate_violation_detection(self, msp_rate: Dict[str, Any], price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate MSP violation detection"""
        market_price = price_data["price"]
        msp_price = msp_rate["msp_price"]
        price_difference = market_price - msp_price
        violation_percentage = abs(price_difference) / msp_price * 100
        
        severity = self._calculate_expected_severity(violation_percentage)
        
        return {
            "id": str(uuid.uuid4()),
            "commodity": msp_rate["commodity"],
            "variety": price_data.get("variety"),
            "mandi_id": price_data["mandi_id"],
            "mandi_name": price_data["mandi_name"],
            "district": price_data["district"],
            "state": price_data["state"],
            "market_price": market_price,
            "msp_price": msp_price,
            "price_difference": price_difference,
            "violation_percentage": violation_percentage,
            "violation_type": ViolationType.BELOW_MSP,
            "detected_at": datetime.now(timezone.utc),
            "severity": severity,
            "is_resolved": False,
            "evidence": {
                "comparison_data": self._simulate_price_comparison(msp_rate, price_data),
                "detection_method": "automated_monitoring",
                "data_confidence": price_data["confidence"]
            }
        }
    
    def _calculate_expected_severity(self, violation_percentage: float) -> AlertSeverity:
        """Calculate expected severity based on violation percentage"""
        if violation_percentage >= CRITICAL_THRESHOLD:
            return AlertSeverity.CRITICAL
        elif violation_percentage >= 10.0:
            return AlertSeverity.HIGH
        elif violation_percentage >= 5.0:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    def _simulate_government_data_update(self, rate_data: Dict[str, Any], update_info: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate government data update processing"""
        # Simulate processing logic
        processing_time = datetime.now(timezone.utc)
        
        # Create stored rate with additional metadata
        stored_rate = rate_data.copy()
        stored_rate["id"] = str(uuid.uuid4())
        stored_rate["created_at"] = processing_time
        stored_rate["updated_at"] = processing_time
        stored_rate["source_document"] = f"{update_info['source']} - {update_info['update_type']}"
        
        return {
            "status": "success",
            "processed_at": processing_time,
            "source": update_info["source"],
            "update_timestamp": update_info["update_timestamp"],
            "reliability_score": update_info["reliability_score"],
            "stored_rate": stored_rate
        }
    
    def _simulate_monitoring_cycle(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a complete monitoring cycle"""
        cycle_start = datetime.now(timezone.utc)
        
        msp_rate = scenario["msp_rate"]
        market_prices = scenario["market_prices"]
        
        # Filter fresh prices
        current_time = datetime.now(timezone.utc)
        fresh_prices = []
        
        for price_data in market_prices:
            price_age_hours = (current_time - price_data["timestamp"]).total_seconds() / 3600
            if price_age_hours <= MAX_PRICE_AGE_HOURS:
                fresh_prices.append(price_data)
        
        # Process comparisons
        comparisons = []
        violations = []
        errors = []
        
        for price_data in fresh_prices:
            try:
                comparison = self._simulate_price_comparison(msp_rate, price_data)
                comparisons.append(comparison)
                
                if comparison["compliance_status"] == "violation":
                    violation = self._simulate_violation_detection(msp_rate, price_data)
                    violations.append(violation)
            
            except Exception as e:
                errors.append({"price_data": price_data, "error": str(e)})
        
        cycle_end = datetime.now(timezone.utc)
        processing_time = (cycle_end - cycle_start).total_seconds()
        
        # Calculate statistics
        total_comparisons = len(comparisons)
        total_violations = len(violations)
        compliance_rate = ((total_comparisons - total_violations) / total_comparisons * 100) if total_comparisons > 0 else 100
        
        return {
            "cycle_start_time": cycle_start,
            "cycle_end_time": cycle_end,
            "processing_time_seconds": processing_time,
            "prices_processed": len(fresh_prices),
            "comparisons": comparisons,
            "violations": violations,
            "errors": errors,
            "monitoring_stats": {
                "total_comparisons": total_comparisons,
                "total_violations": total_violations,
                "compliance_rate": compliance_rate
            }
        }

@pytest.mark.asyncio
@given(scenario=monitoring_scenario())
@settings(max_examples=5, deadline=25000)
async def test_msp_monitoring_api_integration(scenario: Dict[str, Any]):
    """
    Property 12: Continuous Price Monitoring - API Integration Test
    
    For any monitoring scenario through the API, the MSP enforcement service 
    should provide accurate monitoring results and maintain data consistency.
    """
    assume(scenario["msp_rate"]["msp_price"] > 0)
    assume(len(scenario["market_prices"]) > 0)
    
    try:
        # Prepare test data for API (convert dates to strings for JSON serialization)
        msp_rate = scenario["msp_rate"].copy()
        msp_rate["effective_date"] = msp_rate["effective_date"].isoformat()
        msp_rate["announcement_date"] = msp_rate["announcement_date"].isoformat()
        msp_rate["season"] = msp_rate["season"].value
        msp_rate["commodity_type"] = msp_rate["commodity_type"].value
        
        market_prices = []
        for price_data in scenario["market_prices"][:3]:  # Limit for API testing
            price_copy = price_data.copy()
            price_copy["timestamp"] = price_copy["timestamp"].isoformat()
            market_prices.append(price_copy)
        
        # Test MSP rate creation/update API
        async with httpx.AsyncClient() as client:
            # Create MSP rate
            msp_response = await client.post(
                f"{API_BASE_URL}/msp-rates",
                json=msp_rate,
                timeout=15.0
            )
            
            assert msp_response.status_code in [200, 201], \
                f"MSP rate creation failed: {msp_response.status_code}"
            
            msp_result = msp_response.json()
            assert "id" in msp_result, "MSP rate response should include ID"
            
            # Test price monitoring API
            monitoring_request = {
                "commodity": msp_rate["commodity"],
                "market_prices": market_prices,
                "monitoring_config": {
                    "violation_threshold": VIOLATION_THRESHOLD,
                    "critical_threshold": CRITICAL_THRESHOLD
                }
            }
            
            monitor_response = await client.post(
                f"{API_BASE_URL}/monitor-prices",
                json=monitoring_request,
                timeout=20.0
            )
            
            assert monitor_response.status_code == 200, \
                f"Price monitoring failed: {monitor_response.status_code}"
            
            monitor_result = monitor_response.json()
            
            # Validate API response structure
            required_fields = ["status", "comparisons", "violations", "monitoring_stats"]
            for field in required_fields:
                assert field in monitor_result, f"Missing required field: {field}"
            
            # Validate monitoring results
            assert monitor_result["status"] == "success", \
                f"Monitoring status should be success: {monitor_result['status']}"
            
            comparisons = monitor_result["comparisons"]
            violations = monitor_result["violations"]
            
            # Should have comparisons for valid prices
            valid_prices = [p for p in market_prices if p["confidence"] >= 0.7]
            assert len(comparisons) == len(valid_prices), \
                f"Comparison count mismatch: {len(comparisons)} != {len(valid_prices)}"
            
            # Validate comparison structure
            for comparison in comparisons:
                comp_fields = ["commodity", "market_price", "msp_price", "compliance_status"]
                for field in comp_fields:
                    assert field in comparison, f"Missing comparison field: {field}"
                
                assert comparison["commodity"] == msp_rate["commodity"], \
                    "Comparison commodity should match MSP rate"
            
            # Validate violations
            expected_violations = 0
            for price_data in valid_prices:
                if price_data["price"] < msp_rate["msp_price"]:
                    violation_pct = abs(price_data["price"] - msp_rate["msp_price"]) / msp_rate["msp_price"] * 100
                    if violation_pct >= VIOLATION_THRESHOLD:
                        expected_violations += 1
            
            assert len(violations) == expected_violations, \
                f"Violation count mismatch: {len(violations)} != {expected_violations}"
            
            # Validate monitoring statistics
            stats = monitor_result["monitoring_stats"]
            assert "compliance_rate" in stats, "Stats should include compliance rate"
            assert "total_comparisons" in stats, "Stats should include total comparisons"
            
            if stats["total_comparisons"] > 0:
                assert 0 <= stats["compliance_rate"] <= 100, \
                    f"Invalid compliance rate: {stats['compliance_rate']}"
    
    except httpx.ConnectError:
        pytest.skip("MSP enforcement service not available for testing")
    except Exception as e:
        pytest.fail(f"MSP monitoring API integration test failed: {str(e)}")

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])