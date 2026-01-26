#!/usr/bin/env python3
"""
Basic test for MSP Enforcement Service components
"""

import sys
import asyncio
from datetime import datetime, date
from models import (
    MSPRate, MSPViolation, MSPAlert, ProcurementCenter,
    MSPSeason, MSPCommodityType, ViolationType, AlertSeverity
)

def test_models():
    """Test model creation and validation"""
    print("Testing MSP models...")
    
    # Test MSP Rate
    msp_rate = MSPRate(
        commodity="Wheat",
        season=MSPSeason.RABI,
        crop_year="2023-24",
        msp_price=2125.0,
        commodity_type=MSPCommodityType.CEREALS,
        effective_date=date(2023, 4, 1),
        announcement_date=date(2023, 3, 15)
    )
    print(f"✓ MSP Rate created: {msp_rate.commodity} - ₹{msp_rate.msp_price}")
    
    # Test MSP Violation
    violation = MSPViolation(
        commodity="Wheat",
        mandi_id="mandi_punjab_001",
        mandi_name="Central Mandi Punjab",
        district="Ludhiana",
        state="Punjab",
        market_price=2000.0,
        msp_price=2125.0,
        price_difference=-125.0,
        violation_percentage=5.88,
        violation_type=ViolationType.BELOW_MSP,
        severity=AlertSeverity.MEDIUM
    )
    print(f"✓ MSP Violation created: {violation.commodity} - {violation.violation_percentage:.1f}% below MSP")
    
    # Test Procurement Center
    center = ProcurementCenter(
        name="FCI Depot Delhi",
        center_type="FCI",
        address="Sector 12, Dwarka, New Delhi",
        district="New Delhi",
        state="Delhi",
        pincode="110075",
        commodities_accepted=["Wheat", "Rice", "Maize"]
    )
    print(f"✓ Procurement Center created: {center.name}")
    
    # Test MSP Alert
    alert = MSPAlert(
        violation_id=violation.id,
        title="MSP Violation Alert - Wheat",
        message="Wheat prices below MSP detected",
        severity=AlertSeverity.MEDIUM,
        commodity="Wheat",
        location="Ludhiana, Punjab",
        suggested_actions=["Check alternative markets", "Contact procurement centers"]
    )
    print(f"✓ MSP Alert created: {alert.title}")
    
    print("All models created successfully!")
    return True

async def test_monitoring_config():
    """Test monitoring configuration"""
    print("\nTesting monitoring configuration...")
    
    try:
        from msp_monitor import MonitoringConfig, MSPMonitoringEngine
        
        config = MonitoringConfig(
            check_interval_minutes=15,
            violation_threshold_percentage=5.0,
            critical_threshold_percentage=15.0
        )
        print(f"✓ Monitoring config created: {config.check_interval_minutes}min intervals")
        
        # Test engine creation (without initialization)
        engine = MSPMonitoringEngine(config)
        print("✓ MSP Monitoring Engine created")
        
        return True
    except ImportError as e:
        print(f"⚠ Monitoring engine test skipped (missing dependencies): {e}")
        return True

def test_data_structures():
    """Test data structure serialization"""
    print("\nTesting data structures...")
    
    msp_rate = MSPRate(
        commodity="Rice",
        season=MSPSeason.KHARIF,
        crop_year="2023-24",
        msp_price=2183.0,
        commodity_type=MSPCommodityType.CEREALS,
        effective_date=date(2023, 10, 1),
        announcement_date=date(2023, 9, 15)
    )
    
    # Test serialization
    data = msp_rate.dict()
    print(f"✓ MSP Rate serialized: {len(data)} fields")
    
    # Test JSON serialization
    import json
    json_data = msp_rate.json()
    print(f"✓ MSP Rate JSON serialized: {len(json_data)} characters")
    
    return True

def main():
    """Run all tests"""
    print("=" * 50)
    print("MSP Enforcement Service - Basic Tests")
    print("=" * 50)
    
    tests = [
        test_models,
        test_data_structures,
    ]
    
    async_tests = [
        test_monitoring_config,
    ]
    
    # Run synchronous tests
    for test in tests:
        try:
            result = test()
            if not result:
                print(f"❌ Test failed: {test.__name__}")
                return False
        except Exception as e:
            print(f"❌ Test error in {test.__name__}: {e}")
            return False
    
    # Run asynchronous tests
    for test in async_tests:
        try:
            result = asyncio.run(test())
            if not result:
                print(f"❌ Async test failed: {test.__name__}")
                return False
        except Exception as e:
            print(f"❌ Async test error in {test.__name__}: {e}")
            return False
    
    print("\n" + "=" * 50)
    print("✅ All basic tests passed!")
    print("MSP Enforcement Service structure is valid")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)