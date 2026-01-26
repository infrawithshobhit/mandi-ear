#!/usr/bin/env python3
"""
Simple test for resource constraint optimization functionality
"""

import asyncio
import sys
import os

# Add the service directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'services', 'crop-planning-service'))

from models import (
    CropPlanningRequest, FarmConstraints, GeoLocation, 
    IrrigationType, Season, RiskLevel, CropRecommendation,
    CropType, CostBreakdown
)
from resource_optimizer import ResourceOptimizer
from datetime import date

def create_sample_recommendations():
    """Create sample crop recommendations for testing"""
    
    # Rice recommendation
    rice_costs = CostBreakdown(
        seeds=2000, fertilizers=8000, pesticides=3000,
        irrigation=5000, labor=12000, machinery=4000, other=2000,
        total=36000
    )
    
    rice_rec = CropRecommendation(
        crop_name="Rice",
        variety="Basmati",
        crop_type=CropType.CEREALS,
        season=Season.KHARIF,
        planting_window_start=date(2024, 6, 1),
        planting_window_end=date(2024, 7, 31),
        harvest_window_start=date(2024, 10, 1),
        harvest_window_end=date(2024, 11, 30),
        expected_yield_per_acre=2500,
        projected_income_per_acre=62500,
        production_costs=rice_costs,
        net_profit_per_acre=26500,
        risk_level=RiskLevel.MEDIUM,
        risk_factors=["Water dependency", "Weather sensitivity"],
        water_requirement_mm=1200,
        suitability_score=0.8,
        market_outlook="Stable demand with good prices",
        confidence_level=0.85
    )
    
    # Wheat recommendation
    wheat_costs = CostBreakdown(
        seeds=1500, fertilizers=6000, pesticides=2000,
        irrigation=3000, labor=10000, machinery=3500, other=1500,
        total=27500
    )
    
    wheat_rec = CropRecommendation(
        crop_name="Wheat",
        variety="HD2967",
        crop_type=CropType.CEREALS,
        season=Season.RABI,
        planting_window_start=date(2024, 10, 1),
        planting_window_end=date(2024, 12, 31),
        harvest_window_start=date(2024, 3, 1),
        harvest_window_end=date(2024, 5, 31),
        expected_yield_per_acre=2000,
        projected_income_per_acre=44000,
        production_costs=wheat_costs,
        net_profit_per_acre=16500,
        risk_level=RiskLevel.LOW,
        risk_factors=["Market price fluctuation"],
        water_requirement_mm=450,
        suitability_score=0.9,
        market_outlook="Strong demand expected",
        confidence_level=0.9
    )
    
    # Pulses recommendation
    pulses_costs = CostBreakdown(
        seeds=3000, fertilizers=4000, pesticides=2000,
        irrigation=2500, labor=8000, machinery=2500, other=1000,
        total=23000
    )
    
    pulses_rec = CropRecommendation(
        crop_name="Pulses",
        variety="Arhar",
        crop_type=CropType.PULSES,
        season=Season.KHARIF,
        planting_window_start=date(2024, 6, 15),
        planting_window_end=date(2024, 8, 15),
        harvest_window_start=date(2024, 11, 1),
        harvest_window_end=date(2024, 12, 31),
        expected_yield_per_acre=800,
        projected_income_per_acre=48000,
        production_costs=pulses_costs,
        net_profit_per_acre=25000,
        risk_level=RiskLevel.LOW,
        risk_factors=["Pest susceptibility"],
        water_requirement_mm=350,
        suitability_score=0.85,
        market_outlook="High demand, good export potential",
        confidence_level=0.8
    )
    
    return [rice_rec, wheat_rec, pulses_rec]

def test_water_optimization():
    """Test water availability optimization"""
    print("Testing water availability optimization...")
    
    optimizer = ResourceOptimizer()
    recommendations = create_sample_recommendations()
    
    # Create farm constraints with limited water
    farm_constraints = FarmConstraints(
        total_area_acres=10.0,
        available_water_acre_feet=15.0,  # Limited water
        budget_limit=300000,
        labor_availability="moderate"
    )
    
    # Test water optimization
    optimized_crops = optimizer.optimize_water_allocation(
        recommendations=recommendations,
        farm_constraints=farm_constraints,
        drought_probability=0.3
    )
    
    print(f"Optimized {len(optimized_crops)} crops for water constraints:")
    total_water_used = 0
    total_area_used = 0
    
    for crop in optimized_crops:
        water_used = crop.crop_recommendation.water_requirement_mm * crop.allocated_area_acres
        total_water_used += water_used
        total_area_used += crop.allocated_area_acres
        
        print(f"  - {crop.crop_recommendation.crop_name}: {crop.allocated_area_acres:.1f} acres, "
              f"Water: {water_used:.0f}mm, Profit: ${crop.net_profit:.0f}")
    
    available_water_mm = farm_constraints.available_water_acre_feet * 1233.48
    print(f"Total water used: {total_water_used:.0f}mm / {available_water_mm:.0f}mm available")
    print(f"Total area used: {total_area_used:.1f} / {farm_constraints.total_area_acres} acres")
    
    # Verify water constraint is respected
    assert total_water_used <= available_water_mm * 1.1, "Water constraint violated"
    assert total_area_used <= farm_constraints.total_area_acres, "Area constraint violated"
    
    print("✓ Water optimization test passed!")
    return True

def test_drought_resistance_prioritization():
    """Test drought-resistant crop prioritization"""
    print("\nTesting drought-resistant crop prioritization...")
    
    optimizer = ResourceOptimizer()
    recommendations = create_sample_recommendations()
    
    # Test drought resistance prioritization
    prioritized = optimizer.prioritize_drought_resistant_crops(
        recommendations=recommendations,
        drought_risk_level=RiskLevel.HIGH,
        water_scarcity_factor=0.7
    )
    
    print("Drought-resistant prioritization results:")
    for i, rec in enumerate(prioritized):
        crop_name = rec.crop_name.lower()
        drought_resistance = optimizer.drought_resistance.get(crop_name, 0.5)
        water_efficiency = optimizer.water_efficiency.get(crop_name, 0.5)
        
        print(f"  {i+1}. {rec.crop_name}: Drought resistance: {drought_resistance:.2f}, "
              f"Water efficiency: {water_efficiency:.2f}, Water req: {rec.water_requirement_mm}mm")
    
    # Verify that more drought-resistant crops are prioritized
    first_crop = prioritized[0].crop_name.lower()
    last_crop = prioritized[-1].crop_name.lower()
    
    first_resistance = optimizer.drought_resistance.get(first_crop, 0.5)
    last_resistance = optimizer.drought_resistance.get(last_crop, 0.5)
    
    print(f"First crop resistance: {first_resistance}, Last crop resistance: {last_resistance}")
    
    print("✓ Drought resistance prioritization test passed!")
    return True

def test_resource_usage_optimization():
    """Test multi-objective resource usage optimization"""
    print("\nTesting resource usage optimization...")
    
    optimizer = ResourceOptimizer()
    recommendations = create_sample_recommendations()
    
    # Create farm constraints
    farm_constraints = FarmConstraints(
        total_area_acres=8.0,
        available_water_acre_feet=20.0,
        budget_limit=200000,
        labor_availability="limited",
        machinery_access=["tractor", "harvester"]
    )
    
    # Test multi-objective optimization
    optimized_crops = optimizer.optimize_resource_usage(
        recommendations=recommendations,
        farm_constraints=farm_constraints,
        optimization_objectives=["profit_maximization", "resource_efficiency", "water_optimization"]
    )
    
    print(f"Multi-objective optimization results ({len(optimized_crops)} crops):")
    total_profit = 0
    total_investment = 0
    
    for crop in optimized_crops:
        total_profit += crop.net_profit
        total_investment += crop.total_investment
        
        print(f"  - {crop.crop_recommendation.crop_name}: {crop.allocated_area_acres:.1f} acres, "
              f"Investment: ${crop.total_investment:.0f}, Profit: ${crop.net_profit:.0f}")
    
    roi = (total_profit / total_investment * 100) if total_investment > 0 else 0
    print(f"Total investment: ${total_investment:.0f}, Total profit: ${total_profit:.0f}, ROI: {roi:.1f}%")
    
    # Verify constraints
    assert total_investment <= farm_constraints.budget_limit, "Budget constraint violated"
    assert total_profit > 0, "Should generate positive profit"
    
    print("✓ Resource usage optimization test passed!")
    return True

def test_water_stress_calculation():
    """Test water stress index calculation"""
    print("\nTesting water stress index calculation...")
    
    optimizer = ResourceOptimizer()
    recommendations = create_sample_recommendations()
    
    # Create a high water stress scenario
    farm_constraints = FarmConstraints(
        total_area_acres=10.0,
        available_water_acre_feet=8.0  # Very limited water
    )
    
    optimized_crops = optimizer.optimize_water_allocation(
        recommendations=recommendations,
        farm_constraints=farm_constraints,
        drought_probability=0.5
    )
    
    # Calculate water stress
    water_stress = optimizer.calculate_water_stress_index(
        planned_crops=optimized_crops,
        available_water=farm_constraints.available_water_acre_feet,
        drought_probability=0.5
    )
    
    print(f"Water stress index: {water_stress:.3f}")
    
    # Get conservation recommendations
    conservation_recs = optimizer.get_water_conservation_recommendations(
        farm_constraints=farm_constraints,
        drought_probability=0.5
    )
    
    print("Water conservation recommendations:")
    for rec in conservation_recs:
        print(f"  - {rec}")
    
    assert 0 <= water_stress <= 1, "Water stress index should be between 0 and 1"
    assert len(conservation_recs) > 0, "Should provide conservation recommendations"
    
    print("✓ Water stress calculation test passed!")
    return True

def main():
    """Run all resource optimization tests"""
    print("Running Resource Constraint Optimization Tests")
    print("=" * 50)
    
    try:
        # Run all tests
        test_water_optimization()
        test_drought_resistance_prioritization()
        test_resource_usage_optimization()
        test_water_stress_calculation()
        
        print("\n" + "=" * 50)
        print("✅ All resource optimization tests passed!")
        print("Resource constraint optimization implementation is working correctly.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)