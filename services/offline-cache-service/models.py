"""
Data models for offline cache service
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class PriorityLevel(str, Enum):
    """Priority levels for cached data"""
    CRITICAL = "critical"      # Essential for basic functionality
    HIGH = "high"             # Important for user experience
    MEDIUM = "medium"         # Useful but not essential
    LOW = "low"              # Nice to have

class DataType(str, Enum):
    """Types of cached data"""
    PRICE_DATA = "price_data"
    MANDI_INFO = "mandi_info"
    WEATHER_DATA = "weather_data"
    MSP_RATES = "msp_rates"
    USER_PREFERENCES = "user_preferences"
    CROP_RECOMMENDATIONS = "crop_recommendations"
    MARKET_TRENDS = "market_trends"

class SyncStatus(str, Enum):
    """Synchronization status"""
    IDLE = "idle"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class ConnectivityLevel(str, Enum):
    """Network connectivity levels"""
    OFFLINE = "offline"
    POOR = "poor"           # < 1 Mbps
    MODERATE = "moderate"   # 1-5 Mbps
    GOOD = "good"          # > 5 Mbps

class CachedData(BaseModel):
    """Model for cached data entries"""
    id: str
    data_type: DataType
    content: Dict[str, Any]
    priority: PriorityLevel
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    size_bytes: int
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class OfflineQuery(BaseModel):
    """Model for offline query requests"""
    query_type: str
    parameters: Dict[str, Any]
    user_id: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    priority: PriorityLevel = PriorityLevel.MEDIUM
    created_at: datetime = Field(default_factory=datetime.now)

class SyncConfiguration(BaseModel):
    """Synchronization configuration"""
    sync_interval_minutes: int = 15
    priority_data_interval_minutes: int = 5
    max_cache_size_mb: int = 100
    max_age_hours: Dict[DataType, int] = Field(default_factory=lambda: {
        DataType.PRICE_DATA: 6,
        DataType.MANDI_INFO: 24,
        DataType.WEATHER_DATA: 3,
        DataType.MSP_RATES: 168,  # 1 week
        DataType.USER_PREFERENCES: 720,  # 30 days
        DataType.CROP_RECOMMENDATIONS: 24,
        DataType.MARKET_TRENDS: 12
    })
    connectivity_thresholds: Dict[ConnectivityLevel, float] = Field(default_factory=lambda: {
        ConnectivityLevel.POOR: 1.0,
        ConnectivityLevel.MODERATE: 5.0,
        ConnectivityLevel.GOOD: float('inf')
    })

class CacheStatistics(BaseModel):
    """Cache usage statistics"""
    total_entries: int
    total_size_mb: float
    entries_by_type: Dict[DataType, int]
    size_by_type: Dict[DataType, float]
    hit_rate: float
    miss_rate: float
    last_sync: Optional[datetime] = None
    sync_success_rate: float
    expired_entries: int
    most_accessed: List[Dict[str, Any]]

class EssentialDataPackage(BaseModel):
    """Essential data package for offline use"""
    location: Dict[str, float]  # lat, lng
    radius_km: float
    commodities: List[str]
    price_data: List[Dict[str, Any]]
    mandi_info: List[Dict[str, Any]]
    msp_rates: Dict[str, float]
    weather_summary: Dict[str, Any]
    last_updated: datetime
    data_freshness: Dict[str, datetime]
    estimated_validity_hours: int

class SyncResult(BaseModel):
    """Result of a synchronization operation"""
    sync_id: str
    status: SyncStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    items_synced: int = 0
    items_failed: int = 0
    bytes_transferred: int = 0
    errors: List[str] = Field(default_factory=list)
    data_types_synced: List[DataType] = Field(default_factory=list)

class OfflinePreparation(BaseModel):
    """Offline data preparation request"""
    preparation_id: str
    user_location: Dict[str, float]
    commodities: List[str]
    radius_km: float
    status: str  # preparing, completed, failed
    progress_percentage: float = 0.0
    estimated_completion: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    data_size_mb: float = 0.0
    error_message: Optional[str] = None

class NetworkOptimization(BaseModel):
    """Network optimization settings"""
    connectivity_level: ConnectivityLevel
    max_request_size_kb: int
    request_timeout_seconds: int
    retry_attempts: int
    compression_enabled: bool
    priority_data_only: bool

class DataPriority(BaseModel):
    """Data priority configuration"""
    data_type: DataType
    priority: PriorityLevel
    max_age_hours: int
    size_limit_mb: float
    refresh_frequency_minutes: int
    essential_for_offline: bool

class CacheEntry(BaseModel):
    """Individual cache entry"""
    key: str
    data_type: DataType
    content: Union[Dict[str, Any], List[Any], str, int, float]
    priority: PriorityLevel
    created_at: datetime
    expires_at: Optional[datetime] = None
    size_bytes: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class QueryResult(BaseModel):
    """Result of a cached query"""
    query_id: str
    data: Union[Dict[str, Any], List[Any]]
    source: str  # "cache" or "live"
    freshness: datetime
    confidence: float  # 0.0 to 1.0
    partial_result: bool = False
    missing_data: List[str] = Field(default_factory=list)