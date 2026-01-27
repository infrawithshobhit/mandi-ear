"""
Service routing for API Gateway
Centralized routing to all microservices
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
import httpx
import structlog
from typing import Any, Dict
import json

from config import settings
from auth.dependencies import get_current_user
from models import UserResponse

logger = structlog.get_logger()
router = APIRouter()

# HTTP client for service communication
http_client = httpx.AsyncClient(timeout=30.0)

async def proxy_request(
    service_url: str,
    path: str,
    method: str,
    headers: Dict[str, str] = None,
    params: Dict[str, Any] = None,
    json_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Proxy request to microservice"""
    
    url = f"{service_url}{path}"
    request_headers = headers or {}
    
    try:
        if method.upper() == "GET":
            response = await http_client.get(url, headers=request_headers, params=params)
        elif method.upper() == "POST":
            response = await http_client.post(url, headers=request_headers, json=json_data)
        elif method.upper() == "PUT":
            response = await http_client.put(url, headers=request_headers, json=json_data)
        elif method.upper() == "DELETE":
            response = await http_client.delete(url, headers=request_headers)
        else:
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail=f"Method {method} not supported"
            )
        
        response.raise_for_status()
        return response.json()
        
    except httpx.HTTPStatusError as e:
        logger.error(
            "Service request failed",
            service_url=service_url,
            path=path,
            status_code=e.response.status_code,
            error=str(e)
        )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Service request failed: {e.response.text}"
        )
    except httpx.RequestError as e:
        logger.error(
            "Service connection failed",
            service_url=service_url,
            path=path,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable"
        )

# Ambient AI Service Routes
@router.post("/ambient/process")
async def process_ambient_audio(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Process ambient audio for market intelligence"""
    body = await request.json()
    
    headers = {
        "X-User-ID": str(current_user.id),
        "X-User-Language": current_user.preferred_language
    }
    
    return await proxy_request(
        settings.AMBIENT_AI_SERVICE_URL,
        "/process",
        "POST",
        headers=headers,
        json_data=body
    )

@router.get("/ambient/intelligence")
async def get_market_intelligence(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get recent market intelligence"""
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.AMBIENT_AI_SERVICE_URL,
        "/intelligence",
        "GET",
        headers=headers
    )

# Voice Processing Service Routes
@router.post("/voice/transcribe")
async def transcribe_voice(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Transcribe voice input"""
    body = await request.json()
    
    headers = {
        "X-User-ID": str(current_user.id),
        "X-User-Language": current_user.preferred_language
    }
    
    return await proxy_request(
        settings.VOICE_PROCESSING_SERVICE_URL,
        "/transcribe",
        "POST",
        headers=headers,
        json_data=body
    )

@router.post("/voice/synthesize")
async def synthesize_speech(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Synthesize speech from text"""
    body = await request.json()
    
    headers = {
        "X-User-ID": str(current_user.id),
        "X-User-Language": current_user.preferred_language
    }
    
    return await proxy_request(
        settings.VOICE_PROCESSING_SERVICE_URL,
        "/synthesize",
        "POST",
        headers=headers,
        json_data=body
    )

# Price Discovery Service Routes
@router.get("/prices/current")
async def get_current_prices(
    commodity: str = None,
    location: str = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get current market prices"""
    params = {}
    if commodity:
        params["commodity"] = commodity
    if location:
        params["location"] = location
    
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.PRICE_DISCOVERY_SERVICE_URL,
        "/prices/current",
        "GET",
        headers=headers,
        params=params
    )

@router.get("/prices/trends")
async def get_price_trends(
    commodity: str,
    days: int = 30,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get price trends for commodity"""
    params = {"commodity": commodity, "days": days}
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.PRICE_DISCOVERY_SERVICE_URL,
        "/prices/trends",
        "GET",
        headers=headers,
        params=params
    )

@router.get("/prices/cross-mandi")
async def get_cross_mandi_prices(
    commodity: str,
    radius_km: int = 500,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get cross-mandi price comparison"""
    params = {"commodity": commodity, "radius_km": radius_km}
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.PRICE_DISCOVERY_SERVICE_URL,
        "/prices/cross-mandi",
        "GET",
        headers=headers,
        params=params
    )

# Negotiation Intelligence Service Routes
@router.post("/negotiation/analyze")
async def analyze_negotiation_context(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Analyze negotiation context and provide guidance"""
    body = await request.json()
    
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.NEGOTIATION_SERVICE_URL,
        "/analyze",
        "POST",
        headers=headers,
        json_data=body
    )

@router.get("/negotiation/strategies")
async def get_negotiation_strategies(
    commodity: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get negotiation strategies for commodity"""
    params = {"commodity": commodity}
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.NEGOTIATION_SERVICE_URL,
        "/strategies",
        "GET",
        headers=headers,
        params=params
    )

# Crop Planning Service Routes
@router.post("/crop-planning/recommend")
async def get_crop_recommendations(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get crop planning recommendations"""
    body = await request.json()
    
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.CROP_PLANNING_SERVICE_URL,
        "/recommend",
        "POST",
        headers=headers,
        json_data=body
    )

@router.get("/crop-planning/weather")
async def get_weather_forecast(
    latitude: float,
    longitude: float,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get weather forecast for location"""
    params = {"latitude": latitude, "longitude": longitude}
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.CROP_PLANNING_SERVICE_URL,
        "/weather",
        "GET",
        headers=headers,
        params=params
    )

# MSP Enforcement Service Routes
@router.get("/msp/rates")
async def get_msp_rates(
    commodity: str = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get current MSP rates"""
    params = {}
    if commodity:
        params["commodity"] = commodity
    
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.MSP_SERVICE_URL,
        "/rates",
        "GET",
        headers=headers,
        params=params
    )

@router.get("/msp/violations")
async def get_msp_violations(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get MSP violations in user's area"""
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.MSP_SERVICE_URL,
        "/violations",
        "GET",
        headers=headers
    )

# Anti-Hoarding Service Routes
@router.get("/anti-hoarding/alerts")
async def get_hoarding_alerts(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get anti-hoarding alerts"""
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.ANTI_HOARDING_SERVICE_URL,
        "/alerts",
        "GET",
        headers=headers
    )

@router.get("/anti-hoarding/analysis")
async def get_market_analysis(
    commodity: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get market manipulation analysis"""
    params = {"commodity": commodity}
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.ANTI_HOARDING_SERVICE_URL,
        "/analysis",
        "GET",
        headers=headers,
        params=params
    )

# User Management Service Routes
@router.get("/user/profile")
async def get_user_profile(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user profile"""
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.USER_MANAGEMENT_SERVICE_URL,
        "/profile",
        "GET",
        headers=headers
    )

@router.put("/user/profile")
async def update_user_profile(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update user profile"""
    body = await request.json()
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.USER_MANAGEMENT_SERVICE_URL,
        "/profile",
        "PUT",
        headers=headers,
        json_data=body
    )

# Notification Service Routes
@router.get("/notifications")
async def get_notifications(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user notifications"""
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.NOTIFICATION_SERVICE_URL,
        "/notifications",
        "GET",
        headers=headers
    )

@router.post("/notifications/preferences")
async def update_notification_preferences(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update notification preferences"""
    body = await request.json()
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.NOTIFICATION_SERVICE_URL,
        "/preferences",
        "POST",
        headers=headers,
        json_data=body
    )

# Benchmarking Service Routes
@router.get("/benchmarking/performance")
async def get_farmer_performance(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get farmer performance analytics"""
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.BENCHMARKING_SERVICE_URL,
        "/performance",
        "GET",
        headers=headers
    )

@router.post("/benchmarking/set-floor")
async def set_price_floor(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Set minimum price floor for farmer"""
    body = await request.json()
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.BENCHMARKING_SERVICE_URL,
        "/set-floor",
        "POST",
        headers=headers,
        json_data=body
    )

# Accessibility Service Routes
@router.get("/accessibility/features")
async def get_accessibility_features(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get accessibility features for user"""
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.ACCESSIBILITY_SERVICE_URL,
        "/features",
        "GET",
        headers=headers
    )

@router.post("/accessibility/preferences")
async def update_accessibility_preferences(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update accessibility preferences"""
    body = await request.json()
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.ACCESSIBILITY_SERVICE_URL,
        "/preferences",
        "POST",
        headers=headers,
        json_data=body
    )

# Offline Cache Service Routes
@router.get("/offline/sync")
async def sync_offline_data(
    current_user: UserResponse = Depends(get_current_user)
):
    """Sync offline data for user"""
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.OFFLINE_CACHE_SERVICE_URL,
        "/sync",
        "GET",
        headers=headers
    )

@router.post("/offline/cache")
async def cache_data_for_offline(
    request: Request,
    current_user: UserResponse = Depends(get_current_user)
):
    """Cache data for offline access"""
    body = await request.json()
    headers = {"X-User-ID": str(current_user.id)}
    
    return await proxy_request(
        settings.OFFLINE_CACHE_SERVICE_URL,
        "/cache",
        "POST",
        headers=headers,
        json_data=body
    )