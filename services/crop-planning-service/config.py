"""
Configuration settings for crop planning service
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    weather_api_key: Optional[str] = None
    
    # Database URLs
    postgres_url: str = "postgresql://user:password@localhost:5432/mandi_ear"
    mongodb_url: str = "mongodb://localhost:27017/mandi_ear"
    redis_url: str = "redis://localhost:6379"
    influxdb_url: str = "http://localhost:8086"
    
    # Service URLs
    price_discovery_service_url: str = "http://localhost:8001"
    voice_processing_service_url: str = "http://localhost:8002"
    
    # External APIs
    government_data_api_url: str = "https://api.data.gov.in"
    
    # Logging
    log_level: str = "INFO"
    
    # Development settings
    debug: bool = False
    
    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    """Get application settings"""
    return Settings()