"""
Configuration settings for API Gateway
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://mandi_user:mandi_pass@localhost:5432/mandi_ear"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Service URLs
    AMBIENT_AI_SERVICE_URL: str = "http://ambient-ai-service:8000"
    VOICE_PROCESSING_SERVICE_URL: str = "http://voice-processing-service:8000"
    PRICE_DISCOVERY_SERVICE_URL: str = "http://price-discovery-service:8000"
    NEGOTIATION_SERVICE_URL: str = "http://negotiation-intelligence-service:8000"
    CROP_PLANNING_SERVICE_URL: str = "http://crop-planning-service:8000"
    MSP_SERVICE_URL: str = "http://msp-enforcement-service:8000"
    ANTI_HOARDING_SERVICE_URL: str = "http://anti-hoarding-service:8000"
    USER_MANAGEMENT_SERVICE_URL: str = "http://user-management-service:8000"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8000"
    BENCHMARKING_SERVICE_URL: str = "http://benchmarking-service:8000"
    ACCESSIBILITY_SERVICE_URL: str = "http://accessibility-service:8000"
    OFFLINE_CACHE_SERVICE_URL: str = "http://offline-cache-service:8000"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()