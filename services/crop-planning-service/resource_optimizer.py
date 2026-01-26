"""
Resource Constraint Optimization Module

Implements advanced algorithms for optimizing crop allocation under various
resource constraints including water availability, drought resistance,
and resource usage optimization.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import math

from models import (
    CropPlanningRequest, CropRecommendation, PlannedCrop,
    FarmConstraints, RiskLevel, CropType, Season
)

logger = logging.getLogger(__name__)

class ResourceOptimizer:
    """
    Advanced resource constraint optimization for crop planning
    
    Provides:
    - Water availability optimization
    - Drought-resistant crop prioritization
    - Resource usage optimization algorithms
    - Multi-objective optimization
    """
    
    def __init__(self):
        # Drought resistance ratings for crops (0-1 scale)
        self.drought_resistance = {
            "rice": 0.2,
            "wheat": 0.6,
            "cotton": 0.4,
            "maize": 0.5,
            "sugarcane": 0.1,
            "pulses": 0.8,
            "millets": 0.9,
            "sorghum": 0.9,
            "pearl_millet": 0.95,
            "finger_millet": 0.85,
            "vegetables": 0.3,
            "fruits": 0.4,
            "oilseeds": 0.7,
            "groundnut": 0.6,
            "sunflower": 0.7,
            "mustard": 0.8,
            "safflower": 0.85
        }
        
        # Water use efficiency ratings (yield per unit water)
        self.water_efficiency = {
            "rice": 0.3,
            "wheat": 0.7,
            "cotton": 0.5,
            "maize": 0.6,
            "sugarcane": 0.2,
            "pulses": 0.9,
            "millets": 0.95,
            "sorghum": 0.9,
            "vegetables": 0.4,
            "fruits": 0.5,
            "oilseeds": 0.8
        }
        
        # Resource intensity ratings (0-1 scale, higher = more intensive)
        self.resource_intensity = {
            "labor": {
                "rice": 0.8,
                "wheat": 0.6,
                "cotton": 0.9,
                "vegetables": 0.95,
                "fruits": 0.9,
                "sugarcane": 0.85,
                "pulses": 0.4,
                "millets": 0.3
            },
            "capital": {
                "rice": 0.7,
                "wheat": 0.6,
                "cotton": 0.8,
                "vegetables": 0.9,
                "fruits": 0.95,
                "sugarcane": 0.9,
                "pulses": 0.4,
                "millets": 0.3
            },
            "machinery": {
                "rice": 0.8,
                "wheat": 0.9,
                "cotton": 0.7,
                "vegetables": 0.5,
                "fruits": 0.6,
                "sugarcane": 0.8,
                "pulses": 0.6,
                "millets": 0.5
            }
        }
    
    def optimize_water_allocation(
        self,
        recommendations: List[CropRecommendation],
        farm_constraints: FarmConstraints,
        drought_probability: float = 0.0
    ) -> List[PlannedCrop]:
        """
        Optimize crop allocation based on water availability constraints
        
        Args:
            recommendations: Available crop recommendations
            farm_constraints: Farm resource constraints
            drought_probability: Probability of drought (0-1)
            
        Returns:
            Optimized list of planned crops
        """
        try:
            if not recommendations:
                return []
            
            available_water = farm_constraints.available_water_acre_feet or 0
            total_area = farm_constraints.total_area_acres
            
            # Convert water from acre-feet to mm for calculations
            available_water_mm = available_water * 1233.48  # 1 acre-foot = 1233.48 mm
            
            # Filter and score crops based on water constraints
            water_scored_crops = self._score_crops_for_water_optimization(
                recommendations, drought_probability
            )
            
            # Apply water allocation algorithm
            planned_crops = self._allocate_crops_with_water_constraints(
                water_scored_crops, total_area, available_water_mm
            )
            
            return planned_crops
            
        except Exception as e:
            logger.error(f"Water allocation optimization failed: {str(e)}")
            return []
    
    def prioritize_drought_resistant_crops(
        self,
        recommendations: List[CropRecommendation],
        drought_risk_level: RiskLevel,
        water_scarcity_factor: float = 0.0
    ) -> List[CropRecommendation]:
        """
        Prioritize drought-resistant crops based on risk assessment
        
        Args:
            recommendations: Available crop recommendations
            drought_risk_level: Assessed drought risk level
            water_scarcity_factor: Water scarcity factor (0-1)
            
        Returns:
            Reordered recommendations prioritizing drought resistance
        """
        try:
            if not recommendations:
                return []
            
            # Calculate drought resistance scores for each crop
            scored_recommendations = []
            
            for recommendation in recommendations:
                crop_name = recommendation.crop_name.lower()
                
                # Get base drought resistance
                drought_resistance = self.drought_resistance.get(crop_name, 0.5)
                
                # Get water efficiency
                water_efficiency = self.water_efficiency.get(crop_name, 0.5)
                
                # Calculate drought priority score
                drought_score = self._calculate_drought_priority_score(
                    recommendation, drought_resistance, water_efficiency,
                    drought_risk_level, water_scarcity_factor
                )
                
                scored_recommendations.append((recommendation, drought_score))
            
            # Sort by drought priority score (higher is better)
            scored_recommendations.sort(key=lambda x: x[1], reverse=True)
            
            # Return reordered recommendations
            return [rec for rec, score in scored_recommendations]
            
        except Exception as e:
            logger.error(f"Drought resistance prioritization failed: {str(e)}")
            return recommendations
    
    def optimize_resource_usage(
        self,
        recommendations: List[CropRecommendation],
        farm_constraints: FarmConstraints,
        optimization_objectives: List[str] = None
    ) -> List[PlannedCrop]:
        """
        Optimize resource usage across multiple constraints
        
        Args:
            recommendations: Available crop recommendations
            farm_constraints: Farm resource constraints
            optimization_objectives: List of optimization objectives
            
        Returns:
            Optimized list of planned crops
        """
        try:
            if not recommendations:
                return []
            
            if optimization_objectives is None:
                optimization_objectives = ["profit_maximization", "resource_efficiency"]
            
            # Multi-objective optimization
            optimized_crops = self._multi_objective_optimization(
                recommendations, farm_constraints, optimization_objectives
            )
            
            return optimized_crops
            
        except Exception as e:
            logger.error(f"Resource usage optimization failed: {str(e)}")
            return []
    
    def _score_crops_for_water_optimization(
        self,
        recommendations: List[CropRecommendation],
        drought_probability: float
    ) -> List[Tuple[CropRecommendation, float]]:
        """Score crops for water optimization"""
        
        scored_crops = []
        
        for recommendation in recommendations:
            crop_name = recommendation.crop_name.lower()
            
            # Base water efficiency score
            water_efficiency = self.water_efficiency.get(crop_name, 0.5)
            
            # Drought resistance factor
            drought_resistance = self.drought_resistance.get(crop_name, 0.5)
            
            # Water requirement penalty (lower is better)
            water_req_normalized = min(recommendation.water_requirement_mm / 2000.0, 1.0)
            water_req_score = 1.0 - water_req_normalized
            
            # Profitability per unit water
            water_productivity = (
                recommendation.net_profit_per_acre / 
                max(recommendation.water_requirement_mm, 100)
            )
            water_productivity_normalized = min(water_productivity / 50.0, 1.0)
            
            # Combine scores with drought probability weighting
            drought_weight = 0.3 + (drought_probability * 0.4)  # 0.3 to 0.7
            efficiency_weight = 0.25
            requirement_weight = 0.25
            productivity_weight = 0.2
            
            total_score = (
                drought_resistance * drought_weight +
                water_efficiency * efficiency_weight +
                water_req_score * requirement_weight +
                water_productivity_normalized * productivity_weight
            )
            
            scored_crops.append((recommendation, total_score))
        
        return scored_crops
    
    def _allocate_crops_with_water_constraints(
        self,
        scored_crops: List[Tuple[CropRecommendation, float]],
        total_area: float,
        available_water_mm: float
    ) -> List[PlannedCrop]:
        """Allocate crops considering water constraints"""
        
        # Sort by water optimization score
        scored_crops.sort(key=lambda x: x[1], reverse=True)
        
        planned_crops = []
        remaining_area = total_area
        remaining_water = available_water_mm
        
        for recommendation, score in scored_crops:
            if remaining_area <= 0.1 or remaining_water <= 0:
                break
            
            # Calculate maximum area possible with water constraint
            water_per_acre = recommendation.water_requirement_mm
            max_area_by_water = remaining_water / water_per_acre if water_per_acre > 0 else remaining_area
            
            # Allocate area (limited by both area and water)
            allocated_area = min(remaining_area, max_area_by_water, remaining_area * 0.6)
            
            if allocated_area > 0.1:  # Minimum viable area
                water_used = allocated_area * water_per_acre
                
                # Create planned crop
                total_investment = recommendation.production_costs.total * allocated_area
                projected_revenue = recommendation.projected_income_per_acre * allocated_area
                net_profit = projected_revenue - total_investment
                
                planned_crop = PlannedCrop(
                    crop_recommendation=recommendation,
                    allocated_area_acres=allocated_area,
                    total_investment=total_investment,
                    projected_revenue=projected_revenue,
                    net_profit=net_profit
                )
                
                planned_crops.append(planned_crop)
                remaining_area -= allocated_area
                remaining_water -= water_used
        
        return planned_crops
    
    def _calculate_drought_priority_score(
        self,
        recommendation: CropRecommendation,
        drought_resistance: float,
        water_efficiency: float,
        drought_risk_level: RiskLevel,
        water_scarcity_factor: float
    ) -> float:
        """Calculate drought priority score for a crop"""
        
        # Base score from drought resistance and water efficiency
        base_score = (drought_resistance * 0.6) + (water_efficiency * 0.4)
        
        # Risk level multiplier
        risk_multipliers = {
            RiskLevel.LOW: 1.0,
            RiskLevel.MEDIUM: 1.2,
            RiskLevel.HIGH: 1.5,
            RiskLevel.VERY_HIGH: 2.0
        }
        risk_multiplier = risk_multipliers.get(drought_risk_level, 1.0)
        
        # Water scarcity adjustment
        scarcity_bonus = water_scarcity_factor * 0.3
        
        # Profitability consideration (don't sacrifice too much profit)
        profit_factor = min(recommendation.net_profit_per_acre / 30000.0, 1.0)
        
        # Final score
        final_score = (base_score * risk_multiplier + scarcity_bonus) * (0.7 + profit_factor * 0.3)
        
        return final_score
    
    def _multi_objective_optimization(
        self,
        recommendations: List[CropRecommendation],
        farm_constraints: FarmConstraints,
        objectives: List[str]
    ) -> List[PlannedCrop]:
        """Multi-objective optimization algorithm"""
        
        # Score each crop for each objective
        crop_scores = {}
        
        for recommendation in recommendations:
            crop_name = recommendation.crop_name
            scores = {}
            
            # Profit maximization score
            if "profit_maximization" in objectives:
                scores["profit"] = min(recommendation.net_profit_per_acre / 50000.0, 1.0)
            
            # Resource efficiency score
            if "resource_efficiency" in objectives:
                scores["efficiency"] = self._calculate_resource_efficiency_score(
                    recommendation, farm_constraints
                )
            
            # Risk minimization score
            if "risk_minimization" in objectives:
                risk_scores = {
                    RiskLevel.LOW: 1.0,
                    RiskLevel.MEDIUM: 0.7,
                    RiskLevel.HIGH: 0.4,
                    RiskLevel.VERY_HIGH: 0.1
                }
                scores["risk"] = risk_scores.get(recommendation.risk_level, 0.5)
            
            # Water optimization score
            if "water_optimization" in objectives:
                crop_name_lower = recommendation.crop_name.lower()
                water_efficiency = self.water_efficiency.get(crop_name_lower, 0.5)
                water_req_score = 1.0 - min(recommendation.water_requirement_mm / 2000.0, 1.0)
                scores["water"] = (water_efficiency + water_req_score) / 2.0
            
            # Yield maximization score
            if "yield_maximization" in objectives:
                scores["yield"] = min(recommendation.expected_yield_per_acre / 5000.0, 1.0)
            
            crop_scores[crop_name] = scores
        
        # Combine scores with equal weighting
        combined_scores = []
        for recommendation in recommendations:
            crop_name = recommendation.crop_name
            scores = crop_scores[crop_name]
            
            if scores:
                combined_score = sum(scores.values()) / len(scores)
                combined_scores.append((recommendation, combined_score))
        
        # Sort by combined score
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Allocate area using knapsack-like algorithm
        return self._knapsack_allocation(combined_scores, farm_constraints)
    
    def _calculate_resource_efficiency_score(
        self,
        recommendation: CropRecommendation,
        farm_constraints: FarmConstraints
    ) -> float:
        """Calculate resource efficiency score"""
        
        crop_name = recommendation.crop_name.lower()
        efficiency_scores = []
        
        # Labor efficiency
        if farm_constraints.labor_availability:
            labor_intensity = self.resource_intensity["labor"].get(crop_name, 0.5)
            if farm_constraints.labor_availability == "limited":
                efficiency_scores.append(1.0 - labor_intensity)
            else:
                efficiency_scores.append(0.7 + labor_intensity * 0.3)
        
        # Capital efficiency
        if farm_constraints.budget_limit:
            capital_intensity = self.resource_intensity["capital"].get(crop_name, 0.5)
            roi = recommendation.net_profit_per_acre / max(recommendation.production_costs.total, 1)
            capital_efficiency = min(roi / 2.0, 1.0) * (1.0 - capital_intensity * 0.3)
            efficiency_scores.append(capital_efficiency)
        
        # Machinery efficiency
        if farm_constraints.machinery_access:
            machinery_intensity = self.resource_intensity["machinery"].get(crop_name, 0.5)
            owned_machinery = len(farm_constraints.machinery_access)
            if owned_machinery >= 3:
                efficiency_scores.append(0.7 + machinery_intensity * 0.3)
            else:
                efficiency_scores.append(1.0 - machinery_intensity * 0.5)
        
        # Water efficiency
        water_efficiency = self.water_efficiency.get(crop_name, 0.5)
        efficiency_scores.append(water_efficiency)
        
        return statistics.mean(efficiency_scores) if efficiency_scores else 0.5
    
    def _knapsack_allocation(
        self,
        scored_crops: List[Tuple[CropRecommendation, float]],
        farm_constraints: FarmConstraints
    ) -> List[PlannedCrop]:
        """Knapsack-like allocation algorithm"""
        
        planned_crops = []
        remaining_area = farm_constraints.total_area_acres
        remaining_budget = farm_constraints.budget_limit or float('inf')
        
        # Sort by score (already sorted)
        for recommendation, score in scored_crops[:5]:  # Limit to top 5 crops
            if remaining_area <= 0.1:
                break
            
            # Calculate optimal allocation for this crop
            cost_per_acre = recommendation.production_costs.total
            max_area_by_budget = remaining_budget / cost_per_acre if cost_per_acre > 0 else remaining_area
            
            # Allocate area (consider diminishing returns)
            if len(planned_crops) == 0:
                allocated_area = min(remaining_area * 0.5, max_area_by_budget)
            elif len(planned_crops) == 1:
                allocated_area = min(remaining_area * 0.6, max_area_by_budget)
            else:
                allocated_area = min(remaining_area, max_area_by_budget)
            
            if allocated_area > 0.1:
                total_investment = cost_per_acre * allocated_area
                projected_revenue = recommendation.projected_income_per_acre * allocated_area
                net_profit = projected_revenue - total_investment
                
                planned_crop = PlannedCrop(
                    crop_recommendation=recommendation,
                    allocated_area_acres=allocated_area,
                    total_investment=total_investment,
                    projected_revenue=projected_revenue,
                    net_profit=net_profit
                )
                
                planned_crops.append(planned_crop)
                remaining_area -= allocated_area
                remaining_budget -= total_investment
        
        return planned_crops
    
    def get_water_conservation_recommendations(
        self,
        farm_constraints: FarmConstraints,
        drought_probability: float
    ) -> List[str]:
        """Get water conservation recommendations"""
        
        recommendations = []
        
        # Basic water conservation
        recommendations.append("Implement mulching to reduce water evaporation")
        recommendations.append("Use drip irrigation for water-efficient crop watering")
        
        # Drought-specific recommendations
        if drought_probability > 0.3:
            recommendations.append("Install rainwater harvesting systems")
            recommendations.append("Consider drought-resistant crop varieties")
            recommendations.append("Implement soil moisture conservation techniques")
        
        if drought_probability > 0.6:
            recommendations.append("Reduce crop area to conserve water resources")
            recommendations.append("Focus on high-value, low-water crops")
            recommendations.append("Consider deficit irrigation strategies")
        
        # Water source specific
        if farm_constraints.available_water_acre_feet:
            if farm_constraints.available_water_acre_feet < farm_constraints.total_area_acres * 2:
                recommendations.append("Water availability is limited - prioritize water-efficient crops")
                recommendations.append("Consider supplemental irrigation only for high-value crops")
        
        return recommendations
    
    def calculate_water_stress_index(
        self,
        planned_crops: List[PlannedCrop],
        available_water: float,
        drought_probability: float = 0.0
    ) -> float:
        """Calculate water stress index for the crop plan"""
        
        if not planned_crops or available_water <= 0:
            return 1.0  # Maximum stress
        
        # Calculate total water demand
        total_water_demand = sum(
            crop.crop_recommendation.water_requirement_mm * crop.allocated_area_acres
            for crop in planned_crops
        )
        
        # Convert available water from acre-feet to mm
        available_water_mm = available_water * 1233.48
        
        # Base stress ratio
        stress_ratio = total_water_demand / available_water_mm
        
        # Adjust for drought probability
        drought_adjusted_stress = stress_ratio * (1.0 + drought_probability * 0.5)
        
        # Normalize to 0-1 scale
        water_stress_index = min(drought_adjusted_stress, 1.0)
        
        return water_stress_index