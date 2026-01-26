"""
Data models for Anti-Hoarding Detection Service
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, date
from enum import Enum
from uuid import UUID, uuid4
import math

class AnomalyType(str, Enum):
    """Types of market anomalies"""
    PRICE_SPIKE = "price_spike"
    INVENTORY_HOARDING = "inventory_hoarding"
    SUPPLY_MANIPULATION = "supply_manipulation"
    ARTIFICIAL_SCARCITY = "artificial_scarcity"
    STOCKPILING_PATTERN = "stockpiling_pattern"

class AnomalySeverity(str, Enum):
    """Severity levels for anomalies"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DetectionMethod(str, Enum):
    """Methods used for anomaly detection"""
    STATISTICAL_ANALYSIS = "statistical_analysis"
    MOVING_AVERAGE_DEVIATION = "moving_average_deviation"
    INVENTORY_TRACKING = "inventory_tracking"
    PATTERN_RECOGNITION = "pattern_recognition"
    MACHINE_LEARNING = "machine_learning"

class MarketManipulationType(str, Enum):
    """Types of market manipulation"""
    HOARDING = "hoarding"
    CORNERING = "cornering"
    PRICE_FIXING = "price_fixing"
    SUPPLY_RESTRICTION = "supply_restriction"
    DEMAND_INFLATION = "demand_inflation"

class GeoLocation(BaseModel):
    """Geographic location"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    district: Optional[str] = None
    state: str
    country: str = "India"

class PriceAnomaly(BaseModel):
    """Price anomaly detection result"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    commodity: str
    variety: Optional[str] = None
    mandi_id: str
    mandi_name: str
    location: GeoLocation
    anomaly_type: AnomalyType
    detection_method: DetectionMethod
    severity: AnomalySeverity
    
    # Price data
    current_price: float = Field(..., gt=0)
    baseline_price: float = Field(..., gt=0)
    price_deviation: float  # Absolute deviation
    deviation_percentage: float  # Percentage deviation
    
    # Statistical measures
    moving_average_30d: float
    standard_deviation: float
    z_score: float
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    
    # Time information
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    analysis_period_days: int = Field(default=30)
    
    # Evidence and context
    evidence: Dict[str, Any] = {}
    contributing_factors: List[str] = []
    historical_context: Optional[str] = None
    
    # Status
    is_confirmed: bool = False
    is_resolved: bool = False
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None

class InventoryAnomaly(BaseModel):
    """Inventory level anomaly detection result"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    commodity: str
    variety: Optional[str] = None
    region: str  # Can be district, state, or multi-state
    anomaly_type: AnomalyType
    detection_method: DetectionMethod
    severity: AnomalySeverity
    
    # Inventory data
    current_inventory_level: float = Field(..., ge=0)
    normal_inventory_level: float = Field(..., ge=0)
    inventory_deviation: float
    deviation_percentage: float
    
    # Tracking across mandis
    affected_mandis: List[str] = []
    total_mandis_monitored: int
    concentration_ratio: float = Field(..., ge=0.0, le=1.0)  # How concentrated the inventory is
    
    # Time analysis
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    accumulation_period_days: int
    trend_direction: str  # "increasing", "decreasing", "stable"
    
    # Evidence
    evidence: Dict[str, Any] = {}
    stockpiling_indicators: List[str] = []
    
    # Status
    is_confirmed: bool = False
    is_resolved: bool = False

class StockpilingPattern(BaseModel):
    """Stockpiling pattern detection result"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    commodity: str
    variety: Optional[str] = None
    pattern_type: str  # "coordinated", "seasonal_unusual", "cross_regional"
    detection_method: DetectionMethod
    severity: AnomalySeverity
    
    # Pattern characteristics
    involved_locations: List[str] = []
    pattern_duration_days: int
    accumulation_rate: float  # Units per day
    total_accumulated_quantity: float
    
    # Market impact
    price_impact_percentage: Optional[float] = None
    supply_reduction_percentage: Optional[float] = None
    affected_market_radius_km: Optional[float] = None
    
    # Detection details
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    pattern_indicators: List[str] = []
    
    # Evidence
    evidence: Dict[str, Any] = {}
    coordination_evidence: Optional[Dict[str, Any]] = None
    
    # Status
    is_confirmed: bool = False
    is_resolved: bool = False

class MarketManipulationAlert(BaseModel):
    """Alert for detected market manipulation"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    alert_type: str = "market_manipulation"
    manipulation_type: MarketManipulationType
    severity: AnomalySeverity
    
    # Related anomalies
    price_anomaly_ids: List[str] = []
    inventory_anomaly_ids: List[str] = []
    stockpiling_pattern_ids: List[str] = []
    
    # Alert content
    title: str
    message: str
    commodity: str
    affected_regions: List[str] = []
    estimated_impact: Optional[str] = None
    
    # Recommendations
    farmer_recommendations: List[str] = []
    alternative_markets: List[str] = []
    authority_actions: List[str] = []
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    evidence_summary: Dict[str, Any] = {}
    
    # Status
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None

class AnomalyDetectionConfig(BaseModel):
    """Configuration for anomaly detection algorithms"""
    # Price spike detection
    price_spike_threshold_percentage: float = Field(default=25.0, ge=5.0, le=100.0)
    moving_average_window_days: int = Field(default=30, ge=7, le=90)
    min_data_points: int = Field(default=10, ge=5, le=100)
    z_score_threshold: float = Field(default=2.5, ge=1.0, le=5.0)
    
    # Inventory tracking
    inventory_deviation_threshold: float = Field(default=30.0, ge=10.0, le=100.0)
    stockpiling_threshold_days: int = Field(default=7, ge=3, le=30)
    concentration_threshold: float = Field(default=0.7, ge=0.5, le=1.0)
    
    # Pattern detection
    pattern_confidence_threshold: float = Field(default=0.75, ge=0.5, le=1.0)
    coordination_detection_enabled: bool = True
    cross_regional_analysis_enabled: bool = True
    
    # Alert settings
    alert_cooldown_hours: int = Field(default=6, ge=1, le=24)
    auto_alert_enabled: bool = True
    authority_notification_enabled: bool = True

class DetectionStatistics(BaseModel):
    """Statistics for anomaly detection system"""
    total_anomalies_detected: int = 0
    price_anomalies_count: int = 0
    inventory_anomalies_count: int = 0
    stockpiling_patterns_count: int = 0
    
    # By severity
    critical_anomalies: int = 0
    high_severity_anomalies: int = 0
    medium_severity_anomalies: int = 0
    low_severity_anomalies: int = 0
    
    # Resolution stats
    confirmed_anomalies: int = 0
    resolved_anomalies: int = 0
    false_positives: int = 0
    
    # Performance metrics
    average_detection_time_minutes: float = 0.0
    accuracy_rate: float = 0.0
    
    # Time period
    statistics_period_start: datetime
    statistics_period_end: datetime
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class SupplyDemandBalance(BaseModel):
    """Supply-demand balance indicator"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    commodity: str
    variety: Optional[str] = None
    region: str
    
    # Supply metrics
    total_supply: float = Field(..., ge=0)
    available_supply: float = Field(..., ge=0)
    reserved_supply: float = Field(..., ge=0)
    supply_trend: str  # "increasing", "decreasing", "stable"
    
    # Demand metrics
    estimated_demand: float = Field(..., ge=0)
    actual_consumption: float = Field(..., ge=0)
    demand_trend: str  # "increasing", "decreasing", "stable"
    
    # Balance calculation
    supply_demand_ratio: float
    balance_status: str  # "surplus", "balanced", "deficit", "critical_shortage"
    balance_score: float = Field(..., ge=-1.0, le=1.0)  # -1 (shortage) to 1 (surplus)
    
    # Market indicators
    price_pressure_indicator: str  # "upward", "downward", "neutral"
    volatility_risk: str  # "low", "medium", "high"
    
    # Time information
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    data_freshness_hours: float
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    
    # Contributing factors
    supply_factors: List[str] = []
    demand_factors: List[str] = []
    external_factors: List[str] = []

class EvidenceRecord(BaseModel):
    """Evidence record for anomaly detection"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    anomaly_id: str
    evidence_type: str  # "price_data", "inventory_data", "pattern_analysis", "statistical"
    
    # Evidence content
    data_points: List[Dict[str, Any]] = []
    analysis_results: Dict[str, Any] = {}
    supporting_documents: List[str] = []
    
    # Metadata
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    source: str
    reliability_score: float = Field(..., ge=0.0, le=1.0)
    
    # Verification
    is_verified: bool = False
    verified_by: Optional[str] = None
    verification_notes: Optional[str] = None