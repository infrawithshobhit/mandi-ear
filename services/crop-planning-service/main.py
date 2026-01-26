"""
Crop Planning Service - Main Application

This service provides comprehensive crop planning recommendations based on:
- Weather forecast integration
- Soil condition analysis  
- Demand pattern analysis
- Risk assessment and income optimization
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List, Optional
import logging
from datetime import datetime, timedelta
import statistics

from models import (
    CropPlanningRequest, CropRecommendation, WeatherAnalysis,
    SoilAssessment, DemandForecast, RiskAssessment, CropPlan
)
from weather_analyzer import WeatherAnalyzer
from soil_analyzer import SoilAnalyzer
from demand_analyzer import DemandAnalyzer
from recommendation_engine import RecommendationEngine
from resource_optimizer import ResourceOptimizer
from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MANDI EAR - Crop Planning Service",
    description="AI-powered crop planning and recommendation system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analyzers
settings = get_settings()
weather_analyzer = WeatherAnalyzer(settings.weather_api_key)
soil_analyzer = SoilAnalyzer()
demand_analyzer = DemandAnalyzer()
recommendation_engine = RecommendationEngine()
resource_optimizer = ResourceOptimizer()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "crop-planning", "timestamp": datetime.utcnow()}

@app.post("/analyze/weather", response_model=WeatherAnalysis)
async def analyze_weather(
    latitude: float,
    longitude: float,
    timeframe_months: int = 6
):
    """
    Analyze weather patterns for crop planning
    
    Args:
        latitude: Farm latitude
        longitude: Farm longitude  
        timeframe_months: Analysis timeframe in months
    """
    try:
        analysis = await weather_analyzer.analyze_patterns(
            latitude=latitude,
            longitude=longitude,
            timeframe=timedelta(days=timeframe_months * 30)
        )
        return analysis
    except Exception as e:
        logger.error(f"Weather analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Weather analysis failed: {str(e)}")

@app.post("/analyze/soil", response_model=SoilAssessment)
async def analyze_soil(
    latitude: float,
    longitude: float,
    soil_type: Optional[str] = None
):
    """
    Analyze soil conditions for crop suitability
    
    Args:
        latitude: Farm latitude
        longitude: Farm longitude
        soil_type: Optional known soil type
    """
    try:
        assessment = await soil_analyzer.assess_conditions(
            latitude=latitude,
            longitude=longitude,
            known_soil_type=soil_type
        )
        return assessment
    except Exception as e:
        logger.error(f"Soil analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Soil analysis failed: {str(e)}")

@app.post("/analyze/demand", response_model=DemandForecast)
async def analyze_demand(
    commodity: str,
    region: str,
    timeframe_months: int = 12
):
    """
    Analyze market demand patterns for crop planning
    
    Args:
        commodity: Crop/commodity name
        region: Geographic region
        timeframe_months: Forecast timeframe in months
    """
    try:
        forecast = await demand_analyzer.forecast_demand(
            commodity=commodity,
            region=region,
            timeframe=timedelta(days=timeframe_months * 30)
        )
        return forecast
    except Exception as e:
        logger.error(f"Demand analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Demand analysis failed: {str(e)}")

@app.post("/recommend", response_model=List[CropRecommendation])
async def get_crop_recommendations(request: CropPlanningRequest):
    """
    Get comprehensive crop recommendations based on all analysis factors
    
    Args:
        request: Crop planning request with farm details and constraints
    """
    try:
        # Perform comprehensive analysis
        weather_analysis = await weather_analyzer.analyze_patterns(
            latitude=request.farm_location.latitude,
            longitude=request.farm_location.longitude,
            timeframe=timedelta(days=180)  # 6 months
        )
        
        soil_assessment = await soil_analyzer.assess_conditions(
            latitude=request.farm_location.latitude,
            longitude=request.farm_location.longitude,
            known_soil_type=request.soil_type
        )
        
        # Generate recommendations
        recommendations = await recommendation_engine.generate_recommendations(
            request=request,
            weather_analysis=weather_analysis,
            soil_assessment=soil_assessment
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Crop recommendation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Crop recommendation failed: {str(e)}")

@app.post("/plan", response_model=CropPlan)
async def create_crop_plan(request: CropPlanningRequest):
    """
    Create comprehensive crop plan with income projections and risk assessment
    
    Args:
        request: Crop planning request with farm details and constraints
    """
    try:
        # Get recommendations first
        recommendations = await get_crop_recommendations(request)
        
        # Create comprehensive plan
        plan = await recommendation_engine.create_comprehensive_plan(
            request=request,
            recommendations=recommendations
        )
        
        return plan
        
    except Exception as e:
        logger.error(f"Crop plan creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Crop plan creation failed: {str(e)}")

@app.post("/optimize/water")
async def optimize_water_allocation(
    request: CropPlanningRequest,
    drought_probability: float = 0.0
):
    """
    Optimize crop allocation based on water availability constraints
    
    Args:
        request: Crop planning request with water constraints
        drought_probability: Probability of drought (0-1)
    """
    try:
        # Get base recommendations
        recommendations = await get_crop_recommendations(request)
        
        # Apply water optimization
        optimized_crops = resource_optimizer.optimize_water_allocation(
            recommendations=recommendations,
            farm_constraints=request.farm_constraints,
            drought_probability=drought_probability
        )
        
        # Calculate water stress index
        water_stress = resource_optimizer.calculate_water_stress_index(
            planned_crops=optimized_crops,
            available_water=request.farm_constraints.available_water_acre_feet or 0,
            drought_probability=drought_probability
        )
        
        # Get conservation recommendations
        conservation_recs = resource_optimizer.get_water_conservation_recommendations(
            farm_constraints=request.farm_constraints,
            drought_probability=drought_probability
        )
        
        return {
            "optimized_crops": optimized_crops,
            "water_stress_index": water_stress,
            "conservation_recommendations": conservation_recs,
            "total_water_requirement_mm": sum(
                crop.crop_recommendation.water_requirement_mm * crop.allocated_area_acres
                for crop in optimized_crops
            ),
            "optimization_summary": {
                "drought_probability": drought_probability,
                "available_water_acre_feet": request.farm_constraints.available_water_acre_feet,
                "crops_selected": len(optimized_crops),
                "total_area_allocated": sum(crop.allocated_area_acres for crop in optimized_crops)
            }
        }
        
    except Exception as e:
        logger.error(f"Water optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Water optimization failed: {str(e)}")

@app.post("/optimize/drought-resistant")
async def prioritize_drought_resistant(
    request: CropPlanningRequest,
    drought_risk_level: str = "medium",
    water_scarcity_factor: float = 0.0
):
    """
    Prioritize drought-resistant crops based on risk assessment
    
    Args:
        request: Crop planning request
        drought_risk_level: Drought risk level (low, medium, high, very_high)
        water_scarcity_factor: Water scarcity factor (0-1)
    """
    try:
        from models import RiskLevel
        
        # Convert string to RiskLevel enum
        risk_level_map = {
            "low": RiskLevel.LOW,
            "medium": RiskLevel.MEDIUM,
            "high": RiskLevel.HIGH,
            "very_high": RiskLevel.VERY_HIGH
        }
        risk_level = risk_level_map.get(drought_risk_level.lower(), RiskLevel.MEDIUM)
        
        # Get base recommendations
        recommendations = await get_crop_recommendations(request)
        
        # Prioritize drought-resistant crops
        prioritized_recommendations = resource_optimizer.prioritize_drought_resistant_crops(
            recommendations=recommendations,
            drought_risk_level=risk_level,
            water_scarcity_factor=water_scarcity_factor
        )
        
        # Add drought resistance information
        for rec in prioritized_recommendations:
            crop_name = rec.crop_name.lower()
            rec.drought_resistance_score = resource_optimizer.drought_resistance.get(crop_name, 0.5)
            rec.water_efficiency_score = resource_optimizer.water_efficiency.get(crop_name, 0.5)
        
        return {
            "prioritized_recommendations": prioritized_recommendations,
            "drought_risk_level": drought_risk_level,
            "water_scarcity_factor": water_scarcity_factor,
            "drought_resistant_crops": [
                {
                    "crop_name": rec.crop_name,
                    "drought_resistance": resource_optimizer.drought_resistance.get(rec.crop_name.lower(), 0.5),
                    "water_efficiency": resource_optimizer.water_efficiency.get(rec.crop_name.lower(), 0.5),
                    "water_requirement_mm": rec.water_requirement_mm,
                    "suitability_score": rec.suitability_score
                }
                for rec in prioritized_recommendations[:5]
            ]
        }
        
    except Exception as e:
        logger.error(f"Drought resistance prioritization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Drought resistance prioritization failed: {str(e)}")

@app.post("/optimize/resources")
async def optimize_resource_usage(
    request: CropPlanningRequest,
    optimization_objectives: List[str] = None
):
    """
    Optimize resource usage across multiple constraints
    
    Args:
        request: Crop planning request with resource constraints
        optimization_objectives: List of optimization objectives
    """
    try:
        if optimization_objectives is None:
            optimization_objectives = ["profit_maximization", "resource_efficiency"]
        
        # Get base recommendations
        recommendations = await get_crop_recommendations(request)
        
        # Apply multi-objective resource optimization
        optimized_crops = resource_optimizer.optimize_resource_usage(
            recommendations=recommendations,
            farm_constraints=request.farm_constraints,
            optimization_objectives=optimization_objectives
        )
        
        # Calculate resource utilization metrics
        total_investment = sum(crop.total_investment for crop in optimized_crops)
        total_revenue = sum(crop.projected_revenue for crop in optimized_crops)
        total_area = sum(crop.allocated_area_acres for crop in optimized_crops)
        
        resource_metrics = {
            "total_investment": total_investment,
            "total_projected_revenue": total_revenue,
            "net_profit": total_revenue - total_investment,
            "roi_percentage": ((total_revenue - total_investment) / total_investment * 100) if total_investment > 0 else 0,
            "area_utilization": (total_area / request.farm_constraints.total_area_acres * 100) if request.farm_constraints.total_area_acres > 0 else 0,
            "profit_per_acre": (total_revenue - total_investment) / max(total_area, 0.1),
            "investment_per_acre": total_investment / max(total_area, 0.1)
        }
        
        # Budget utilization
        if request.farm_constraints.budget_limit:
            resource_metrics["budget_utilization"] = (total_investment / request.farm_constraints.budget_limit * 100)
        
        return {
            "optimized_crops": optimized_crops,
            "optimization_objectives": optimization_objectives,
            "resource_metrics": resource_metrics,
            "optimization_summary": {
                "crops_selected": len(optimized_crops),
                "total_area_allocated": total_area,
                "diversification_index": len(set(crop.crop_recommendation.crop_type for crop in optimized_crops)),
                "average_risk_level": statistics.mode([crop.crop_recommendation.risk_level for crop in optimized_crops]) if optimized_crops else "unknown"
            }
        }
        
    except Exception as e:
        logger.error(f"Resource optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Resource optimization failed: {str(e)}")

@app.get("/optimize/conservation-recommendations")
async def get_conservation_recommendations(
    total_area_acres: float,
    available_water_acre_feet: Optional[float] = None,
    drought_probability: float = 0.0
):
    """
    Get water conservation recommendations based on farm constraints
    
    Args:
        total_area_acres: Total farm area
        available_water_acre_feet: Available water resources
        drought_probability: Probability of drought (0-1)
    """
    try:
        from models import FarmConstraints
        
        # Create farm constraints object
        farm_constraints = FarmConstraints(
            total_area_acres=total_area_acres,
            available_water_acre_feet=available_water_acre_feet
        )
        
        # Get conservation recommendations
        recommendations = resource_optimizer.get_water_conservation_recommendations(
            farm_constraints=farm_constraints,
            drought_probability=drought_probability
        )
        
        return {
            "conservation_recommendations": recommendations,
            "farm_area": total_area_acres,
            "available_water": available_water_acre_feet,
            "drought_probability": drought_probability,
            "water_per_acre": (available_water_acre_feet / total_area_acres) if available_water_acre_feet and total_area_acres > 0 else None
        }
        
    except Exception as e:
        logger.error(f"Conservation recommendations failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Conservation recommendations failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8006,
        reload=True
    )