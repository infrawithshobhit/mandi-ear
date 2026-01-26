"""
Data models for Notification Service
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, time
from enum import Enum
from uuid import UUID, uuid4

class AlertType(str, Enum):
    """Types of alerts"""
    PRICE_RISE = "price_rise"
    PRICE_DROP = "price_drop"
    PRICE_MOVEMENT = "price_movement"  # Generic price movement >10%
    MSP_VIOLATION = "msp_violation"
    WEATHER_EMERGENCY = "weather_emergency"
    WEATHER_WARNING = "weather_warning"
    MARKET_OPPORTUNITY = "market_opportunity"
    CROP_ADVISORY = "crop_advisory"
    CUSTOM_THRESHOLD = "custom_threshold"

class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    SMS = "sms"
    PUSH = "push"
    EMAIL = "email"
    VOICE = "voice"
    IN_APP = "in_app"
    WHATSAPP = "whatsapp"

class WeatherEventType(str, Enum):
    """Types of weather events"""
    HEAVY_RAIN = "heavy_rain"
    DROUGHT = "drought"
    HAILSTORM = "hailstorm"
    CYCLONE = "cyclone"
    FLOOD = "flood"
    EXTREME_HEAT = "extreme_heat"
    FROST = "frost"
    WIND_STORM = "wind_storm"

class ThresholdCondition(str, Enum):
    """Threshold condition types"""
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"
    PERCENTAGE_CHANGE = "percentage_change"
    ABSOLUTE_CHANGE = "absolute_change"

class AlertConfiguration(BaseModel):
    """User-defined alert configuration"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    alert_type: AlertType
    commodity: Optional[str] = None
    location: Optional[str] = None  # State, district, or specific mandi
    threshold_value: float
    threshold_condition: ThresholdCondition
    comparison_period: Optional[str] = "24h"  # 1h, 24h, 7d, etc.
    is_active: bool = True
    notification_channels: List[NotificationChannel] = [NotificationChannel.PUSH]
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    max_alerts_per_day: int = 10
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

    @validator('threshold_value')
    def validate_threshold(cls, v, values):
        """Validate threshold value based on alert type"""
        alert_type = values.get('alert_type')
        if alert_type in [AlertType.PRICE_MOVEMENT, AlertType.PRICE_RISE, AlertType.PRICE_DROP]:
            if v <= 0:
                raise ValueError("Price thresholds must be positive")
        return v

class UserAlertPreferences(BaseModel):
    """User notification preferences"""
    user_id: str
    preferred_channels: List[NotificationChannel] = [NotificationChannel.PUSH]
    preferred_language: str = "en"
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None
    emergency_override: bool = True  # Allow emergency alerts during quiet hours
    max_alerts_per_day: int = 20
    group_similar_alerts: bool = True
    alert_frequency: str = "immediate"  # immediate, hourly, daily
    location_preferences: List[str] = []  # Preferred locations for alerts
    commodity_preferences: List[str] = []  # Preferred commodities
    phone_number: Optional[str] = None
    email: Optional[str] = None
    whatsapp_number: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BaseAlert(BaseModel):
    """Base alert model"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    commodity: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class PriceMovementAlert(BaseAlert):
    """Price movement alert"""
    current_price: float
    previous_price: float
    percentage_change: float
    absolute_change: float
    mandi_name: Optional[str] = None
    price_trend: Optional[str] = None  # "rising", "falling", "volatile"
    market_context: Optional[Dict[str, Any]] = None

    def __init__(self, **data):
        # Calculate derived fields
        if 'current_price' in data and 'previous_price' in data:
            current = data['current_price']
            previous = data['previous_price']
            data['absolute_change'] = current - previous
            data['percentage_change'] = ((current - previous) / previous) * 100 if previous != 0 else 0
        super().__init__(**data)

class WeatherEmergencyAlert(BaseAlert):
    """Weather emergency alert"""
    weather_event: WeatherEventType
    intensity: str  # "low", "moderate", "high", "extreme"
    start_time: datetime
    end_time: Optional[datetime] = None
    affected_areas: List[str] = []
    impact_assessment: Optional[str] = None
    recommended_actions: List[str] = []
    weather_data: Optional[Dict[str, Any]] = None

class CustomThresholdAlert(BaseAlert):
    """Custom user-defined threshold alert"""
    threshold_config_id: str
    threshold_value: float
    current_value: float
    condition_met: str
    trigger_data: Dict[str, Any]

class NotificationDelivery(BaseModel):
    """Notification delivery record"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    alert_id: str
    user_id: str
    channel: NotificationChannel
    status: str  # "pending", "sent", "delivered", "failed", "read"
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Optional[Dict[str, Any]] = None

class AlertHistory(BaseModel):
    """Alert history record"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    commodity: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime
    channels_sent: List[NotificationChannel] = []
    was_read: bool = False
    was_acknowledged: bool = False
    response_time: Optional[float] = None  # Time to read in seconds
    metadata: Optional[Dict[str, Any]] = None

class AlertStatistics(BaseModel):
    """Alert statistics for monitoring"""
    user_id: str
    date: datetime
    total_alerts: int = 0
    alerts_by_type: Dict[AlertType, int] = {}
    alerts_by_severity: Dict[AlertSeverity, int] = {}
    alerts_by_channel: Dict[NotificationChannel, int] = {}
    read_rate: float = 0.0
    acknowledgment_rate: float = 0.0
    average_response_time: Optional[float] = None

class WeatherData(BaseModel):
    """Weather data for monitoring"""
    location: str
    timestamp: datetime
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    rainfall: Optional[float] = None
    wind_speed: Optional[float] = None
    wind_direction: Optional[str] = None
    pressure: Optional[float] = None
    visibility: Optional[float] = None
    weather_condition: Optional[str] = None
    alerts: List[str] = []
    forecast: Optional[Dict[str, Any]] = None

class PriceData(BaseModel):
    """Price data for monitoring"""
    commodity: str
    location: str
    current_price: float
    previous_price: float
    timestamp: datetime
    price_change: float
    percentage_change: float
    volume: Optional[float] = None
    quality: Optional[str] = None
    source: str
    confidence: float = 0.8

class AlertConfigurationResponse(BaseModel):
    """Response for alert configuration"""
    alert_id: str
    success: bool
    message: str
    configuration: Optional[AlertConfiguration] = None

class AlertToggleResponse(BaseModel):
    """Response for alert toggle"""
    alert_id: str
    is_active: bool
    success: bool
    message: str

class MonitoringStatus(BaseModel):
    """Monitoring service status"""
    service_name: str
    is_active: bool
    last_check_time: Optional[datetime] = None
    alerts_sent_today: int = 0
    errors_today: int = 0
    uptime_percentage: float = 100.0
    last_error: Optional[str] = None

class NotificationTemplate(BaseModel):
    """Notification message template"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    alert_type: AlertType
    severity: AlertSeverity
    language: str = "en"
    channel: NotificationChannel
    title_template: str
    message_template: str
    variables: List[str] = []  # Template variables like {commodity}, {price}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class AlertRule(BaseModel):
    """Alert rule for automated alert generation"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    alert_type: AlertType
    conditions: List[Dict[str, Any]]  # Complex conditions
    actions: List[Dict[str, Any]]  # Actions to take when conditions are met
    is_active: bool = True
    priority: int = 1  # Higher number = higher priority
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class BulkAlertRequest(BaseModel):
    """Request for sending bulk alerts"""
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    target_users: List[str]  # User IDs
    target_criteria: Optional[Dict[str, Any]] = None  # Location, commodity filters
    channels: List[NotificationChannel] = [NotificationChannel.PUSH]
    schedule_time: Optional[datetime] = None  # For scheduled alerts
    metadata: Optional[Dict[str, Any]] = None

class AlertAnalytics(BaseModel):
    """Alert analytics data"""
    period_start: datetime
    period_end: datetime
    total_alerts: int
    alerts_by_type: Dict[str, int]
    alerts_by_severity: Dict[str, int]
    user_engagement: Dict[str, float]  # read_rate, response_time, etc.
    channel_performance: Dict[str, Dict[str, float]]  # delivery rates by channel
    top_commodities: List[Dict[str, Any]]
    top_locations: List[Dict[str, Any]]
    trends: Dict[str, Any]