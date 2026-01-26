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
    USER_MANAGEMENT_SERVICE_URL: str = "http://user-management-service:8000"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()