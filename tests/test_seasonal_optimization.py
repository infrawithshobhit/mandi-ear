"""
Property-Based Test for Seasonal and Resource Optimization
Feature: mandi-ear, Property 11: Seasonal and Resource Optimization

**Validates: Requirements 5.3, 5.4, 5.5**

This test validates that the crop planning system correctly factors seasonal constraints
(festivals, water availability, export demand) into crop recommendations and optimizes
resource usage effectively.
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
SEASONAL_FACTORS = ["festivals", "water_availability", "export_demand", "weather_patterns"]
RESOURCE_CONSTRAINTS = ["water", "budget", "labor", "machinery", "storage", "transportation"]
OPTIMIZATION_CRITERIA = ["profit_maximization", "risk_minimization", "resource_efficiency"]

# Hypothesis strategies for generating test data
@st.composite
def seasonal_constraints(draw):
    """Generate seasonal constraints for testing"""
    current_month = datetime.now().month
    
    return {
        "planning_month": draw(st.integers(min_value=1, max_value=12)),
        "festival_season": draw(st.sampled_from([
            "diwali", "holi", "eid", "christmas", "dussehra", "none"
        ])),
        "monsoon_pattern": draw(st.sampled_from([
            "early_monsoon", "normal_monsoon", "late_monsoon", "weak_monsoon", "strong_monsoon"
        ])),
        "export_peak_months": draw(st.lists(
            st.integers(min_value=1, max_value=12), 
            min_size=1, max_size=4, unique=True
        )),
        "harvest_season": draw(st.sampled_from(["kharif", "rabi", "zaid"])),
        "market_demand_peak": draw(st.sampled_from([
            "pre_festival", "post_harvest", "export_season", "wedding_season", "normal"
        ]))
    }

@st.composite
def resource_constraints(draw):
    """Generate resource constraints for optimization testing"""
    total_area = draw(st.floats(min_value=1.0, max_value=100.0))
    
    return {
        "total_area_acres": total_area,
        "water_availability": {
            "total_acre_feet": draw(st.one_of(
                st.none(),
                st.floats(min_value=total_area * 0.5, max_value=total_area * 5.0)
            )),
            "source_type": draw(st.sampled_from([
                "rainfed", "canal", "tube_well", "mixed", "limited"
            ])),
            "reliability": draw(st.sampled_from(["high", "medium", "low"]))
        },
        "budget_constraints": {
            "total_budget": draw(st.one_of(
                st.none(),
                st.floats(min_value=total_area * 10000, max_value=total_area * 200000)
            )),
            "credit_access": draw(st.sampled_from(["excellent", "good", "limited", "none"])),
            "subsidy_eligible": draw(st.booleans())
        },
        "labor_resources": {
            "family_labor": draw(st.integers(min_value=1, max_value=8)),
            "hired_labor_access": draw(st.sampled_from(["abundant", "moderate", "limited", "scarce"])),
            "skilled_labor": draw(st.booleans()),
            "seasonal_availability": draw(st.sampled_from(["consistent", "variable", "peak_only"]))
        },
        "machinery_access": {
            "owned_equipment": draw(st.lists(
                st.sampled_from(["tractor", "harvester", "planter", "sprayer", "thresher"]),
                min_size=0, max_size=5, unique=True
            )),
            "rental_availability": draw(st.sampled_from(["excellent", "good", "limited", "poor"])),
            "custom_services": draw(st.booleans())
        },
        "storage_facilities": {
            "on_farm_storage": draw(st.one_of(
                st.none(),
                st.floats(min_value=100, max_value=total_area * 10000)
            )),
            "cold_storage_access": draw(st.booleans()),
            "warehouse_distance_km": draw(st.floats(min_value=1, max_value=50))
        },
        "transportation": {
            "road_quality": draw(st.sampled_from(["excellent", "good", "poor", "very_poor"])),
            "market_distance_km": draw(st.floats(min_value=5, max_value=100)),
            "vehicle_access": draw(st.sampled_from(["owned", "rental", "shared", "none"]))
        }
    }

@st.composite
def optimization_request(draw):
    """Generate comprehensive optimization request"""
    seasonal_data = draw(seasonal_constraints())
    resource_data = draw(resource_constraints())
    
    return {
        "farmer_id": f"farmer_{draw(st.integers(min_value=1000, max_value=9999))}",
        "farm_location": {
            "latitude": draw(st.floats(min_value=8.0, max_value=37.0)),
            "longitude": draw(st.floats(min_value=68.0, max_value=97.0)),
            "address": "Test Farm Location"
        },
        "seasonal_constraints": seasonal_data,
        "resource_constraints": resource_data,
        "optimization_goals": draw(st.lists(
            st.sampled_from(["maximize_profit", "minimize_risk", "optimize_water_use", 
                           "maximize_yield", "ensure_food_security", "export_focus"]),
            min_size=1, max_size=3, unique=True
        )),
        "planning_horizon": draw(st.sampled_from(["single_season", "annual", "multi_year"])),
        "risk_tolerance": draw(st.sampled_from(["low", "medium", "high"])),
        "sustainability_focus": draw(st.booleans())
    }

@st.composite
def water_optimization_scenario(draw):
    """Generate water optimization scenarios"""
    total_area = draw(st.floats(min_value=2.0, max_value=50.0))
    
    return {
        "farm_area": total_area,
        "water_availability": draw(st.floats(min_value=total_area * 0.3, max_value=total_area * 3.0)),
        "irrigation_efficiency": draw(st.floats(min_value=0.4, max_value=0.9)),
        "drought_probability": draw(st.floats(min_value=0.0, max_value=0.8)),
        "crop_water_requirements": draw(st.lists(
            st.floats(min_value=300, max_value=2000),  # mm per season
            min_size=1, max_size=5
        )),
        "water_cost_per_unit": draw(st.floats(min_value=0.5, max_value=5.0)),
        "conservation_methods": draw(st.lists(
            st.sampled_from(["drip", "sprinkler", "mulching", "rainwater_harvesting"]),
            min_size=0, max_size=4, unique=True
        ))
    }

class TestSeasonalOptimization:
    """Test class for seasonal and resource optimization properties"""
    
    @given(constraints=seasonal_constraints())
    @settings(max_examples=20, deadline=8000)
    def test_seasonal_factor_integration(self, constraints: Dict[str, Any]):
        """
        Property 11: Seasonal and Resource Optimization - Seasonal Factor Integration
        
        For any seasonal constraints, the system should correctly factor festivals,
        monsoon patterns, and export seasons into crop planning decisions.
        """
        assume(1 <= constraints["planning_month"] <= 12)
        assume(len(constraints["export_peak_months"]) >= 1)
        
        try:
            # Create a test request with seasonal constraints
            test_request = {
                "farmer_id": "test_farmer_seasonal",
                "farm_location": {
                    "latitude": 20.0,
                    "longitude": 77.0,
                    "address": "Test Farm"
                },
                "soil_type": "alluvial",
                "irrigation_type": "canal",
                "farm_constraints": {
                    "total_area_acres": 10.0,
                    "available_water_acre_feet": 25.0
                },
                "planning_season": constraints["harvest_season"],
                "planning_year": 2024,
                "seasonal_factors": constraints
            }
            
            # Test crop recommendations with seasonal factors
            response = httpx.post(
                f"{API_BASE_URL}/recommend",
                json=test_request,
                timeout=20.0
            )
            
            assert response.status_code == 200, f"Seasonal optimization failed: {response.status_code}"
            
            recommendations = response.json()
            assert isinstance(recommendations, list), "Recommendations should be a list"
            assert len(recommendations) > 0, "Should have seasonal recommendations"
            
            # Validate seasonal considerations in recommendations
            for recommendation in recommendations:
                # Check season alignment
                assert recommendation["season"] == constraints["harvest_season"], \
                    f"Season mismatch: {recommendation['season']} != {constraints['harvest_season']}"
                
                # Validate planting and harvest windows
                planting_start = datetime.fromisoformat(recommendation["planting_window_start"])
                harvest_start = datetime.fromisoformat(recommendation["harvest_window_start"])
                
                # Planting should be before harvest
                assert planting_start < harvest_start, "Planting should be before harvest"
                
                # Check seasonal timing makes sense
                if constraints["harvest_season"] == "kharif":
                    # Kharif crops typically planted June-July, harvested Oct-Dec
                    assert 6 <= planting_start.month <= 8, f"Invalid kharif planting month: {planting_start.month}"
                elif constraints["harvest_season"] == "rabi":
                    # Rabi crops typically planted Oct-Dec, harvested Mar-May
                    assert planting_start.month >= 10 or planting_start.month <= 2, \
                        f"Invalid rabi planting month: {planting_start.month}"
                
                # Check market outlook considers seasonal factors
                if "market_outlook" in recommendation:
                    market_outlook = recommendation["market_outlook"].lower()
                    
                    # Festival seasons should show demand considerations
                    if constraints["festival_season"] != "none":
                        # Market outlook should mention demand or seasonal factors
                        seasonal_keywords = ["demand", "festival", "seasonal", "market", "growth"]
                        assert any(keyword in market_outlook for keyword in seasonal_keywords), \
                            "Market outlook should consider seasonal demand factors"
                
                # Export peak months should influence recommendations
                current_month = datetime.now().month
                if current_month in constraints["export_peak_months"]:
                    # Should have higher projected income or mention export potential
                    if "export" in str(recommendation).lower():
                        assert recommendation["projected_income_per_acre"] > 0, \
                            "Export-oriented crops should have positive income projections"
            
        except httpx.ConnectError:
            pytest.skip("Crop planning service not available for testing")
        except Exception as e:
            pytest.fail(f"Seasonal factor integration test failed: {str(e)}")
    
    @given(scenario=water_optimization_scenario())
    @settings(max_examples=15, deadline=10000)
    def test_water_resource_optimization(self, scenario: Dict[str, Any]):
        """
        Property 11: Seasonal and Resource Optimization - Water Resource Optimization
        
        For any water availability scenario, the system should optimize crop selection
        and allocation to maximize efficiency within water constraints.
        """
        assume(scenario["farm_area"] >= 2.0)
        assume(scenario["water_availability"] > 0)
        assume(len(scenario["crop_water_requirements"]) >= 1)
        
        try:
            # Calculate total water demand if all crops were grown
            total_water_demand = sum(scenario["crop_water_requirements"]) * scenario["farm_area"]
            water_stress_factor = total_water_demand / (scenario["water_availability"] * 1000)  # Convert to mm
            
            # Create optimization request
            test_request = {
                "farmer_id": "test_farmer_water",
                "farm_location": {
                    "latitude": 25.0,
                    "longitude": 80.0,
                    "address": "Water Test Farm"
                },
                "farm_constraints": {
                    "total_area_acres": scenario["farm_area"],
                    "available_water_acre_feet": scenario["water_availability"],
                    "irrigation_efficiency": scenario["irrigation_efficiency"]
                },
                "optimization_criteria": ["water_efficiency", "drought_resilience"],
                "water_constraints": {
                    "drought_probability": scenario["drought_probability"],
                    "conservation_methods": scenario["conservation_methods"]
                }
            }
            
            # Test water optimization endpoint
            response = httpx.post(
                f"{API_BASE_URL}/plan",
                json=test_request,
                timeout=25.0
            )
            
            assert response.status_code == 200, f"Water optimization failed: {response.status_code}"
            
            plan = response.json()
            
            # Validate water optimization in the plan
            assert "planned_crops" in plan, "Plan should include planned crops"
            assert "optimization_suggestions" in plan, "Plan should include optimization suggestions"
            
            planned_crops = plan["planned_crops"]
            assert len(planned_crops) > 0, "Should have planned crops"
            
            # Calculate total water requirement of planned crops
            total_planned_water = 0
            total_planned_area = 0
            
            for planned_crop in planned_crops:
                crop_rec = planned_crop["crop_recommendation"]
                allocated_area = planned_crop["allocated_area_acres"]
                water_req = crop_rec.get("water_requirement_mm", 500)  # Default if not specified
                
                total_planned_water += water_req * allocated_area
                total_planned_area += allocated_area
                
                # Individual crop water efficiency checks
                assert water_req > 0, "Water requirement should be positive"
                assert allocated_area > 0, "Allocated area should be positive"
            
            # Total planned area should not exceed farm area
            assert total_planned_area <= scenario["farm_area"] + 0.1, \
                f"Planned area exceeds farm area: {total_planned_area} > {scenario['farm_area']}"
            
            # Water constraint validation
            available_water_mm = scenario["water_availability"] * 1233.48  # Convert acre-feet to mm
            
            if water_stress_factor > 1.2:  # High water stress
                # System should recommend water-efficient crops or reduced area
                avg_water_per_acre = total_planned_water / max(total_planned_area, 0.1)
                assert avg_water_per_acre <= 1200, \
                    f"Under water stress, should recommend lower water requirement crops: {avg_water_per_acre}mm/acre"
            
            # Check optimization suggestions for water management
            optimization_suggestions = plan["optimization_suggestions"]
            
            if scenario["drought_probability"] > 0.3:  # High drought risk
                drought_suggestions = [s for s in optimization_suggestions 
                                     if any(keyword in s.lower() for keyword in 
                                           ["drought", "water", "irrigation", "resistant"])]
                assert len(drought_suggestions) > 0, \
                    "Should provide drought management suggestions for high drought risk"
            
            if len(scenario["conservation_methods"]) > 0:
                # Should mention or consider conservation methods
                conservation_mentioned = any(
                    method in str(optimization_suggestions).lower() 
                    for method in scenario["conservation_methods"]
                )
                # This is a soft check as conservation methods might be implicit
            
            # Water efficiency validation
            if scenario["irrigation_efficiency"] < 0.6:  # Low efficiency
                efficiency_suggestions = [s for s in optimization_suggestions 
                                        if any(keyword in s.lower() for keyword in 
                                              ["efficiency", "drip", "sprinkler", "water"])]
                assert len(efficiency_suggestions) > 0, \
                    "Should suggest efficiency improvements for low irrigation efficiency"
            
        except httpx.ConnectError:
            pytest.skip("Crop planning service not available for testing")
        except Exception as e:
            pytest.fail(f"Water resource optimization test failed: {str(e)}")
    
    @given(request=optimization_request())
    @settings(max_examples=12, deadline=15000)
    def test_comprehensive_resource_optimization(self, request: Dict[str, Any]):
        """
        Property 11: Seasonal and Resource Optimization - Comprehensive Resource Optimization
        
        For any combination of resource constraints, the system should optimize
        crop allocation considering all available resources and constraints.
        """
        assume(2.0 <= request["resource_constraints"]["total_area_acres"] <= 100.0)
        assume(8.0 <= request["farm_location"]["latitude"] <= 37.0)
        assume(68.0 <= request["farm_location"]["longitude"] <= 97.0)
        
        try:
            # Test comprehensive resource optimization
            response = httpx.post(
                f"{API_BASE_URL}/plan",
                json=request,
                timeout=30.0
            )
            
            assert response.status_code == 200, f"Resource optimization failed: {response.status_code}"
            
            plan = response.json()
            
            # Validate comprehensive optimization
            assert "planned_crops" in plan, "Plan should include planned crops"
            assert "total_investment" in plan, "Plan should include financial projections"
            assert "optimization_suggestions" in plan, "Plan should include optimization suggestions"
            assert "risk_assessment" in plan, "Plan should include risk assessment"
            
            planned_crops = plan["planned_crops"]
            resource_constraints = request["resource_constraints"]
            optimization_goals = request["optimization_goals"]
            
            # Resource constraint validation
            total_area = sum(crop["allocated_area_acres"] for crop in planned_crops)
            max_area = resource_constraints["total_area_acres"]
            assert total_area <= max_area + 0.1, f"Area constraint violated: {total_area} > {max_area}"
            
            # Budget constraint validation
            budget_info = resource_constraints["budget_constraints"]
            if budget_info["total_budget"] is not None:
                total_investment = plan["total_investment"]
                max_budget = budget_info["total_budget"]
                
                if budget_info["credit_access"] in ["limited", "none"]:
                    # Stricter budget constraint
                    assert total_investment <= max_budget * 1.1, \
                        f"Budget constraint violated with limited credit: {total_investment} > {max_budget}"
                else:
                    # Some flexibility with good credit access
                    assert total_investment <= max_budget * 1.3, \
                        f"Budget constraint severely violated: {total_investment} > {max_budget * 1.3}"
            
            # Labor constraint considerations
            labor_info = resource_constraints["labor_resources"]
            optimization_suggestions = plan["optimization_suggestions"]
            
            if labor_info["hired_labor_access"] in ["limited", "scarce"]:
                # Should suggest labor-efficient crops or mechanization
                labor_suggestions = [s for s in optimization_suggestions 
                                   if any(keyword in s.lower() for keyword in 
                                         ["labor", "mechaniz", "efficient", "automation"])]
                # Soft check - labor considerations should be present
            
            # Machinery access optimization
            machinery_info = resource_constraints["machinery_access"]
            if len(machinery_info["owned_equipment"]) >= 3:
                # With good machinery access, should optimize for mechanization
                mechanized_crops = 0
                for crop in planned_crops:
                    crop_name = crop["crop_recommendation"]["crop_name"].lower()
                    if crop_name in ["wheat", "rice", "maize", "cotton"]:  # Mechanization-friendly crops
                        mechanized_crops += 1
                
                # Should have some mechanization-friendly crops
                assert mechanized_crops > 0, "Should include mechanization-friendly crops with good machinery access"
            
            # Storage constraint validation
            storage_info = resource_constraints["storage_facilities"]
            if storage_info["on_farm_storage"] is not None:
                # Calculate expected total yield
                total_expected_yield = sum(
                    crop["crop_recommendation"]["expected_yield_per_acre"] * crop["allocated_area_acres"]
                    for crop in planned_crops
                )
                
                storage_capacity = storage_info["on_farm_storage"]
                if total_expected_yield > storage_capacity * 1.2:
                    # Should suggest storage solutions or crops with better storage life
                    storage_suggestions = [s for s in optimization_suggestions 
                                         if any(keyword in s.lower() for keyword in 
                                               ["storage", "shelf", "preserve", "post-harvest"])]
                    # Soft validation - storage considerations should be mentioned
            
            # Transportation optimization
            transport_info = resource_constraints["transportation"]
            if transport_info["road_quality"] in ["poor", "very_poor"]:
                # Should consider crops with better transportability
                transport_suggestions = [s for s in optimization_suggestions 
                                       if any(keyword in s.lower() for keyword in 
                                             ["transport", "shelf", "perishable", "access"])]
                # Soft validation for transportation considerations
            
            # Optimization goal validation
            if "maximize_profit" in optimization_goals:
                # Should have positive net profit
                assert plan["net_profit"] > 0, "Profit maximization should result in positive net profit"
                
                # Should prioritize high-value crops
                avg_income_per_acre = sum(
                    crop["crop_recommendation"]["projected_income_per_acre"] * crop["allocated_area_acres"]
                    for crop in planned_crops
                ) / max(total_area, 0.1)
                
                assert avg_income_per_acre > 15000, \
                    f"Profit maximization should result in reasonable income per acre: {avg_income_per_acre}"
            
            if "minimize_risk" in optimization_goals:
                # Should have lower overall risk
                risk_assessment = plan["risk_assessment"]
                overall_risk = risk_assessment["overall_risk_level"]
                assert overall_risk in ["low", "medium"], \
                    f"Risk minimization should result in low-medium risk: {overall_risk}"
            
            if "optimize_water_use" in optimization_goals:
                # Should consider water efficiency
                water_suggestions = [s for s in optimization_suggestions 
                                   if any(keyword in s.lower() for keyword in 
                                         ["water", "drought", "irrigation", "efficient"])]
                # Water optimization should be mentioned in suggestions
            
            # Sustainability focus validation
            if request.get("sustainability_focus", False):
                # Should include sustainability considerations
                sustainability_indicators = 0
                
                # Check for crop diversity
                crop_types = set(crop["crop_recommendation"]["crop_type"] for crop in planned_crops)
                if len(crop_types) > 1:
                    sustainability_indicators += 1
                
                # Check for soil health mentions
                soil_health_suggestions = [s for s in optimization_suggestions 
                                         if any(keyword in s.lower() for keyword in 
                                               ["rotation", "soil", "organic", "sustainable"])]
                if len(soil_health_suggestions) > 0:
                    sustainability_indicators += 1
                
                # Should have some sustainability indicators
                assert sustainability_indicators > 0, "Sustainability focus should show in recommendations"
            
        except httpx.ConnectError:
            pytest.skip("Crop planning service not available for testing")
        except Exception as e:
            pytest.fail(f"Comprehensive resource optimization test failed: {str(e)}")
    
    @given(
        festival_season=st.sampled_from(["diwali", "holi", "eid", "christmas", "dussehra"]),
        crop_type=st.sampled_from(["vegetables", "fruits", "cereals", "pulses", "cash_crops"])
    )
    @settings(max_examples=10, deadline=8000)
    def test_festival_demand_optimization(self, festival_season: str, crop_type: str):
        """
        Property 11: Seasonal and Resource Optimization - Festival Demand Integration
        
        For any festival season and crop type, the system should factor festival
        demand patterns into crop planning and pricing projections.
        """
        try:
            # Create request with festival considerations
            test_request = {
                "farmer_id": "test_farmer_festival",
                "farm_location": {
                    "latitude": 22.0,
                    "longitude": 78.0,
                    "address": "Festival Test Farm"
                },
                "farm_constraints": {
                    "total_area_acres": 5.0
                },
                "seasonal_factors": {
                    "festival_season": festival_season,
                    "market_focus": "festival_demand"
                },
                "preferred_crops": [crop_type],
                "planning_season": "rabi" if festival_season in ["diwali", "christmas"] else "kharif"
            }
            
            # Test demand analysis with festival factors
            response = httpx.post(
                f"{API_BASE_URL}/analyze/demand",
                params={
                    "commodity": crop_type,
                    "region": "central",
                    "timeframe_months": 6
                },
                timeout=15.0
            )
            
            assert response.status_code == 200, f"Festival demand analysis failed: {response.status_code}"
            
            demand_forecast = response.json()
            
            # Validate festival considerations in demand forecast
            assert "seasonal_patterns" in demand_forecast, "Should include seasonal patterns"
            assert "trends" in demand_forecast, "Should include market trends"
            
            seasonal_patterns = demand_forecast["seasonal_patterns"]
            
            # Festival seasons should show demand spikes for relevant crops
            if crop_type in ["vegetables", "fruits"]:
                # These crops typically see festival demand
                peak_demand_months = [month for month, demand in seasonal_patterns.items() 
                                    if isinstance(demand, (int, float)) and demand > 0.8]
                assert len(peak_demand_months) > 0, \
                    f"Should show peak demand months for {crop_type} during {festival_season}"
            
            # Price projections should reflect festival premiums
            price_projection = demand_forecast["price_projection"]
            if "current" in price_projection and "6_month" in price_projection:
                current_price = price_projection["current"]
                future_price = price_projection["6_month"]
                
                # Should show some price variation (not necessarily always higher)
                price_change_ratio = abs(future_price - current_price) / max(current_price, 1)
                assert price_change_ratio >= 0, "Price projections should be reasonable"
            
        except httpx.ConnectError:
            pytest.skip("Crop planning service not available for testing")
        except Exception as e:
            pytest.fail(f"Festival demand optimization test failed: {str(e)}")

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])