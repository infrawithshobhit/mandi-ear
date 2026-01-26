"""
Data models for crop planning service
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum

class GeoLocation(BaseModel):
    """Geographic location coordinates"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None

class SoilType(str, Enum):
    """Soil type classifications"""
    ALLUVIAL = "alluvial"
    BLACK = "black"
    RED = "red"
    LATERITE = "laterite"
    DESERT = "desert"
    MOUNTAIN = "mountain"
    SALINE = "saline"

class IrrigationType(str, Enum):
    """Irrigation system types"""
    RAINFED = "rainfed"
    CANAL = "canal"
    TUBE_WELL = "tube_well"
    DRIP = "drip"
    SPRINKLER = "sprinkler"

class Season(str, Enum):
    """Agricultural seasons"""
    KHARIF = "kharif"  # Monsoon season
    RABI = "rabi"      # Winter season
    ZAID = "zaid"      # Summer season

class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class CropType(str, Enum):
    """Major crop categories"""
    CEREALS = "cereals"
    PULSES = "pulses"
    OILSEEDS = "oilseeds"
    CASH_CROPS = "cash_crops"
    VEGETABLES = "vegetables"
    FRUITS = "fruits"
    SPICES = "spices"

class WeatherPattern(BaseModel):
    """Weather pattern data"""
    temperature_avg: float
    temperature_min: float
    temperature_max: float
    rainfall_mm: float
    humidity_percent: float
    wind_speed_kmh: float
    month: int

class WeatherAnalysis(BaseModel):
    """Comprehensive weather analysis for crop planning"""
    location: GeoLocation
    analysis_period: str
    patterns: List[WeatherPattern]
    rainfall_total: float
    temperature_range: Dict[str, float]
    drought_risk: RiskLevel
    flood_risk: RiskLevel
    optimal_planting_windows: List[Dict[str, Any]]
    weather_suitability_score: float = Field(..., ge=0, le=1)

class SoilProperties(BaseModel):
    """Soil chemical and physical properties"""
    ph_level: float
    organic_matter_percent: float
    nitrogen_level: str  # low, medium, high
    phosphorus_level: str
    potassium_level: str
    drainage: str  # poor, moderate, good, excellent
    water_holding_capacity: str  # low, medium, high

class SoilAssessment(BaseModel):
    """Comprehensive soil condition assessment"""
    location: GeoLocation
    soil_type: SoilType
    properties: SoilProperties
    suitable_crops: List[str]
    improvement_recommendations: List[str]
    fertility_score: float = Field(..., ge=0, le=1)
    water_retention_score: float = Field(..., ge=0, le=1)

class MarketTrend(BaseModel):
    """Market trend data for demand analysis"""
    month: int
    price_avg: float
    demand_index: float
    supply_index: float
    export_demand: float

class DemandForecast(BaseModel):
    """Market demand forecast for crop planning"""
    commodity: str
    region: str
    forecast_period: str
    trends: List[MarketTrend]
    seasonal_patterns: Dict[str, float]
    export_opportunities: List[Dict[str, Any]]
    price_projection: Dict[str, float]
    demand_growth_rate: float

class CostBreakdown(BaseModel):
    """Detailed cost breakdown for crop production"""
    seeds: float
    fertilizers: float
    pesticides: float
    irrigation: float
    labor: float
    machinery: float
    other: float
    total: float

class CropRecommendation(BaseModel):
    """Individual crop recommendation with complete analysis"""
    crop_name: str
    variety: str
    crop_type: CropType
    season: Season
    planting_window_start: date
    planting_window_end: date
    harvest_window_start: date
    harvest_window_end: date
    expected_yield_per_acre: float
    projected_income_per_acre: float
    production_costs: CostBreakdown
    net_profit_per_acre: float
    risk_level: RiskLevel
    risk_factors: List[str]
    water_requirement_mm: float
    suitability_score: float = Field(..., ge=0, le=1)
    market_outlook: str
    confidence_level: float = Field(..., ge=0, le=1)
    
    # Additional fields for resource optimization
    drought_resistance_score: Optional[float] = Field(None, ge=0, le=1)
    water_efficiency_score: Optional[float] = Field(None, ge=0, le=1)

class FarmConstraints(BaseModel):
    """Farm-specific constraints and resources"""
    total_area_acres: float
    available_water_acre_feet: Optional[float] = None
    budget_limit: Optional[float] = None
    labor_availability: Optional[str] = None  # limited, moderate, abundant
    machinery_access: Optional[List[str]] = None
    storage_capacity: Optional[float] = None
    transportation_access: Optional[str] = None

class CropPlanningRequest(BaseModel):
    """Request for crop planning recommendations"""
    farmer_id: str
    farm_location: GeoLocation
    soil_type: Optional[SoilType] = None
    irrigation_type: IrrigationType
    farm_constraints: FarmConstraints
    preferred_crops: Optional[List[str]] = None
    risk_tolerance: RiskLevel = RiskLevel.MEDIUM
    planning_season: Season
    planning_year: int = Field(default_factory=lambda: datetime.now().year)

class RiskFactor(BaseModel):
    """Individual risk factor assessment"""
    factor_type: str
    description: str
    probability: float = Field(..., ge=0, le=1)
    impact_level: RiskLevel
    mitigation_strategies: List[str]

class RiskAssessment(BaseModel):
    """Comprehensive risk assessment for crop plan"""
    overall_risk_level: RiskLevel
    risk_factors: List[RiskFactor]
    weather_risks: List[str]
    market_risks: List[str]
    production_risks: List[str]
    financial_risks: List[str]
    risk_mitigation_plan: List[str]

class PlannedCrop(BaseModel):
    """Crop planned for specific area with details"""
    crop_recommendation: CropRecommendation
    allocated_area_acres: float
    total_investment: float
    projected_revenue: float
    net_profit: float

class CropPlan(BaseModel):
    """Comprehensive crop plan for a farm"""
    plan_id: str
    farmer_id: str
    farm_location: GeoLocation
    planning_season: Season
    planning_year: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Analysis results
    weather_analysis: WeatherAnalysis
    soil_assessment: SoilAssessment
    
    # Planned crops
    planned_crops: List[PlannedCrop]
    
    # Financial projections
    total_investment: float
    projected_revenue: float
    net_profit: float
    roi_percentage: float
    
    # Risk assessment
    risk_assessment: RiskAssessment
    
    # Recommendations
    optimization_suggestions: List[str]
    alternative_plans: Optional[List[Dict[str, Any]]] = None
    
    # Confidence and validation
    plan_confidence: float = Field(..., ge=0, le=1)
    validation_notes: List[str] = []