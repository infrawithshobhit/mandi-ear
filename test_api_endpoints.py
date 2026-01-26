#!/usr/bin/env python3
"""
Test the resource optimization API endpoints
"""

import httpx
import json

API_BASE_URL = "http://localhost:8006"

def test_water_optimization_endpoint():
    """Test the water optimization endpoint"""
    print("Testing water optimization endpoint...")
    
    # Create a valid request
    request_data = {
        "farmer_id": "test_farmer_water",
        "farm_location": {
            "latitude": 25.0,
            "longitude": 80.0,
            "address": "Water Test Farm"
        },
        "irrigation_type": "canal",
        "planning_season": "kharif",
        "farm_constraints": {
            "total_area_acres": 10.0,
            "available_water_acre_feet": 15.0,
            "budget_limit": 300000,
            "labor_availability": "moderate"
        }
    }
    
    try:
        # Test the water optimization endpoint
        response = httpx.post(
            f"{API_BASE_URL}/optimize/water",
            json=request_data,
            params={"drought_probability": 0.3},
            timeout=30.0
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Water optimization successful!")
            print(f"  - Crops selected: {result['optimization_summary']['crops_selected']}")
            print(f"  - Water stress index: {result['water_stress_index']:.3f}")
            print(f"  - Total water requirement: {result['total_water_requirement_mm']:.0f}mm")
            return True
        else:
            print(f"❌ Water optimization failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing water optimization: {str(e)}")
        return False

def test_drought_resistant_endpoint():
    """Test the drought-resistant prioritization endpoint"""
    print("\nTesting drought-resistant prioritization endpoint...")
    
    request_data = {
        "farmer_id": "test_farmer_drought",
        "farm_location": {
            "latitude": 25.0,
            "longitude": 80.0,
            "address": "Drought Test Farm"
        },
        "irrigation_type": "rainfed",
        "planning_season": "kharif",
        "farm_constraints": {
            "total_area_acres": 8.0,
            "available_water_acre_feet": 10.0
        }
    }
    
    try:
        response = httpx.post(
            f"{API_BASE_URL}/optimize/drought-resistant",
            json=request_data,
            params={
                "drought_risk_level": "high",
                "water_scarcity_factor": 0.7
            },
            timeout=30.0
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Drought resistance prioritization successful!")
            print(f"  - Recommendations: {len(result['prioritized_recommendations'])}")
            print(f"  - Drought risk level: {result['drought_risk_level']}")
            
            # Show top drought-resistant crops
            for i, crop in enumerate(result['drought_resistant_crops'][:3]):
                print(f"  - {i+1}. {crop['crop_name']}: Drought resistance {crop['drought_resistance']:.2f}")
            
            return True
        else:
            print(f"❌ Drought resistance prioritization failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing drought resistance: {str(e)}")
        return False

def test_resource_optimization_endpoint():
    """Test the resource optimization endpoint"""
    print("\nTesting resource optimization endpoint...")
    
    request_data = {
        "farmer_id": "test_farmer_resource",
        "farm_location": {
            "latitude": 25.0,
            "longitude": 80.0,
            "address": "Resource Test Farm"
        },
        "irrigation_type": "drip",
        "planning_season": "rabi",
        "farm_constraints": {
            "total_area_acres": 12.0,
            "available_water_acre_feet": 25.0,
            "budget_limit": 400000,
            "labor_availability": "limited",
            "machinery_access": ["tractor", "harvester"]
        }
    }
    
    try:
        response = httpx.post(
            f"{API_BASE_URL}/optimize/resources?optimization_objectives=profit_maximization&optimization_objectives=resource_efficiency",
            json=request_data,
            timeout=30.0
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Resource optimization successful!")
            print(f"  - Crops selected: {result['optimization_summary']['crops_selected']}")
            if result['resource_metrics']['roi_percentage'] != 0:
                print(f"  - ROI: {result['resource_metrics']['roi_percentage']:.1f}%")
                print(f"  - Area utilization: {result['resource_metrics']['area_utilization']:.1f}%")
                print(f"  - Profit per acre: ${result['resource_metrics']['profit_per_acre']:.0f}")
            else:
                print("  - No crops selected (likely due to missing analysis data)")
            return True
        else:
            print(f"❌ Resource optimization failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing resource optimization: {str(e)}")
        return False

def test_conservation_recommendations_endpoint():
    """Test the conservation recommendations endpoint"""
    print("\nTesting conservation recommendations endpoint...")
    
    try:
        response = httpx.get(
            f"{API_BASE_URL}/optimize/conservation-recommendations",
            params={
                "total_area_acres": 10.0,
                "available_water_acre_feet": 12.0,
                "drought_probability": 0.6
            },
            timeout=15.0
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Conservation recommendations successful!")
            print(f"  - Recommendations: {len(result['conservation_recommendations'])}")
            print(f"  - Water per acre: {result['water_per_acre']:.1f} acre-feet")
            
            for i, rec in enumerate(result['conservation_recommendations'][:3]):
                print(f"  - {i+1}. {rec}")
            
            return True
        else:
            print(f"❌ Conservation recommendations failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing conservation recommendations: {str(e)}")
        return False

def main():
    """Run all API endpoint tests"""
    print("Testing Resource Optimization API Endpoints")
    print("=" * 50)
    
    try:
        # Test all endpoints
        results = []
        results.append(test_water_optimization_endpoint())
        results.append(test_drought_resistant_endpoint())
        results.append(test_resource_optimization_endpoint())
        results.append(test_conservation_recommendations_endpoint())
        
        success_count = sum(results)
        total_count = len(results)
        
        print("\n" + "=" * 50)
        if success_count == total_count:
            print("✅ All API endpoint tests passed!")
            print("Resource optimization API is working correctly.")
            return True
        else:
            print(f"❌ {total_count - success_count} out of {total_count} tests failed.")
            return False
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)