"""
Data models for Benchmarking Service
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class BenchmarkStatus(str, Enum):
    """Status of benchmark"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"

class PerformanceCategory(str, Enum):
    """Performance categories"""
    EXCELLENT = "excellent"
    GOOD = "good"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"
    POOR = "poor"

# Request Models
class PriceFloorRequest(BaseModel):
    """Request to set price floor"""
    farmer_id: UUID
    commodity: str
    floor_price: float = Field(..., gt=0, description="Minimum acceptable price")
    unit: str = Field(default="per_quintal", description="Price unit")
    reasoning: Optional[str] = Field(None, description="Reason for setting this floor")
    
    @validator('commodity')
    def validate_commodity(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Commodity name cannot be empty')
        return v.strip().lower()

class BenchmarkRequest(BaseModel):
    """Request to create benchmark"""
    farmer_id: UUID
    commodity: str
    analysis_period_days: int = Field(default=30, ge=7, le=365, description="Days to analyze")
    location_filter: Optional[str] = Field(None, description="Location filter for analysis")
    
    @validator('commodity')
    def validate_commodity(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Commodity name cannot be empty')
        return v.strip().lower()

class PerformanceTrackingRequest(BaseModel):
    """Request to track performance"""
    farmer_id: UUID
    commodity: str
    actual_price: float = Field(..., gt=0, description="Actual selling price")
    quantity_sold: float = Field(..., gt=0, description="Quantity sold")
    sale_date: datetime = Field(default_factory=datetime.utcnow)
    location: Optional[str] = Field(None, description="Sale location")
    
    @validator('commodity')
    def validate_commodity(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Commodity name cannot be empty')
        return v.strip().lower()

# Database Models
class PriceFloor(BaseModel):
    """Price floor model"""
    id: UUID = Field(default_factory=uuid4)
    farmer_id: UUID
    commodity: str
    floor_price: float
    unit: str
    reasoning: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    
    class Config:
        from_attributes = True

class ConversationRecord(BaseModel):
    """Conversation record for benchmark analysis"""
    id: UUID = Field(default_factory=uuid4)
    farmer_id: UUID
    commodity: Optional[str] = None
    price_extracted: Optional[float] = None
    quantity_extracted: Optional[float] = None
    intent: Optional[str] = None
    location: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    conversation_text: Optional[str] = None
    audio_segment_id: Optional[str] = None
    recorded_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class FarmerBenchmark(BaseModel):
    """Farmer benchmark model"""
    id: UUID = Field(default_factory=uuid4)
    farmer_id: UUID
    commodity: str
    benchmark_price: float
    price_range: Dict[str, float]  # min, max, avg, median
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    data_points_count: int
    analysis_period: str  # e.g., "30 days", "3 months"
    location_context: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: BenchmarkStatus = BenchmarkStatus.ACTIVE
    is_active: bool = True
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class PerformanceMetric(BaseModel):
    """Performance tracking model"""
    id: UUID = Field(default_factory=uuid4)
    farmer_id: UUID
    commodity: str
    actual_price: float
    benchmark_price: Optional[float] = None
    price_floor: Optional[float] = None
    performance_score: float = Field(..., ge=0.0, le=100.0)
    vs_benchmark: Optional[float] = None  # percentage difference
    vs_floor: Optional[float] = None  # percentage above floor
    quantity_sold: float
    total_revenue: float
    benchmark_revenue: Optional[float] = None
    revenue_difference: Optional[float] = None
    sale_date: datetime
    location: Optional[str] = None
    category: PerformanceCategory
    analysis: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True

class BenchmarkAnalysis(BaseModel):
    """Benchmark analysis result"""
    commodity: str
    total_conversations: int
    price_data_points: int
    average_price: float
    median_price: float
    price_range: Dict[str, float]
    confidence_factors: Dict[str, float]
    location_breakdown: Dict[str, Any]
    time_trend: List[Dict[str, Any]]
    quality_indicators: Dict[str, Any]
    
    class Config:
        from_attributes = True

# Response Models
class PriceFloorResponse(BaseModel):
    """Price floor response"""
    id: UUID
    farmer_id: UUID
    commodity: str
    floor_price: float
    unit: str
    reasoning: Optional[str]
    created_at: datetime
    is_active: bool

class BenchmarkResponse(BaseModel):
    """Benchmark response"""
    id: UUID
    farmer_id: UUID
    commodity: str
    benchmark_price: float
    price_range: Dict[str, float]
    confidence_score: float
    data_points_count: int
    analysis_period: str
    created_at: datetime

class PerformanceResponse(BaseModel):
    """Performance response"""
    id: UUID
    farmer_id: UUID
    commodity: str
    actual_price: float
    benchmark_price: Optional[float]
    performance_score: float
    vs_benchmark: Optional[float]
    total_revenue: float
    sale_date: datetime
    category: PerformanceCategory

class AnalyticsResponse(BaseModel):
    """Analytics response"""
    farmer_id: UUID
    period: str
    total_sales: int
    total_revenue: float
    average_performance_score: float
    best_performing_commodity: Optional[str]
    improvement_over_time: float
    benchmark_adherence_rate: float
    floor_violation_count: int
    recommendations: List[str]

# Internal Models
class PriceDataPoint(BaseModel):
    """Individual price data point"""
    price: float
    quantity: Optional[float]
    date: datetime
    location: Optional[str]
    confidence: float
    source: str  # conversation, manual, etc.

class TrendAnalysis(BaseModel):
    """Trend analysis result"""
    trend_direction: str  # "rising", "falling", "stable"
    trend_strength: float  # 0.0 to 1.0
    volatility: float
    seasonal_pattern: Optional[Dict[str, Any]]
    key_factors: List[str]

class RecommendationEngine(BaseModel):
    """Recommendation result"""
    recommendation_type: str
    priority: str  # "high", "medium", "low"
    title: str
    description: str
    action_items: List[str]
    expected_impact: Optional[str]
    confidence: float

class MarketContext(BaseModel):
    """Market context for benchmarking"""
    regional_average: Optional[float]
    national_average: Optional[float]
    seasonal_factor: Optional[float]
    demand_indicator: Optional[str]
    supply_indicator: Optional[str]
    market_sentiment: Optional[str]