"""
Pydantic models for API Gateway
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import re

class UserBase(BaseModel):
    phone_number: str = Field(..., description="User's phone number")
    name: str = Field(..., description="User's full name")
    preferred_language: str = Field(default="hi", description="Preferred language code")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Indian phone number validation
        pattern = r'^(\+91|91)?[6-9]\d{9}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid Indian phone number format')
        return v
    
    @validator('preferred_language')
    def validate_language(cls, v):
        # Supported Indian languages
        supported_languages = [
            'hi', 'en', 'ta', 'te', 'bn', 'mr', 'gu', 'kn', 'ml', 'pa', 'or'
        ]
        if v not in supported_languages:
            raise ValueError(f'Language {v} not supported')
        return v

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    phone_number: str
    # In production, this would be OTP-based authentication
    otp: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[UUID] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    services: dict

class LocationData(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    
class FarmData(BaseModel):
    location: LocationData
    area: float = Field(..., gt=0, description="Farm area in acres")
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None

class UserPreferences(BaseModel):
    alert_thresholds: Optional[dict] = None
    notification_preferences: Optional[dict] = None
    price_floors: Optional[dict] = None

# Request validation models
class AudioProcessingRequest(BaseModel):
    audio_data: str = Field(..., description="Base64 encoded audio data")
    format: str = Field(default="wav", description="Audio format")
    sample_rate: int = Field(default=16000, description="Audio sample rate")
    language: Optional[str] = Field(default=None, description="Expected language")

class VoiceTranscriptionRequest(BaseModel):
    audio_data: str = Field(..., description="Base64 encoded audio data")
    language: Optional[str] = Field(default=None, description="Language code")

class TextToSpeechRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    language: str = Field(default="hi", description="Language code")
    voice_type: Optional[str] = Field(default="female", description="Voice type")

class PriceQueryRequest(BaseModel):
    commodity: str = Field(..., description="Commodity name")
    location: Optional[str] = Field(default=None, description="Location")
    quantity: Optional[float] = Field(default=None, description="Quantity")
    unit: Optional[str] = Field(default="quintal", description="Unit of measurement")

class NegotiationAnalysisRequest(BaseModel):
    commodity: str = Field(..., description="Commodity being negotiated")
    quantity: float = Field(..., description="Quantity")
    current_offer: float = Field(..., description="Current price offer")
    market_price: Optional[float] = Field(default=None, description="Current market price")
    buyer_urgency: Optional[str] = Field(default="medium", description="Buyer urgency level")

class CropPlanningRequest(BaseModel):
    location: LocationData = Field(..., description="Farm location")
    farm_area: float = Field(..., gt=0, description="Farm area in acres")
    soil_type: Optional[str] = Field(default=None, description="Soil type")
    irrigation_type: Optional[str] = Field(default=None, description="Irrigation type")
    season: str = Field(..., description="Planting season")
    budget: Optional[float] = Field(default=None, description="Available budget")

class NotificationPreferencesRequest(BaseModel):
    price_alerts: bool = Field(default=True, description="Enable price alerts")
    weather_alerts: bool = Field(default=True, description="Enable weather alerts")
    msp_alerts: bool = Field(default=True, description="Enable MSP alerts")
    sms_enabled: bool = Field(default=True, description="Enable SMS notifications")
    voice_enabled: bool = Field(default=False, description="Enable voice notifications")
    app_enabled: bool = Field(default=True, description="Enable app notifications")

# Response models
class APIResponse(BaseModel):
    success: bool = Field(default=True, description="Request success status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    timestamp: Optional[str] = Field(default=None, description="Response timestamp")

class ErrorResponse(BaseModel):
    success: bool = Field(default=False, description="Request success status")
    error: Dict[str, Any] = Field(..., description="Error details")
    timestamp: str = Field(..., description="Error timestamp")