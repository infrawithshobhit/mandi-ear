"""
Data models for Price Discovery Service
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

class QualityGrade(str, Enum):
    """Quality grades for commodities"""
    PREMIUM = "premium"
    GOOD = "good"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"

class DataSourceType(str, Enum):
    """Types of data sources"""
    GOVERNMENT_PORTAL = "government_portal"
    MANDI_COMMITTEE = "mandi_committee"
    TRADER_REPORT = "trader_report"
    AMBIENT_AI = "ambient_ai"
    MANUAL_ENTRY = "manual_entry"

class DataSource(BaseModel):
    """Data source configuration"""
    id: str
    name: str
    type: DataSourceType
    url: Optional[str] = None
    api_key: Optional[str] = None
    update_frequency: int = Field(..., description="Update frequency in minutes")
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)
    is_active: bool = True
    last_updated: Optional[datetime] = None

class GeoLocation(BaseModel):
    """Geographic location"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    district: Optional[str] = None
    state: str
    country: str = "India"

class MandiInfo(BaseModel):
    """Mandi (market) information"""
    id: str
    name: str
    location: GeoLocation
    operating_hours: Optional[str] = None
    facilities: List[str] = []
    average_daily_volume: Optional[float] = None
    reliability_score: float = Field(default=0.8, ge=0.0, le=1.0)
    contact_info: Optional[Dict[str, str]] = None

class PricePoint(BaseModel):
    """Individual price data point"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    commodity: str
    variety: Optional[str] = None
    price: float = Field(..., gt=0, description="Price per unit")
    unit: str = Field(default="quintal", description="Unit of measurement")
    quantity: Optional[float] = Field(None, gt=0, description="Quantity traded")
    quality: QualityGrade = QualityGrade.AVERAGE
    mandi_id: str
    timestamp: datetime
    source_id: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None

class PriceData(BaseModel):
    """Aggregated price data with market context"""
    commodity: str
    variety: Optional[str] = None
    current_price: float
    price_range: Dict[str, float]  # min, max, avg
    unit: str
    mandi: MandiInfo
    last_updated: datetime
    price_points: List[PricePoint] = []
    trend_indicator: Optional[str] = None  # "rising", "falling", "stable"
    volume_indicator: Optional[str] = None  # "high", "medium", "low"

class ValidationResult(BaseModel):
    """Data validation result"""
    is_valid: bool
    confidence_score: float
    issues: List[str] = []
    corrected_data: Optional[Dict[str, Any]] = None

class IngestionStats(BaseModel):
    """Statistics for data ingestion"""
    source_id: str
    records_processed: int
    records_validated: int
    records_stored: int
    errors: int
    processing_time: float
    timestamp: datetime

class PriceAlert(BaseModel):
    """Price alert configuration"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    commodity: str
    alert_type: str  # "price_drop", "price_rise", "msp_violation"
    threshold: float
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MarketTrend(BaseModel):
    """Market trend analysis"""
    commodity: str
    region: str
    trend_direction: str  # "bullish", "bearish", "sideways"
    strength: float = Field(..., ge=0.0, le=1.0)
    duration_days: int
    key_factors: List[str] = []
    confidence: float = Field(..., ge=0.0, le=1.0)
    analysis_date: datetime = Field(default_factory=datetime.utcnow)