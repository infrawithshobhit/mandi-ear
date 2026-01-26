"""
Property-Based Test for Crop Planning Comprehensiveness
Feature: mandi-ear, Property 10: Crop Planning Comprehensiveness

**Validates: Requirements 5.1, 5.2**

This test validates that the Crop Planning Engine analyzes all required data sources 
(weather, soil, demand, historical trends) and provides complete recommendations 
with income projections and risk assessments.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
import asyncio
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

# Test configuration
API_BASE_URL = "http://localhost:8006"  # Crop planning service port
REQUIRED_ANALYSIS_SOURCES = ["weather", "soil", "demand", "historical_trends"]
MIN_RECOMMENDATION_FIELDS = [
    "crop_name", "variety", "season", "expected_yield_per_acre", 
    "projected_income_per_acre", "production_costs", "risk_level"
]
MIN_INCOME_PROJECTION_FIELDS = ["total_investment", "projected_revenue", "net_profit", "roi_percentage"]
MIN_RISK_ASSESSMENT_FIELDS = ["overall_risk_level", "risk_factors", "weather_risks", "market_risks"]

# Hypothesis strategies for generating test data
@st.composite
def farm_location(draw):
    """Generate valid farm location coordinates within India"""
    # India's approximate bounding box
    latitude = draw(st.floats(min_value=8.0, max_value=37.0))
    longitude = draw(st.floats(min_value=68.0, max_value=97.0))
    
    return {
        "latitude": latitude,
        "longitude": longitude,
        "address": f"Test Farm at {latitude:.2f}, {longitude:.2f}"
    }

@st.composite
def farm_constraints(draw):
    """Generate realistic farm constraints"""
    total_area = draw(st.floats(min_value=0.5, max_value=50.0))  # 0.5 to 50 acres
    
    return {
        "total_area_acres": total_area,
        "available_water_acre_feet": draw(st.one_of(
            st.none(),
            st.floats(min_value=1.0, max_value=total_area * 3.0)
        )),
        "budget_limit": draw(st.one_of(
            st.none(),
            st.floats(min_value=10000.0, max_value=total_area * 100000.0)
        )),
        "labor_availability": draw(st.one_of(
            st.none(),
            st.sampled_from(["limited", "moderate", "abundant"])
        )),
        "machinery_access": draw(st.one_of(
            st.none(),
            st.lists(st.sampled_from(["tractor", "harvester", "planter", "sprayer"]), min_size=0, max_size=4)
        )),
        "storage_capacity": draw(st.one_of(
            st.none(),
            st.floats(min_value=100.0, max_value=total_area * 5000.0)
        )),
        "transportation_access": draw(st.one_of(
            st.none(),
            st.sampled_from(["poor", "moderate", "good", "excellent"])
        ))
    }

@st.composite
def crop_planning_request(draw):
    """Generate comprehensive crop planning request"""
    location = draw(farm_location())
    constraints = draw(farm_constraints())
    
    return {
        "farmer_id": f"farmer_{draw(st.integers(min_value=1000, max_value=9999))}",
        "farm_location": location,
        "soil_type": draw(st.one_of(
            st.none(),
            st.sampled_from(["alluvial", "black", "red", "laterite", "desert", "mountain", "saline"])
        )),
        "irrigation_type": draw(st.sampled_from(["rainfed", "canal", "tube_well", "drip", "sprinkler"])),
        "farm_constraints": constraints,
        "preferred_crops": draw(st.one_of(
            st.none(),
            st.lists(st.sampled_from(["rice", "wheat", "cotton", "maize", "sugarcane", "pulses", "vegetables"]), 
                    min_size=1, max_size=3)
        )),
        "risk_tolerance": draw(st.sampled_from(["low", "medium", "high"])),
        "planning_season": draw(st.sampled_from(["kharif", "rabi", "zaid"])),
        "planning_year": draw(st.integers(min_value=2024, max_value=2026))
    }

@st.composite
def weather_analysis_params(draw):
    """Generate parameters for weather analysis testing"""
    location = draw(farm_location())
    
    return {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "timeframe_months": draw(st.integers(min_value=3, max_value=12))
    }

@st.composite
def soil_analysis_params(draw):
    """Generate parameters for soil analysis testing"""
    location = draw(farm_location())
    
    return {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "soil_type": draw(st.one_of(
            st.none(),
            st.sampled_from(["alluvial", "black", "red", "laterite", "desert", "mountain", "saline"])
        ))
    }

@st.composite
def demand_analysis_params(draw):
    """Generate parameters for demand analysis testing"""
    return {
        "commodity": draw(st.sampled_from(["rice", "wheat", "cotton", "maize", "sugarcane", "pulses", "vegetables"])),
        "region": draw(st.sampled_from(["north", "south", "east", "west", "central", "maharashtra", "punjab", "tamil nadu"])),
        "timeframe_months": draw(st.integers(min_value=6, max_value=18))
    }

class TestCropPlanningComprehensiveness:
    """Test class for crop planning comprehensiveness properties"""
    
    @given(params=weather_analysis_params())
    @settings(max_examples=15, deadline=10000)
    def test_weather_analysis_completeness(self, params: Dict[str, Any]):
        """
        Property 10: Crop Planning Comprehensiveness - Weather Analysis
        
        For any valid location and timeframe, the weather analysis should provide
        complete weather data including patterns, risks, and planting windows.
        """
        assume(8.0 <= params["latitude"] <= 37.0)  # Within India
        assume(68.0 <= params["longitude"] <= 97.0)
        assume(params["timeframe_months"] >= 3)
        
        try:
            # Test weather analysis endpoint
            response = httpx.post(
                f"{API_BASE_URL}/analyze/weather",
                params={
                    "latitude": params["latitude"],
                    "longitude": params["longitude"],
                    "timeframe_months": params["timeframe_months"]
                },
                timeout=15.0
            )
            
            assert response.status_code == 200, f"Weather analysis failed: {response.status_code}"
            
            result = response.json()
            
            # Validate required fields for comprehensive weather analysis
            required_fields = [
                "location", "analysis_period", "patterns", "rainfall_total",
                "temperature_range", "drought_risk", "flood_risk", 
                "optimal_planting_windows", "weather_suitability_score"
            ]
            
            for field in required_fields:
                assert field in result, f"Missing required weather analysis field: {field}"
            
            # Validate location data
            location = result["location"]
            assert "latitude" in location and "longitude" in location
            assert abs(location["latitude"] - params["latitude"]) < 0.1
            assert abs(location["longitude"] - params["longitude"]) < 0.1
            
            # Validate weather patterns
            patterns = result["patterns"]
            assert isinstance(patterns, list), "Weather patterns should be a list"
            assert len(patterns) > 0, "Weather patterns should not be empty"
            
            for pattern in patterns:
                pattern_fields = ["temperature_avg", "temperature_min", "temperature_max", 
                                "rainfall_mm", "humidity_percent", "wind_speed_kmh", "month"]
                for field in pattern_fields:
                    assert field in pattern, f"Missing pattern field: {field}"
                
                # Validate reasonable ranges
                assert -10 <= pattern["temperature_avg"] <= 50, f"Invalid avg temperature: {pattern['temperature_avg']}"
                assert pattern["temperature_min"] <= pattern["temperature_avg"] <= pattern["temperature_max"]
                assert 0 <= pattern["rainfall_mm"] <= 1000, f"Invalid rainfall: {pattern['rainfall_mm']}"
                assert 0 <= pattern["humidity_percent"] <= 100, f"Invalid humidity: {pattern['humidity_percent']}"
                assert 0 <= pattern["wind_speed_kmh"] <= 200, f"Invalid wind speed: {pattern['wind_speed_kmh']}"
                assert 1 <= pattern["month"] <= 12, f"Invalid month: {pattern['month']}"
            
            # Validate temperature range
            temp_range = result["temperature_range"]
            assert "average" in temp_range and "minimum" in temp_range and "maximum" in temp_range
            assert temp_range["minimum"] <= temp_range["average"] <= temp_range["maximum"]
            
            # Validate risk levels
            valid_risk_levels = ["low", "medium", "high", "very_high"]
            assert result["drought_risk"] in valid_risk_levels, f"Invalid drought risk: {result['drought_risk']}"
            assert result["flood_risk"] in valid_risk_levels, f"Invalid flood risk: {result['flood_risk']}"
            
            # Validate suitability score
            suitability = result["weather_suitability_score"]
            assert 0.0 <= suitability <= 1.0, f"Invalid suitability score: {suitability}"
            
            # Validate planting windows
            planting_windows = result["optimal_planting_windows"]
            assert isinstance(planting_windows, list), "Planting windows should be a list"
            
            for window in planting_windows:
                window_fields = ["season", "month", "suitability", "recommended_crops"]
                for field in window_fields:
                    assert field in window, f"Missing planting window field: {field}"
                
                assert window["season"] in ["kharif", "rabi", "zaid"], f"Invalid season: {window['season']}"
                assert 1 <= window["month"] <= 12, f"Invalid month: {window['month']}"
                assert window["suitability"] in ["low", "medium", "high"], f"Invalid suitability: {window['suitability']}"
                assert isinstance(window["recommended_crops"], list), "Recommended crops should be a list"
            
        except httpx.ConnectError:
            pytest.skip("Crop planning service not available for testing")
        except Exception as e:
            pytest.fail(f"Weather analysis completeness test failed: {str(e)}")
    
    @given(params=soil_analysis_params())
    @settings(max_examples=15, deadline=10000)
    def test_soil_analysis_completeness(self, params: Dict[str, Any]):
        """
        Property 10: Crop Planning Comprehensiveness - Soil Analysis
        
        For any valid location, the soil analysis should provide complete
        soil assessment including properties, suitable crops, and improvement recommendations.
        """
        assume(8.0 <= params["latitude"] <= 37.0)
        assume(68.0 <= params["longitude"] <= 97.0)
        
        try:
            # Test soil analysis endpoint
            request_params = {
                "latitude": params["latitude"],
                "longitude": params["longitude"]
            }
            if params["soil_type"]:
                request_params["soil_type"] = params["soil_type"]
            
            response = httpx.post(
                f"{API_BASE_URL}/analyze/soil",
                params=request_params,
                timeout=15.0
            )
            
            assert response.status_code == 200, f"Soil analysis failed: {response.status_code}"
            
            result = response.json()
            
            # Validate required fields for comprehensive soil analysis
            required_fields = [
                "location", "soil_type", "properties", "suitable_crops",
                "improvement_recommendations", "fertility_score", "water_retention_score"
            ]
            
            for field in required_fields:
                assert field in result, f"Missing required soil analysis field: {field}"
            
            # Validate location data
            location = result["location"]
            assert abs(location["latitude"] - params["latitude"]) < 0.1
            assert abs(location["longitude"] - params["longitude"]) < 0.1
            
            # Validate soil type
            valid_soil_types = ["alluvial", "black", "red", "laterite", "desert", "mountain", "saline"]
            assert result["soil_type"] in valid_soil_types, f"Invalid soil type: {result['soil_type']}"
            
            # Validate soil properties
            properties = result["properties"]
            property_fields = [
                "ph_level", "organic_matter_percent", "nitrogen_level", 
                "phosphorus_level", "potassium_level", "drainage", "water_holding_capacity"
            ]
            
            for field in property_fields:
                assert field in properties, f"Missing soil property field: {field}"
            
            # Validate property ranges
            assert 3.0 <= properties["ph_level"] <= 10.0, f"Invalid pH level: {properties['ph_level']}"
            assert 0.0 <= properties["organic_matter_percent"] <= 10.0, f"Invalid organic matter: {properties['organic_matter_percent']}"
            
            valid_nutrient_levels = ["low", "medium", "high"]
            assert properties["nitrogen_level"] in valid_nutrient_levels
            assert properties["phosphorus_level"] in valid_nutrient_levels
            assert properties["potassium_level"] in valid_nutrient_levels
            
            valid_drainage = ["poor", "moderate", "good", "excellent"]
            assert properties["drainage"] in valid_drainage
            
            valid_water_capacity = ["low", "medium", "high"]
            assert properties["water_holding_capacity"] in valid_water_capacity
            
            # Validate suitable crops
            suitable_crops = result["suitable_crops"]
            assert isinstance(suitable_crops, list), "Suitable crops should be a list"
            assert len(suitable_crops) > 0, "Should have at least one suitable crop"
            
            for crop in suitable_crops:
                assert isinstance(crop, str), "Crop names should be strings"
                assert len(crop.strip()) > 0, "Crop names should not be empty"
            
            # Validate improvement recommendations
            improvements = result["improvement_recommendations"]
            assert isinstance(improvements, list), "Improvement recommendations should be a list"
            
            for recommendation in improvements:
                assert isinstance(recommendation, str), "Recommendations should be strings"
                assert len(recommendation.strip()) > 0, "Recommendations should not be empty"
            
            # Validate scores
            fertility_score = result["fertility_score"]
            water_retention_score = result["water_retention_score"]
            
            assert 0.0 <= fertility_score <= 1.0, f"Invalid fertility score: {fertility_score}"
            assert 0.0 <= water_retention_score <= 1.0, f"Invalid water retention score: {water_retention_score}"
            
        except httpx.ConnectError:
            pytest.skip("Crop planning service not available for testing")
        except Exception as e:
            pytest.fail(f"Soil analysis completeness test failed: {str(e)}")
    
    @given(params=demand_analysis_params())
    @settings(max_examples=15, deadline=10000)
    def test_demand_analysis_completeness(self, params: Dict[str, Any]):
        """
        Property 10: Crop Planning Comprehensiveness - Demand Analysis
        
        For any commodity and region, the demand analysis should provide complete
        market forecast including trends, seasonal patterns, and export opportunities.
        """
        assume(params["timeframe_months"] >= 6)
        
        try:
            # Test demand analysis endpoint
            response = httpx.post(
                f"{API_BASE_URL}/analyze/demand",
                params={
                    "commodity": params["commodity"],
                    "region": params["region"],
                    "timeframe_months": params["timeframe_months"]
                },
                timeout=15.0
            )
            
            assert response.status_code == 200, f"Demand analysis failed: {response.status_code}"
            
            result = response.json()
            
            # Validate required fields for comprehensive demand analysis
            required_fields = [
                "commodity", "region", "forecast_period", "trends",
                "seasonal_patterns", "export_opportunities", "price_projection", "demand_growth_rate"
            ]
            
            for field in required_fields:
                assert field in result, f"Missing required demand analysis field: {field}"
            
            # Validate basic fields
            assert result["commodity"] == params["commodity"]
            assert result["region"] == params["region"]
            assert params["timeframe_months"] * 30 in result["forecast_period"] or str(params["timeframe_months"]) in result["forecast_period"]
            
            # Validate market trends
            trends = result["trends"]
            assert isinstance(trends, list), "Market trends should be a list"
            assert len(trends) > 0, "Should have market trend data"
            
            for trend in trends:
                trend_fields = ["month", "price_avg", "demand_index", "supply_index", "export_demand"]
                for field in trend_fields:
                    assert field in trend, f"Missing trend field: {field}"
                
                assert 1 <= trend["month"] <= 12, f"Invalid month: {trend['month']}"
                assert trend["price_avg"] > 0, f"Invalid price: {trend['price_avg']}"
                assert trend["demand_index"] >= 0, f"Invalid demand index: {trend['demand_index']}"
                assert trend["supply_index"] >= 0, f"Invalid supply index: {trend['supply_index']}"
                assert 0 <= trend["export_demand"] <= 1, f"Invalid export demand: {trend['export_demand']}"
            
            # Validate seasonal patterns
            seasonal_patterns = result["seasonal_patterns"]
            assert isinstance(seasonal_patterns, dict), "Seasonal patterns should be a dictionary"
            assert len(seasonal_patterns) > 0, "Should have seasonal pattern data"
            
            for pattern_key, pattern_value in seasonal_patterns.items():
                assert isinstance(pattern_key, str), "Pattern keys should be strings"
                assert isinstance(pattern_value, (int, float)), "Pattern values should be numeric"
                assert 0 <= pattern_value <= 2, f"Invalid pattern value: {pattern_value}"
            
            # Validate export opportunities
            export_opportunities = result["export_opportunities"]
            assert isinstance(export_opportunities, list), "Export opportunities should be a list"
            
            for opportunity in export_opportunities:
                opp_fields = ["market", "potential_volume", "peak_months", "estimated_premium"]
                for field in opp_fields:
                    assert field in opportunity, f"Missing export opportunity field: {field}"
                
                assert isinstance(opportunity["market"], str), "Market should be string"
                assert isinstance(opportunity["potential_volume"], str), "Potential volume should be string"
                assert isinstance(opportunity["peak_months"], list), "Peak months should be list"
                assert isinstance(opportunity["estimated_premium"], str), "Premium should be string"
                
                # Validate peak months
                for month in opportunity["peak_months"]:
                    assert 1 <= month <= 12, f"Invalid peak month: {month}"
            
            # Validate price projection
            price_projection = result["price_projection"]
            assert isinstance(price_projection, dict), "Price projection should be a dictionary"
            
            projection_periods = ["current", "3_month", "6_month", "12_month"]
            for period in projection_periods:
                if period in price_projection:
                    assert price_projection[period] > 0, f"Invalid price projection for {period}: {price_projection[period]}"
            
            # Validate demand growth rate
            growth_rate = result["demand_growth_rate"]
            assert isinstance(growth_rate, (int, float)), "Growth rate should be numeric"
            assert -1.0 <= growth_rate <= 2.0, f"Invalid growth rate: {growth_rate}"
            
        except httpx.ConnectError:
            pytest.skip("Crop planning service not available for testing")
        except Exception as e:
            pytest.fail(f"Demand analysis completeness test failed: {str(e)}")
    
    @given(request=crop_planning_request())
    @settings(max_examples=10, deadline=20000)
    def test_comprehensive_crop_recommendations(self, request: Dict[str, Any]):
        """
        Property 10: Crop Planning Comprehensiveness - Complete Recommendations
        
        For any valid crop planning request, the system should provide comprehensive
        recommendations with all required analysis components and complete data.
        """
        assume(0.5 <= request["farm_constraints"]["total_area_acres"] <= 50.0)
        assume(8.0 <= request["farm_location"]["latitude"] <= 37.0)
        assume(68.0 <= request["farm_location"]["longitude"] <= 97.0)
        
        try:
            # Test comprehensive crop recommendations endpoint
            response = httpx.post(
                f"{API_BASE_URL}/recommend",
                json=request,
                timeout=30.0
            )
            
            assert response.status_code == 200, f"Crop recommendations failed: {response.status_code}"
            
            result = response.json()
            
            # Should return a list of recommendations
            assert isinstance(result, list), "Recommendations should be a list"
            assert len(result) > 0, "Should have at least one crop recommendation"
            
            # Validate each recommendation
            for recommendation in result:
                # Check all required fields are present
                for field in MIN_RECOMMENDATION_FIELDS:
                    assert field in recommendation, f"Missing recommendation field: {field}"
                
                # Validate field types and ranges
                assert isinstance(recommendation["crop_name"], str), "Crop name should be string"
                assert len(recommendation["crop_name"].strip()) > 0, "Crop name should not be empty"
                
                assert isinstance(recommendation["variety"], str), "Variety should be string"
                assert len(recommendation["variety"].strip()) > 0, "Variety should not be empty"
                
                assert recommendation["season"] in ["kharif", "rabi", "zaid"], f"Invalid season: {recommendation['season']}"
                
                # Validate numeric fields
                assert recommendation["expected_yield_per_acre"] > 0, "Expected yield should be positive"
                assert recommendation["projected_income_per_acre"] > 0, "Projected income should be positive"
                
                # Validate production costs
                costs = recommendation["production_costs"]
                cost_fields = ["seeds", "fertilizers", "pesticides", "irrigation", "labor", "machinery", "other", "total"]
                for field in cost_fields:
                    assert field in costs, f"Missing cost field: {field}"
                    assert costs[field] >= 0, f"Cost should be non-negative: {field} = {costs[field]}"
                
                # Total should be sum of components
                expected_total = sum(costs[field] for field in cost_fields[:-1])  # Exclude 'total'
                assert abs(costs["total"] - expected_total) < 1.0, "Cost total mismatch"
                
                # Validate risk level
                valid_risk_levels = ["low", "medium", "high", "very_high"]
                assert recommendation["risk_level"] in valid_risk_levels, f"Invalid risk level: {recommendation['risk_level']}"
                
                # Validate optional fields if present
                if "suitability_score" in recommendation:
                    score = recommendation["suitability_score"]
                    assert 0.0 <= score <= 1.0, f"Invalid suitability score: {score}"
                
                if "confidence_level" in recommendation:
                    confidence = recommendation["confidence_level"]
                    assert 0.0 <= confidence <= 1.0, f"Invalid confidence level: {confidence}"
                
                if "water_requirement_mm" in recommendation:
                    water_req = recommendation["water_requirement_mm"]
                    assert water_req > 0, f"Invalid water requirement: {water_req}"
                
                if "risk_factors" in recommendation:
                    risk_factors = recommendation["risk_factors"]
                    assert isinstance(risk_factors, list), "Risk factors should be a list"
                    for factor in risk_factors:
                        assert isinstance(factor, str), "Risk factors should be strings"
                        assert len(factor.strip()) > 0, "Risk factors should not be empty"
            
            # Validate recommendations are sorted by suitability (if suitability_score present)
            if all("suitability_score" in rec for rec in result):
                scores = [rec["suitability_score"] for rec in result]
                assert scores == sorted(scores, reverse=True), "Recommendations should be sorted by suitability score"
            
        except httpx.ConnectError:
            pytest.skip("Crop planning service not available for testing")
        except Exception as e:
            pytest.fail(f"Comprehensive crop recommendations test failed: {str(e)}")
    
    @given(request=crop_planning_request())
    @settings(max_examples=8, deadline=25000)
    def test_comprehensive_crop_plan_creation(self, request: Dict[str, Any]):
        """
        Property 10: Crop Planning Comprehensiveness - Complete Plan Creation
        
        For any valid crop planning request, the system should create a comprehensive
        crop plan with all analysis components, financial projections, and risk assessments.
        """
        assume(0.5 <= request["farm_constraints"]["total_area_acres"] <= 50.0)
        assume(8.0 <= request["farm_location"]["latitude"] <= 37.0)
        assume(68.0 <= request["farm_location"]["longitude"] <= 97.0)
        
        try:
            # Test comprehensive crop plan creation endpoint
            response = httpx.post(
                f"{API_BASE_URL}/plan",
                json=request,
                timeout=40.0
            )
            
            assert response.status_code == 200, f"Crop plan creation failed: {response.status_code}"
            
            result = response.json()
            
            # Validate plan structure
            plan_fields = [
                "plan_id", "farmer_id", "farm_location", "planning_season", "planning_year",
                "weather_analysis", "soil_assessment", "planned_crops", 
                "total_investment", "projected_revenue", "net_profit", "roi_percentage",
                "risk_assessment", "optimization_suggestions", "plan_confidence"
            ]
            
            for field in plan_fields:
                assert field in result, f"Missing plan field: {field}"
            
            # Validate basic plan information
            assert result["farmer_id"] == request["farmer_id"]
            assert result["planning_season"] == request["planning_season"]
            assert result["planning_year"] == request["planning_year"]
            
            # Validate weather analysis completeness
            weather_analysis = result["weather_analysis"]
            weather_fields = ["location", "patterns", "rainfall_total", "temperature_range", 
                            "drought_risk", "flood_risk", "weather_suitability_score"]
            for field in weather_fields:
                assert field in weather_analysis, f"Missing weather analysis field: {field}"
            
            # Validate soil assessment completeness
            soil_assessment = result["soil_assessment"]
            soil_fields = ["location", "soil_type", "properties", "suitable_crops", 
                          "fertility_score", "water_retention_score"]
            for field in soil_fields:
                assert field in soil_assessment, f"Missing soil assessment field: {field}"
            
            # Validate planned crops
            planned_crops = result["planned_crops"]
            assert isinstance(planned_crops, list), "Planned crops should be a list"
            assert len(planned_crops) > 0, "Should have at least one planned crop"
            
            total_allocated_area = 0
            for planned_crop in planned_crops:
                crop_fields = ["crop_recommendation", "allocated_area_acres", 
                              "total_investment", "projected_revenue", "net_profit"]
                for field in crop_fields:
                    assert field in planned_crop, f"Missing planned crop field: {field}"
                
                assert planned_crop["allocated_area_acres"] > 0, "Allocated area should be positive"
                total_allocated_area += planned_crop["allocated_area_acres"]
                
                # Validate crop recommendation within planned crop
                crop_rec = planned_crop["crop_recommendation"]
                for field in MIN_RECOMMENDATION_FIELDS:
                    assert field in crop_rec, f"Missing crop recommendation field: {field}"
            
            # Total allocated area should not exceed farm area
            farm_area = request["farm_constraints"]["total_area_acres"]
            assert total_allocated_area <= farm_area + 0.1, f"Allocated area exceeds farm area: {total_allocated_area} > {farm_area}"
            
            # Validate financial projections
            for field in MIN_INCOME_PROJECTION_FIELDS:
                assert field in result, f"Missing income projection field: {field}"
                assert isinstance(result[field], (int, float)), f"Financial field should be numeric: {field}"
            
            assert result["total_investment"] >= 0, "Total investment should be non-negative"
            assert result["projected_revenue"] >= 0, "Projected revenue should be non-negative"
            
            # Net profit should equal revenue minus investment
            expected_net_profit = result["projected_revenue"] - result["total_investment"]
            assert abs(result["net_profit"] - expected_net_profit) < 1.0, "Net profit calculation error"
            
            # ROI calculation
            if result["total_investment"] > 0:
                expected_roi = (result["net_profit"] / result["total_investment"]) * 100
                assert abs(result["roi_percentage"] - expected_roi) < 0.1, "ROI calculation error"
            
            # Validate risk assessment completeness
            risk_assessment = result["risk_assessment"]
            for field in MIN_RISK_ASSESSMENT_FIELDS:
                assert field in risk_assessment, f"Missing risk assessment field: {field}"
            
            assert risk_assessment["overall_risk_level"] in ["low", "medium", "high", "very_high"]
            
            # Validate optimization suggestions
            optimization_suggestions = result["optimization_suggestions"]
            assert isinstance(optimization_suggestions, list), "Optimization suggestions should be a list"
            
            for suggestion in optimization_suggestions:
                assert isinstance(suggestion, str), "Suggestions should be strings"
                assert len(suggestion.strip()) > 0, "Suggestions should not be empty"
            
            # Validate plan confidence
            plan_confidence = result["plan_confidence"]
            assert 0.0 <= plan_confidence <= 1.0, f"Invalid plan confidence: {plan_confidence}"
            
        except httpx.ConnectError:
            pytest.skip("Crop planning service not available for testing")
        except Exception as e:
            pytest.fail(f"Comprehensive crop plan creation test failed: {str(e)}")

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])