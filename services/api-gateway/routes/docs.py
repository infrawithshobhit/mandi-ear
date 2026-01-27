"""
API Documentation and Testing Routes
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import structlog
from typing import Dict, List, Any

from auth.dependencies import get_current_user
from models import UserResponse

logger = structlog.get_logger()
router = APIRouter()

@router.get("/endpoints")
async def list_api_endpoints():
    """List all available API endpoints with descriptions"""
    
    endpoints = {
        "authentication": {
            "POST /auth/register": "Register new user",
            "POST /auth/login": "User login",
            "GET /auth/me": "Get current user info"
        },
        "ambient_ai": {
            "POST /api/v1/ambient/process": "Process ambient audio for market intelligence",
            "GET /api/v1/ambient/intelligence": "Get recent market intelligence"
        },
        "voice_processing": {
            "POST /api/v1/voice/transcribe": "Transcribe voice input to text",
            "POST /api/v1/voice/synthesize": "Convert text to speech"
        },
        "price_discovery": {
            "GET /api/v1/prices/current": "Get current market prices",
            "GET /api/v1/prices/trends": "Get price trends for commodity",
            "GET /api/v1/prices/cross-mandi": "Get cross-mandi price comparison"
        },
        "negotiation": {
            "POST /api/v1/negotiation/analyze": "Analyze negotiation context",
            "GET /api/v1/negotiation/strategies": "Get negotiation strategies"
        },
        "crop_planning": {
            "POST /api/v1/crop-planning/recommend": "Get crop recommendations",
            "GET /api/v1/crop-planning/weather": "Get weather forecast"
        },
        "msp_enforcement": {
            "GET /api/v1/msp/rates": "Get current MSP rates",
            "GET /api/v1/msp/violations": "Get MSP violations"
        },
        "anti_hoarding": {
            "GET /api/v1/anti-hoarding/alerts": "Get hoarding alerts",
            "GET /api/v1/anti-hoarding/analysis": "Get market manipulation analysis"
        },
        "user_management": {
            "GET /api/v1/user/profile": "Get user profile",
            "PUT /api/v1/user/profile": "Update user profile"
        },
        "notifications": {
            "GET /api/v1/notifications": "Get user notifications",
            "POST /api/v1/notifications/preferences": "Update notification preferences"
        }
    }
    
    return {
        "title": "MANDI EAR™ API Documentation",
        "version": "1.0.0",
        "description": "India's first ambient AI-powered agricultural intelligence platform",
        "endpoints": endpoints
    }

@router.get("/test-data")
async def get_test_data():
    """Get sample test data for API testing"""
    
    test_data = {
        "sample_audio_request": {
            "audio_data": "base64_encoded_audio_data_here",
            "format": "wav",
            "sample_rate": 16000,
            "language": "hi"
        },
        "sample_voice_transcription": {
            "text": "आज गेहूं का भाव क्या है?",
            "language": "hi",
            "confidence": 0.95
        },
        "sample_price_query": {
            "commodity": "wheat",
            "location": "Delhi",
            "quantity": 100,
            "unit": "quintal"
        },
        "sample_crop_planning_request": {
            "location": {
                "latitude": 28.6139,
                "longitude": 77.2090
            },
            "farm_area": 5.0,
            "soil_type": "loamy",
            "irrigation_type": "drip",
            "season": "kharif"
        },
        "sample_negotiation_context": {
            "commodity": "rice",
            "quantity": 50,
            "current_offer": 2000,
            "market_price": 2200,
            "buyer_urgency": "medium"
        }
    }
    
    return {
        "message": "Sample test data for MANDI EAR™ API",
        "test_data": test_data
    }

@router.post("/test/echo")
async def echo_test(request_data: Dict[str, Any]):
    """Echo test endpoint for API validation"""
    
    return {
        "message": "Echo test successful",
        "received_data": request_data,
        "timestamp": "2024-01-01T00:00:00Z"
    }

@router.get("/test/auth")
async def test_authentication(current_user: UserResponse = Depends(get_current_user)):
    """Test authentication endpoint"""
    
    return {
        "message": "Authentication test successful",
        "user": {
            "id": str(current_user.id),
            "name": current_user.name,
            "phone_number": current_user.phone_number,
            "preferred_language": current_user.preferred_language
        }
    }

@router.get("/test/services")
async def test_service_connectivity():
    """Test connectivity to all microservices"""
    
    # This would normally test actual service connectivity
    # For now, return mock status
    services_status = {
        "ambient-ai-service": "healthy",
        "voice-processing-service": "healthy", 
        "price-discovery-service": "healthy",
        "negotiation-intelligence-service": "healthy",
        "crop-planning-service": "healthy",
        "msp-enforcement-service": "healthy",
        "anti-hoarding-service": "healthy",
        "user-management-service": "healthy",
        "notification-service": "healthy",
        "benchmarking-service": "healthy",
        "accessibility-service": "healthy",
        "offline-cache-service": "healthy"
    }
    
    return {
        "message": "Service connectivity test",
        "services": services_status,
        "overall_status": "healthy"
    }

@router.get("/schema")
async def get_api_schema():
    """Get API schema for client generation"""
    
    schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "MANDI EAR™ API",
            "version": "1.0.0",
            "description": "Agricultural Intelligence Platform API"
        },
        "servers": [
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://api.mandiear.com", "description": "Production server"}
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "security": [{"bearerAuth": []}]
    }
    
    return schema