"""
Recommendation Engine for Crop Planning

Combines weather, soil, and demand analysis to generate comprehensive
crop recommendations with income projections and risk assessments.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import uuid
import statistics

from models import (
    CropPlanningRequest, CropRecommendation, CropPlan, PlannedCrop,
    WeatherAnalysis, SoilAssessment, DemandForecast,
    CropType, Season, RiskLevel, RiskFactor, RiskAssessment,
    CostBreakdown
)
from demand_analyzer import DemandAnalyzer

logger = logging.getLogger(__name__)

class RecommendationEngine:
    """
    Comprehensive crop recommendation engine
    
    Combines multiple analysis factors to generate:
    - Crop recommendations with income projections
    - Risk assessments and mitigation strategies
    - Resource optimization suggestions
    - Complete crop plans
    """
    
    def __init__(self):
        self.demand_analyzer = DemandAnalyzer()
        
        # Crop database with characteristics
        self.crop_database = {
            "rice": {
                "type": CropType.CEREALS,
                "varieties": ["Basmati", "IR64", "Swarna", "Sona Masuri"],
                "growing_period_days": 120,
                "water_requirement_mm": 1200,
                "optimal_temp_range": (20, 35),
                "soil_ph_range": (5.5, 7.0),
                "yield_per_acre_kg": 2500,
                "base_price_per_kg": 25,
                "input_costs_per_acre": {
                    "seeds": 2000, "fertilizers": 8000, "pesticides": 3000,
                    "irrigation": 5000, "labor": 12000, "machinery": 4000, "other": 2000
                }
            },
            "wheat": {
                "type": CropType.CEREALS,
                "varieties": ["HD2967", "PBW343", "DBW17", "WH542"],
                "growing_period_days": 150,
                "water_requirement_mm": 450,
                "optimal_temp_range": (15, 25),
                "soil_ph_range": (6.0, 7.5),
                "yield_per_acre_kg": 2000,
                "base_price_per_kg": 22,
                "input_costs_per_acre": {
                    "seeds": 1500, "fertilizers": 6000, "pesticides": 2000,
                    "irrigation": 3000, "labor": 10000, "machinery": 3500, "other": 1500
                }
            },
            "cotton": {
                "type": CropType.CASH_CROPS,
                "varieties": ["Bt Cotton", "Desi Cotton", "American Cotton"],
                "growing_period_days": 180,
                "water_requirement_mm": 800,
                "optimal_temp_range": (21, 32),
                "soil_ph_range": (6.0, 8.0),
                "yield_per_acre_kg": 500,
                "base_price_per_kg": 55,
                "input_costs_per_acre": {
                    "seeds": 3000, "fertilizers": 10000, "pesticides": 8000,
                    "irrigation": 6000, "labor": 15000, "machinery": 5000, "other": 3000
                }
            },
            "maize": {
                "type": CropType.CEREALS,
                "varieties": ["Hybrid Maize", "Composite Maize", "Sweet Corn"],
                "growing_period_days": 100,
                "water_requirement_mm": 600,
                "optimal_temp_range": (18, 32),
                "soil_ph_range": (6.0, 7.5),
                "yield_per_acre_kg": 2200,
                "base_price_per_kg": 18,
                "input_costs_per_acre": {
                    "seeds": 2500, "fertilizers": 7000, "pesticides": 2500,
                    "irrigation": 4000, "labor": 8000, "machinery": 3000, "other": 1500
                }
            },
            "sugarcane": {
                "type": CropType.CASH_CROPS,
                "varieties": ["Co86032", "Co238", "Co0238", "Co775"],
                "growing_period_days": 365,
                "water_requirement_mm": 1800,
                "optimal_temp_range": (20, 35),
                "soil_ph_range": (6.5, 7.5),
                "yield_per_acre_kg": 50000,
                "base_price_per_kg": 3.5,
                "input_costs_per_acre": {
                    "seeds": 8000, "fertilizers": 15000, "pesticides": 5000,
                    "irrigation": 12000, "labor": 25000, "machinery": 8000, "other": 5000
                }
            },
            "pulses": {
                "type": CropType.PULSES,
                "varieties": ["Arhar", "Moong", "Chana", "Masoor"],
                "growing_period_days": 90,
                "water_requirement_mm": 350,
                "optimal_temp_range": (20, 30),
                "soil_ph_range": (6.0, 7.5),
                "yield_per_acre_kg": 800,
                "base_price_per_kg": 60,
                "input_costs_per_acre": {
                    "seeds": 3000, "fertilizers": 4000, "pesticides": 2000,
                    "irrigation": 2500, "labor": 8000, "machinery": 2500, "other": 1000
                }
            },
            "vegetables": {
                "type": CropType.VEGETABLES,
                "varieties": ["Tomato", "Onion", "Potato", "Cabbage"],
                "growing_period_days": 75,
                "water_requirement_mm": 400,
                "optimal_temp_range": (15, 30),
                "soil_ph_range": (6.0, 7.0),
                "yield_per_acre_kg": 8000,
                "base_price_per_kg": 12,
                "input_costs_per_acre": {
                    "seeds": 5000, "fertilizers": 8000, "pesticides": 6000,
                    "irrigation": 5000, "labor": 15000, "machinery": 3000, "other": 3000
                }
            }
        }
    
    async def generate_recommendations(
        self,
        request: CropPlanningRequest,
        weather_analysis: WeatherAnalysis,
        soil_assessment: SoilAssessment
    ) -> List[CropRecommendation]:
        """
        Generate comprehensive crop recommendations
        
        Args:
            request: Crop planning request
            weather_analysis: Weather analysis results
            soil_assessment: Soil assessment results
            
        Returns:
            List of crop recommendations
        """
        try:
            recommendations = []
            
            # Get suitable crops based on soil
            suitable_crops = soil_assessment.suitable_crops
            
            # Filter by preferred crops if specified
            if request.preferred_crops:
                suitable_crops = [crop for crop in suitable_crops 
                               if any(pref.lower() in crop.lower() for pref in request.preferred_crops)]
            
            # Generate recommendations for each suitable crop
            for crop_name in suitable_crops[:5]:  # Limit to top 5
                if crop_name.lower() in self.crop_database:
                    recommendation = await self._create_crop_recommendation(
                        crop_name.lower(),
                        request,
                        weather_analysis,
                        soil_assessment
                    )
                    if recommendation:
                        recommendations.append(recommendation)
            
            # Sort by suitability score
            recommendations.sort(key=lambda x: x.suitability_score, reverse=True)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Recommendation generation failed: {str(e)}")
            return []
    
    async def _create_crop_recommendation(
        self,
        crop_name: str,
        request: CropPlanningRequest,
        weather_analysis: WeatherAnalysis,
        soil_assessment: SoilAssessment
    ) -> Optional[CropRecommendation]:
        """Create individual crop recommendation"""
        
        try:
            crop_data = self.crop_database[crop_name]
            
            # Get demand forecast
            demand_forecast = await self.demand_analyzer.forecast_demand(
                commodity=crop_name,
                region=request.farm_location.address or "India",
                timeframe=timedelta(days=365)
            )
            
            # Calculate suitability score
            suitability_score = self._calculate_suitability_score(
                crop_data, weather_analysis, soil_assessment, demand_forecast
            )
            
            # Determine planting and harvest windows
            planting_window, harvest_window = self._determine_crop_windows(
                crop_data, request.planning_season, weather_analysis
            )
            
            # Calculate financial projections
            yield_per_acre, income_per_acre, costs, net_profit = self._calculate_financials(
                crop_data, suitability_score, demand_forecast, request.farm_constraints
            )
            
            # Assess risks
            risk_level, risk_factors = self._assess_crop_risks(
                crop_data, weather_analysis, soil_assessment, demand_forecast
            )
            
            # Select best variety
            variety = crop_data["varieties"][0]  # Default to first variety
            
            recommendation = CropRecommendation(
                crop_name=crop_name.title(),
                variety=variety,
                crop_type=crop_data["type"],
                season=request.planning_season,
                planting_window_start=planting_window[0],
                planting_window_end=planting_window[1],
                harvest_window_start=harvest_window[0],
                harvest_window_end=harvest_window[1],
                expected_yield_per_acre=yield_per_acre,
                projected_income_per_acre=income_per_acre,
                production_costs=costs,
                net_profit_per_acre=net_profit,
                risk_level=risk_level,
                risk_factors=risk_factors,
                water_requirement_mm=crop_data["water_requirement_mm"],
                suitability_score=suitability_score,
                market_outlook=self._generate_market_outlook(demand_forecast),
                confidence_level=min(suitability_score + 0.1, 1.0)
            )
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Failed to create recommendation for {crop_name}: {str(e)}")
            return None
    
    def _calculate_suitability_score(
        self,
        crop_data: Dict[str, Any],
        weather_analysis: WeatherAnalysis,
        soil_assessment: SoilAssessment,
        demand_forecast: DemandForecast
    ) -> float:
        """Calculate overall crop suitability score"""
        
        # Weather suitability
        weather_score = weather_analysis.weather_suitability_score
        
        # Soil suitability
        soil_score = soil_assessment.fertility_score
        
        # Temperature suitability
        temp_range = crop_data["optimal_temp_range"]
        avg_temp = weather_analysis.temperature_range["average"]
        if temp_range[0] <= avg_temp <= temp_range[1]:
            temp_score = 1.0
        elif temp_range[0] - 5 <= avg_temp <= temp_range[1] + 5:
            temp_score = 0.7
        else:
            temp_score = 0.3
        
        # pH suitability
        ph_range = crop_data["soil_ph_range"]
        soil_ph = soil_assessment.properties.ph_level
        if ph_range[0] <= soil_ph <= ph_range[1]:
            ph_score = 1.0
        elif ph_range[0] - 0.5 <= soil_ph <= ph_range[1] + 0.5:
            ph_score = 0.7
        else:
            ph_score = 0.3
        
        # Market demand score
        demand_score = min(demand_forecast.demand_growth_rate + 0.5, 1.0)
        
        # Weighted average
        overall_score = (
            weather_score * 0.25 +
            soil_score * 0.25 +
            temp_score * 0.2 +
            ph_score * 0.15 +
            demand_score * 0.15
        )
        
        return round(overall_score, 2)
    
    def _determine_crop_windows(
        self,
        crop_data: Dict[str, Any],
        season: Season,
        weather_analysis: WeatherAnalysis
    ) -> tuple:
        """Determine optimal planting and harvest windows"""
        
        current_year = datetime.now().year
        growing_days = crop_data["growing_period_days"]
        
        # Season-based planting windows
        if season == Season.KHARIF:
            planting_start = date(current_year, 6, 1)
            planting_end = date(current_year, 7, 31)
        elif season == Season.RABI:
            planting_start = date(current_year, 10, 1)
            planting_end = date(current_year, 12, 31)
        else:  # ZAID
            planting_start = date(current_year, 3, 1)
            planting_end = date(current_year, 5, 31)
        
        # Calculate harvest windows
        harvest_start = planting_start + timedelta(days=growing_days)
        harvest_end = planting_end + timedelta(days=growing_days)
        
        return (planting_start, planting_end), (harvest_start, harvest_end)
    
    def _calculate_financials(
        self,
        crop_data: Dict[str, Any],
        suitability_score: float,
        demand_forecast: DemandForecast,
        farm_constraints
    ) -> tuple:
        """Calculate comprehensive financial projections with market factors"""
        
        # Base yield adjusted by suitability
        base_yield = crop_data["yield_per_acre_kg"]
        expected_yield = base_yield * suitability_score
        
        # Price projection with seasonal and export considerations
        base_price = crop_data["base_price_per_kg"]
        
        # Use market forecast price (6-month projection)
        market_price = demand_forecast.price_projection.get("6_month", base_price)
        
        # Apply seasonal premium/discount
        current_month = datetime.now().month
        seasonal_multiplier = self._get_seasonal_price_multiplier(
            crop_data, current_month, demand_forecast.seasonal_patterns
        )
        
        # Apply export premium if applicable
        export_multiplier = self._get_export_price_multiplier(
            crop_data, demand_forecast.export_opportunities
        )
        
        # Final price calculation
        final_price = market_price * seasonal_multiplier * export_multiplier
        
        # Calculate income with quality bonus
        quality_bonus = self._calculate_quality_bonus(suitability_score)
        projected_income = expected_yield * final_price * (1 + quality_bonus)
        
        # Calculate costs with efficiency adjustments
        base_costs = crop_data["input_costs_per_acre"]
        
        # Adjust costs based on farm constraints
        cost_multipliers = self._get_cost_multipliers(farm_constraints)
        
        costs = CostBreakdown(
            seeds=base_costs["seeds"] * cost_multipliers["seeds"],
            fertilizers=base_costs["fertilizers"] * cost_multipliers["fertilizers"],
            pesticides=base_costs["pesticides"] * cost_multipliers["pesticides"],
            irrigation=base_costs["irrigation"] * cost_multipliers["irrigation"],
            labor=base_costs["labor"] * cost_multipliers["labor"],
            machinery=base_costs["machinery"] * cost_multipliers["machinery"],
            other=base_costs["other"] * cost_multipliers["other"],
            total=0  # Will be calculated below
        )
        
        # Calculate total costs
        costs.total = (costs.seeds + costs.fertilizers + costs.pesticides + 
                      costs.irrigation + costs.labor + costs.machinery + costs.other)
        
        # Net profit
        net_profit = projected_income - costs.total
        
        return expected_yield, projected_income, costs, net_profit
    
    def _get_seasonal_price_multiplier(
        self, 
        crop_data: Dict[str, Any], 
        current_month: int,
        seasonal_patterns: Dict[str, float]
    ) -> float:
        """Calculate seasonal price multiplier based on demand patterns"""
        
        # Get seasonal demand for current month
        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }
        
        current_month_name = month_names.get(current_month, "January")
        seasonal_demand = seasonal_patterns.get(current_month_name, 0.8)
        
        # Convert demand to price multiplier (higher demand = higher price)
        if seasonal_demand > 0.9:
            return 1.15  # 15% premium for peak season
        elif seasonal_demand > 0.7:
            return 1.05  # 5% premium for good season
        elif seasonal_demand < 0.5:
            return 0.90  # 10% discount for low season
        else:
            return 1.0   # Normal price
    
    def _get_export_price_multiplier(
        self, 
        crop_data: Dict[str, Any], 
        export_opportunities: List[Dict[str, Any]]
    ) -> float:
        """Calculate export price premium multiplier"""
        
        if not export_opportunities:
            return 1.0
        
        # Check if current month is in peak export season
        current_month = datetime.now().month
        
        for opportunity in export_opportunities:
            peak_months = opportunity.get("peak_months", [])
            if current_month in peak_months:
                # Extract premium percentage from string like "15.2%"
                premium_str = opportunity.get("estimated_premium", "0%")
                try:
                    premium_pct = float(premium_str.replace("%", ""))
                    return 1 + (premium_pct / 100)
                except:
                    return 1.10  # Default 10% export premium
        
        # Off-season export still gets some premium
        return 1.05  # 5% premium for export potential
    
    def _calculate_quality_bonus(self, suitability_score: float) -> float:
        """Calculate quality bonus based on suitability score"""
        
        if suitability_score > 0.9:
            return 0.10  # 10% bonus for excellent conditions
        elif suitability_score > 0.8:
            return 0.05  # 5% bonus for very good conditions
        elif suitability_score > 0.7:
            return 0.02  # 2% bonus for good conditions
        else:
            return 0.0   # No bonus for poor conditions
    
    def _get_cost_multipliers(self, farm_constraints) -> Dict[str, float]:
        """Get cost multipliers based on farm constraints"""
        
        multipliers = {
            "seeds": 1.0,
            "fertilizers": 1.0,
            "pesticides": 1.0,
            "irrigation": 1.0,
            "labor": 1.0,
            "machinery": 1.0,
            "other": 1.0
        }
        
        # Labor cost adjustments
        if farm_constraints.labor_availability == "limited":
            multipliers["labor"] = 1.3  # 30% higher labor costs
            multipliers["machinery"] = 0.9  # More mechanization reduces machinery rental costs
        elif farm_constraints.labor_availability == "abundant":
            multipliers["labor"] = 0.8  # 20% lower labor costs
        
        # Machinery access adjustments
        if farm_constraints.machinery_access:
            owned_machinery = len(farm_constraints.machinery_access)
            if owned_machinery >= 3:
                multipliers["machinery"] = 0.7  # 30% savings on machinery costs
            elif owned_machinery >= 1:
                multipliers["machinery"] = 0.85  # 15% savings
        
        # Transportation cost adjustments
        if farm_constraints.transportation_access == "poor":
            multipliers["other"] = 1.2  # 20% higher transportation costs
        elif farm_constraints.transportation_access == "excellent":
            multipliers["other"] = 0.9  # 10% lower transportation costs
        
        # Irrigation efficiency adjustments
        if hasattr(farm_constraints, 'irrigation_type'):
            # This would be passed from the request
            pass  # Irrigation type adjustments could be added here
        
        return multipliers
    
    def _assess_crop_risks(
        self,
        crop_data: Dict[str, Any],
        weather_analysis: WeatherAnalysis,
        soil_assessment: SoilAssessment,
        demand_forecast: DemandForecast
    ) -> tuple:
        """Comprehensive risk assessment for the crop"""
        
        risk_factors = []
        risk_scores = []
        
        # Weather risks
        if weather_analysis.drought_risk in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            risk_factors.append("High drought risk may significantly affect yield")
            risk_scores.append(0.8 if weather_analysis.drought_risk == RiskLevel.HIGH else 0.9)
        
        if weather_analysis.flood_risk in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]:
            risk_factors.append("High flood risk may damage crops and delay harvest")
            risk_scores.append(0.7 if weather_analysis.flood_risk == RiskLevel.HIGH else 0.85)
        
        # Temperature stress risks
        temp_range = crop_data["optimal_temp_range"]
        avg_temp = weather_analysis.temperature_range["average"]
        if avg_temp < temp_range[0] - 5 or avg_temp > temp_range[1] + 5:
            risk_factors.append("Temperature conditions outside optimal range for crop")
            risk_scores.append(0.6)
        
        # Soil risks
        if soil_assessment.fertility_score < 0.5:
            risk_factors.append("Low soil fertility may significantly reduce yield")
            risk_scores.append(0.6)
        
        if soil_assessment.water_retention_score < 0.4:
            risk_factors.append("Poor water retention may cause water stress")
            risk_scores.append(0.5)
        
        # pH compatibility risk
        ph_range = crop_data["soil_ph_range"]
        soil_ph = soil_assessment.properties.ph_level
        if soil_ph < ph_range[0] - 1 or soil_ph > ph_range[1] + 1:
            risk_factors.append("Soil pH significantly outside optimal range")
            risk_scores.append(0.7)
        
        # Market risks
        if demand_forecast.demand_growth_rate < -0.05:
            risk_factors.append("Declining market demand trend")
            risk_scores.append(0.7)
        
        # Price volatility risk
        price_projections = demand_forecast.price_projection
        if len(price_projections) >= 2:
            current_price = price_projections.get("current", 0)
            future_price = price_projections.get("12_month", current_price)
            if current_price > 0:
                price_change = abs(future_price - current_price) / current_price
                if price_change > 0.3:  # More than 30% price volatility
                    risk_factors.append("High price volatility expected")
                    risk_scores.append(0.6)
        
        # Water requirement vs availability risk
        water_req = crop_data["water_requirement_mm"]
        if water_req > 1000:  # High water requirement
            risk_factors.append("High water requirement crop - vulnerable to water scarcity")
            risk_scores.append(0.5)
        elif water_req > 1500:  # Very high water requirement
            risk_factors.append("Very high water requirement - significant drought vulnerability")
            risk_scores.append(0.7)
        
        # Seasonal timing risks
        current_month = datetime.now().month
        optimal_windows = weather_analysis.optimal_planting_windows
        
        in_optimal_window = False
        for window in optimal_windows:
            if window["month"] == current_month and window["suitability"] in ["high", "medium"]:
                in_optimal_window = True
                break
        
        if not in_optimal_window:
            risk_factors.append("Planting outside optimal seasonal window")
            risk_scores.append(0.4)
        
        # Pest and disease risks (crop-specific)
        high_pest_risk_crops = ["cotton", "vegetables", "fruits"]
        if crop_data.get("type") == CropType.CASH_CROPS or any(crop in crop_data.get("varieties", []) for crop in high_pest_risk_crops):
            risk_factors.append("Higher pest and disease susceptibility")
            risk_scores.append(0.4)
        
        # Input cost inflation risk
        if crop_data["input_costs_per_acre"]["total"] > 40000:  # High input cost crops
            risk_factors.append("High input costs vulnerable to inflation")
            risk_scores.append(0.3)
        
        # Export dependency risk
        export_opportunities = demand_forecast.export_opportunities
        if export_opportunities and len(export_opportunities) > 0:
            # Check if heavily dependent on exports
            total_export_potential = sum(
                float(opp.get("potential_volume", "0%").replace("%", "")) 
                for opp in export_opportunities
            )
            if total_export_potential > 50:  # More than 50% export potential
                risk_factors.append("High export dependency - vulnerable to international market changes")
                risk_scores.append(0.4)
        
        # Storage and post-harvest risks
        perishable_crops = ["vegetables", "fruits"]
        if any(crop_type in str(crop_data.get("type", "")).lower() for crop_type in perishable_crops):
            risk_factors.append("Perishable crop - higher post-harvest losses risk")
            risk_scores.append(0.3)
        
        # Determine overall risk level
        if not risk_scores:
            overall_risk = RiskLevel.LOW
        else:
            avg_risk = statistics.mean(risk_scores)
            max_risk = max(risk_scores)
            
            # Use both average and maximum risk for assessment
            if max_risk > 0.8 or avg_risk > 0.6:
                overall_risk = RiskLevel.HIGH
            elif max_risk > 0.6 or avg_risk > 0.4:
                overall_risk = RiskLevel.MEDIUM
            else:
                overall_risk = RiskLevel.LOW
        
        return overall_risk, risk_factors
    
    def _generate_market_outlook(self, demand_forecast: DemandForecast) -> str:
        """Generate market outlook description"""
        
        growth_rate = demand_forecast.demand_growth_rate
        
        if growth_rate > 0.1:
            return "Strong market growth expected with good demand"
        elif growth_rate > 0.05:
            return "Moderate market growth with stable demand"
        elif growth_rate > 0:
            return "Steady market with slight growth in demand"
        else:
            return "Market facing challenges with declining demand"
    
    async def create_comprehensive_plan(
        self,
        request: CropPlanningRequest,
        recommendations: List[CropRecommendation]
    ) -> CropPlan:
        """Create comprehensive crop plan"""
        
        try:
            # Get analysis data
            weather_analysis = await self._get_weather_analysis(request)
            soil_assessment = await self._get_soil_assessment(request)
            
            # Select crops for the plan based on area allocation
            planned_crops = self._allocate_crops_to_area(
                recommendations, request.farm_constraints.total_area_acres
            )
            
            # Calculate financial totals
            total_investment = sum(crop.total_investment for crop in planned_crops)
            projected_revenue = sum(crop.projected_revenue for crop in planned_crops)
            net_profit = projected_revenue - total_investment
            roi_percentage = (net_profit / total_investment * 100) if total_investment > 0 else 0
            
            # Create risk assessment
            risk_assessment = self._create_comprehensive_risk_assessment(
                planned_crops, weather_analysis, soil_assessment
            )
            
            # Generate optimization suggestions
            optimization_suggestions = self._generate_optimization_suggestions(
                planned_crops, request.farm_constraints
            )
            
            plan = CropPlan(
                plan_id=str(uuid.uuid4()),
                farmer_id=request.farmer_id,
                farm_location=request.farm_location,
                planning_season=request.planning_season,
                planning_year=request.planning_year,
                weather_analysis=weather_analysis,
                soil_assessment=soil_assessment,
                planned_crops=planned_crops,
                total_investment=total_investment,
                projected_revenue=projected_revenue,
                net_profit=net_profit,
                roi_percentage=roi_percentage,
                risk_assessment=risk_assessment,
                optimization_suggestions=optimization_suggestions,
                plan_confidence=self._calculate_plan_confidence(planned_crops),
                validation_notes=[]
            )
            
            return plan
            
        except Exception as e:
            logger.error(f"Comprehensive plan creation failed: {str(e)}")
            raise
    
    def _allocate_crops_to_area(
        self,
        recommendations: List[CropRecommendation],
        total_area: float
    ) -> List[PlannedCrop]:
        """Allocate crops to available area"""
        
        planned_crops = []
        remaining_area = total_area
        
        # Sort by suitability score
        sorted_recommendations = sorted(recommendations, key=lambda x: x.suitability_score, reverse=True)
        
        for i, recommendation in enumerate(sorted_recommendations[:3]):  # Max 3 crops
            if remaining_area <= 0:
                break
            
            # Allocate area (first crop gets more area)
            if i == 0:
                allocated_area = min(remaining_area * 0.6, remaining_area)
            elif i == 1:
                allocated_area = min(remaining_area * 0.7, remaining_area)
            else:
                allocated_area = remaining_area
            
            if allocated_area > 0:
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
        
        return planned_crops
    
    def _create_comprehensive_risk_assessment(
        self,
        planned_crops: List[PlannedCrop],
        weather_analysis: WeatherAnalysis,
        soil_assessment: SoilAssessment
    ) -> RiskAssessment:
        """Create comprehensive risk assessment for the plan"""
        
        risk_factors = []
        
        # Collect all risk factors from crops
        for planned_crop in planned_crops:
            for risk_factor in planned_crop.crop_recommendation.risk_factors:
                risk_factors.append(RiskFactor(
                    factor_type="crop_specific",
                    description=f"{planned_crop.crop_recommendation.crop_name}: {risk_factor}",
                    probability=0.3,
                    impact_level=planned_crop.crop_recommendation.risk_level,
                    mitigation_strategies=["Diversification", "Insurance", "Improved practices"]
                ))
        
        # Weather risks
        weather_risks = []
        if weather_analysis.drought_risk != RiskLevel.LOW:
            weather_risks.append(f"Drought risk: {weather_analysis.drought_risk.value}")
        if weather_analysis.flood_risk != RiskLevel.LOW:
            weather_risks.append(f"Flood risk: {weather_analysis.flood_risk.value}")
        
        # Market risks
        market_risks = ["Price volatility", "Demand fluctuation", "Supply chain disruption"]
        
        # Production risks
        production_risks = ["Pest and disease", "Input cost increase", "Labor shortage"]
        
        # Financial risks
        financial_risks = ["Credit availability", "Input price inflation", "Market access"]
        
        # Overall risk level
        crop_risk_levels = [crop.crop_recommendation.risk_level for crop in planned_crops]
        if RiskLevel.HIGH in crop_risk_levels:
            overall_risk = RiskLevel.HIGH
        elif RiskLevel.MEDIUM in crop_risk_levels:
            overall_risk = RiskLevel.MEDIUM
        else:
            overall_risk = RiskLevel.LOW
        
        return RiskAssessment(
            overall_risk_level=overall_risk,
            risk_factors=risk_factors,
            weather_risks=weather_risks,
            market_risks=market_risks,
            production_risks=production_risks,
            financial_risks=financial_risks,
            risk_mitigation_plan=[
                "Diversify crop portfolio",
                "Invest in water conservation",
                "Use improved varieties",
                "Consider crop insurance",
                "Maintain emergency fund"
            ]
        )
    
    def _generate_optimization_suggestions(
        self,
        planned_crops: List[PlannedCrop],
        farm_constraints
    ) -> List[str]:
        """Generate comprehensive optimization suggestions"""
        
        suggestions = []
        
        # Water optimization
        total_water_req = sum(
            crop.crop_recommendation.water_requirement_mm * crop.allocated_area_acres 
            for crop in planned_crops
        )
        
        if farm_constraints.available_water_acre_feet:
            available_water_mm = farm_constraints.available_water_acre_feet * 1233.48  # Convert to mm
            if total_water_req > available_water_mm:
                suggestions.append("Consider drought-resistant varieties to reduce water requirement")
                suggestions.append("Implement water-efficient irrigation methods like drip or sprinkler systems")
            elif total_water_req < available_water_mm * 0.7:
                suggestions.append("Water availability allows for additional water-intensive crops")
        
        # Diversification optimization
        if len(planned_crops) == 1:
            suggestions.append("Consider diversifying with additional crops to reduce risk")
        elif len(planned_crops) > 3:
            suggestions.append("Consider consolidating to fewer crops for better management efficiency")
        
        # Crop type diversification
        crop_types = set(crop.crop_recommendation.crop_type for crop in planned_crops)
        if len(crop_types) == 1:
            suggestions.append("Diversify across different crop types (cereals, pulses, cash crops) for risk reduction")
        
        # Profitability optimization
        avg_profit_per_acre = statistics.mean([
            crop.net_profit / crop.allocated_area_acres for crop in planned_crops
        ])
        if avg_profit_per_acre < 20000:
            suggestions.append("Consider higher-value crops or improved varieties for better profitability")
        
        # Identify most profitable crop for expansion
        if len(planned_crops) > 1:
            most_profitable = max(planned_crops, key=lambda x: x.net_profit / x.allocated_area_acres)
            suggestions.append(f"Consider expanding {most_profitable.crop_recommendation.crop_name} area for higher profits")
        
        # Seasonal optimization
        suggestions.append("Plan crop rotation for soil health and sustained productivity")
        
        # Export opportunity optimization
        export_potential_crops = []
        for crop in planned_crops:
            crop_name = crop.crop_recommendation.crop_name.lower()
            if crop_name in ["cotton", "rice", "spices", "tea", "coffee"]:
                export_potential_crops.append(crop.crop_recommendation.crop_name)
        
        if export_potential_crops:
            suggestions.append(f"Focus on quality improvement for export potential: {', '.join(export_potential_crops)}")
        
        # Budget optimization
        if farm_constraints.budget_limit:
            total_investment = sum(crop.total_investment for crop in planned_crops)
            if total_investment > farm_constraints.budget_limit:
                suggestions.append("Consider reducing area or selecting lower-cost crops to stay within budget")
            elif total_investment < farm_constraints.budget_limit * 0.8:
                suggestions.append("Budget allows for additional investment in higher-value crops or inputs")
        
        # Labor optimization
        if farm_constraints.labor_availability == "limited":
            suggestions.append("Consider mechanization or less labor-intensive crops")
        elif farm_constraints.labor_availability == "abundant":
            suggestions.append("Consider labor-intensive high-value crops like vegetables or fruits")
        
        # Storage optimization
        if farm_constraints.storage_capacity:
            total_expected_yield = sum(
                crop.crop_recommendation.expected_yield_per_acre * crop.allocated_area_acres 
                for crop in planned_crops
            )
            if total_expected_yield > farm_constraints.storage_capacity:
                suggestions.append("Consider crops with better storage life or invest in additional storage")
        
        # Transportation optimization
        if farm_constraints.transportation_access == "poor":
            suggestions.append("Focus on crops with longer shelf life and better transportability")
        elif farm_constraints.transportation_access == "excellent":
            suggestions.append("Consider perishable high-value crops due to good transportation access")
        
        # Risk optimization
        high_risk_crops = [crop for crop in planned_crops if crop.crop_recommendation.risk_level == RiskLevel.HIGH]
        if len(high_risk_crops) > len(planned_crops) * 0.5:
            suggestions.append("Consider reducing high-risk crop allocation and adding more stable crops")
        
        # Seasonal timing optimization
        current_month = datetime.now().month
        for crop in planned_crops:
            if crop.crop_recommendation.season == Season.KHARIF and current_month > 8:
                suggestions.append(f"Consider rabi alternatives for {crop.crop_recommendation.crop_name} due to late season")
            elif crop.crop_recommendation.season == Season.RABI and current_month > 2:
                suggestions.append(f"Consider zaid alternatives for {crop.crop_recommendation.crop_name} due to late season")
        
        return suggestions
    
    def _calculate_plan_confidence(self, planned_crops: List[PlannedCrop]) -> float:
        """Calculate overall plan confidence"""
        if not planned_crops:
            return 0.0
        
        confidence_scores = [crop.crop_recommendation.confidence_level for crop in planned_crops]
        return statistics.mean(confidence_scores)
    
    async def _get_weather_analysis(self, request: CropPlanningRequest) -> WeatherAnalysis:
        """Get weather analysis (placeholder - would use actual weather analyzer)"""
        from weather_analyzer import WeatherAnalyzer
        weather_analyzer = WeatherAnalyzer()
        return await weather_analyzer.analyze_patterns(
            request.farm_location.latitude,
            request.farm_location.longitude,
            timedelta(days=180)
        )
    
    async def _get_soil_assessment(self, request: CropPlanningRequest) -> SoilAssessment:
        """Get soil assessment (placeholder - would use actual soil analyzer)"""
        from soil_analyzer import SoilAnalyzer
        soil_analyzer = SoilAnalyzer()
        return await soil_analyzer.assess_conditions(
            request.farm_location.latitude,
            request.farm_location.longitude,
            request.soil_type.value if request.soil_type else None
        )