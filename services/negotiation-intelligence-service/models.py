"""
Data models for the Negotiation Intelligence Service
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class NegotiationTactic(str, Enum):
    HOLD_FIRM = "hold_firm"
    GRADUAL_CONCESSION = "gradual_concession"
    COMPETITIVE_BIDDING = "competitive_bidding"
    TIME_PRESSURE = "time_pressure"
    QUALITY_EMPHASIS = "quality_emphasis"
    VOLUME_DISCOUNT = "volume_discount"

class MarketCondition(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    STABLE = "stable"
    VOLATILE = "volatile"

class GeoLocation(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None
    mandi_name: Optional[str] = None

class PriceRange(BaseModel):
    min_price: float
    max_price: float
    optimal_price: float
    confidence: float = Field(ge=0.0, le=1.0)

class MarketContext(BaseModel):
    commodity: str
    current_price: float
    price_trend: str  # "increasing", "decreasing", "stable"
    market_condition: MarketCondition
    supply_level: str  # "high", "medium", "low"
    demand_level: str  # "high", "medium", "low"
    seasonal_factor: float
    weather_impact: Optional[str] = None
    festival_demand: bool = False
    export_demand: Optional[float] = None
    transportation_cost: float
    storage_cost: float
    quality_premium: float
    competition_level: str  # "high", "medium", "low"
    timestamp: datetime = Field(default_factory=datetime.now)

class BuyerIntent(BaseModel):
    urgency: UrgencyLevel
    price_sensitivity: float = Field(ge=0.0, le=1.0)
    quality_focus: float = Field(ge=0.0, le=1.0)
    volume_requirement: float
    negotiation_style: str  # "aggressive", "collaborative", "passive"
    budget_constraint: Optional[float] = None
    alternative_sources: int
    relationship_value: float = Field(ge=0.0, le=1.0)
    repeat_buyer: bool = False
    payment_terms_flexibility: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)

class TimingRecommendation(BaseModel):
    optimal_timing: str  # "immediate", "wait_short", "wait_long"
    wait_duration: Optional[int] = None  # minutes
    price_movement_prediction: str  # "increase", "decrease", "stable"
    confidence: float = Field(ge=0.0, le=1.0)

class AlternativeOption(BaseModel):
    option_type: str  # "different_buyer", "different_mandi", "storage"
    description: str
    expected_price: float
    time_to_execute: int  # minutes
    risk_level: RiskLevel
    confidence: float = Field(ge=0.0, le=1.0)

class NegotiationStrategy(BaseModel):
    recommended_price: float
    price_range: PriceRange
    tactics: List[NegotiationTactic]
    timing: TimingRecommendation
    alternatives: List[AlternativeOption]
    key_arguments: List[str]
    concession_strategy: Dict[str, Any]
    risk_assessment: RiskLevel
    success_probability: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    generated_at: datetime = Field(default_factory=datetime.now)

class OutcomePrediction(BaseModel):
    success_probability: float = Field(ge=0.0, le=1.0)
    expected_final_price: float
    negotiation_duration: int  # minutes
    farmer_satisfaction_score: float = Field(ge=1.0, le=5.0)
    key_success_factors: List[str]
    potential_obstacles: List[str]
    confidence: float = Field(ge=0.0, le=1.0)

class NegotiationSession(BaseModel):
    session_id: str
    farmer_id: str
    commodity: str
    location: GeoLocation
    start_time: datetime
    end_time: Optional[datetime] = None
    initial_offer: float
    final_price: Optional[float] = None
    strategy_used: Optional[NegotiationStrategy] = None
    buyer_intent: Optional[BuyerIntent] = None
    market_context: Optional[MarketContext] = None
    conversation_data: Optional[str] = None
    success: Optional[bool] = None
    farmer_satisfaction: Optional[int] = None
    lessons_learned: List[str] = []

class NegotiationOutcome(BaseModel):
    session_id: str
    final_price: float
    success: bool
    farmer_satisfaction: int = Field(ge=1, le=5)
    strategy_effectiveness: float = Field(ge=0.0, le=1.0)
    time_to_close: int  # minutes
    concessions_made: List[Dict[str, Any]]
    key_factors: List[str]
    lessons_learned: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)

class LearningData(BaseModel):
    commodity: str
    market_conditions: Dict[str, Any]
    strategy_used: Dict[str, Any]
    outcome: Dict[str, Any]
    success_rate: float
    average_price_improvement: float
    pattern_insights: List[str]
    updated_at: datetime = Field(default_factory=datetime.now)