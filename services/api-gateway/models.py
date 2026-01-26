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