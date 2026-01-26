"""
Data models for MSP Enforcement Service
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from uuid import UUID, uuid4

class MSPSeason(str, Enum):
    """MSP seasons"""
    KHARIF = "kharif"
    RABI = "rabi"
    SUMMER = "summer"

class MSPCommodityType(str, Enum):
    """Types of MSP commodities"""
    CEREALS = "cereals"
    PULSES = "pulses"
    OILSEEDS = "oilseeds"
    COMMERCIAL_CROPS = "commercial_crops"

class ViolationType(str, Enum):
    """Types of MSP violations"""
    BELOW_MSP = "below_msp"
    PROCUREMENT_UNAVAILABLE = "procurement_unavailable"
    QUALITY_ISSUES = "quality_issues"

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MSPRate(BaseModel):
    """MSP rate for a commodity"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    commodity: str
    variety: Optional[str] = None
    season: MSPSeason
    crop_year: str  # e.g., "2023-24"
    msp_price: float = Field(..., gt=0, description="MSP price per quintal")
    unit: str = Field(default="quintal")
    commodity_type: MSPCommodityType
    effective_date: date
    expiry_date: Optional[date] = None
    announcement_date: date
    source_document: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ProcurementCenter(BaseModel):
    """Government procurement center information"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    center_type: str  # "FCI", "State Agency", "Cooperative"
    address: str
    district: str
    state: str
    pincode: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_person: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    operating_hours: Optional[str] = None
    commodities_accepted: List[str] = []
    storage_capacity: Optional[float] = None
    current_stock: Optional[float] = None
    is_operational: bool = True
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class MSPViolation(BaseModel):
    """MSP violation record"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    commodity: str
    variety: Optional[str] = None
    mandi_id: str
    mandi_name: str
    district: str
    state: str
    market_price: float
    msp_price: float
    price_difference: float
    violation_percentage: float
    violation_type: ViolationType
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    severity: AlertSeverity
    is_resolved: bool = False
    resolution_notes: Optional[str] = None
    resolved_at: Optional[datetime] = None
    evidence: Optional[Dict[str, Any]] = None

class MSPAlert(BaseModel):
    """MSP violation alert"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    violation_id: str
    farmer_id: Optional[str] = None
    alert_type: str = "msp_violation"
    title: str
    message: str
    severity: AlertSeverity
    commodity: str
    location: str
    suggested_actions: List[str] = []
    alternative_centers: List[str] = []
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = False
    is_acknowledged: bool = False

class MSPComparisonResult(BaseModel):
    """Result of MSP vs market price comparison"""
    commodity: str
    variety: Optional[str] = None
    mandi_id: str
    mandi_name: str
    location: str
    market_price: float
    msp_price: float
    price_difference: float
    compliance_status: str  # "compliant", "violation", "warning"
    violation_percentage: Optional[float] = None
    comparison_timestamp: datetime = Field(default_factory=datetime.utcnow)
    data_confidence: float = Field(default=0.8, ge=0.0, le=1.0)

class GovernmentDataSource(BaseModel):
    """Government data source for MSP rates"""
    id: str
    name: str
    url: str
    api_endpoint: Optional[str] = None
    update_frequency: int = Field(..., description="Update frequency in hours")
    last_sync: Optional[datetime] = None
    is_active: bool = True
    reliability_score: float = Field(default=0.9, ge=0.0, le=1.0)
    auth_required: bool = False
    api_key: Optional[str] = None

class MSPMonitoringStats(BaseModel):
    """Statistics for MSP monitoring"""
    total_commodities_monitored: int
    total_mandis_monitored: int
    violations_detected_today: int
    violations_resolved_today: int
    average_compliance_rate: float
    most_violated_commodity: Optional[str] = None
    most_compliant_state: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class AlternativeSuggestion(BaseModel):
    """Alternative market/procurement center suggestion"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    commodity: str
    original_location: str
    suggested_center_id: str
    suggested_center_name: str
    suggested_location: str
    distance_km: float
    price_offered: float
    price_advantage: float
    transportation_cost: Optional[float] = None
    net_benefit: Optional[float] = None
    contact_info: Optional[Dict[str, str]] = None
    directions: Optional[str] = None
    estimated_travel_time: Optional[str] = None
    suggestion_reason: str
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MSPComplianceReport(BaseModel):
    """MSP compliance report for authorities"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    report_period_start: date
    report_period_end: date
    region: str  # state, district, or "national"
    total_violations: int
    violations_by_commodity: Dict[str, int]
    violations_by_location: Dict[str, int]
    average_violation_percentage: float
    most_affected_farmers: Optional[int] = None
    estimated_farmer_losses: Optional[float] = None
    recommendations: List[str] = []
    evidence_files: List[str] = []
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str = "MSP Enforcement System"
    report_status: str = "draft"  # "draft", "submitted", "acknowledged"