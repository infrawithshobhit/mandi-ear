"""
Property-Based Test for Cross-Platform Consistency
Feature: mandi-ear, Property 21: Cross-Platform Consistency

**Validates: Requirements 10.1**

This test validates that the MANDI EAR platform provides identical functionality 
across web browsers and mobile applications (Android/iOS).
"""

import pytest
from hypothesis import given, strategies as st, settings
import httpx
import asyncio
from typing import Dict, Any, List
import json

# Test configuration
API_BASE_URL = "http://localhost:8000"
MOBILE_USER_AGENT = "MandiEar-Mobile/1.0.0 (Android 13)"
WEB_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

class PlatformClient:
    """Client to simulate different platform requests"""
    
    def __init__(self, user_agent: str, platform: str):
        self.user_agent = user_agent
        self.platform = platform
        self.headers = {
            "User-Agent": user_agent,
            "X-Platform": platform,
            "Content-Type": "application/json"
        }
    
    async def make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with platform-specific headers"""
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=f"{API_BASE_URL}{endpoint}",
                headers=self.headers,
                **kwargs
            )
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "data": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                "platform": self.platform
            }

# Strategy for generating API endpoints to test
@st.composite
def api_endpoints(draw):
    """Generate API endpoints for testing"""
    endpoints = [
        "/",
        "/health",
        "/auth/register",
        "/auth/login"
    ]
    return draw(st.sampled_from(endpoints))

# Strategy for generating user registration data
@st.composite
def user_registration_data(draw):
    """Generate user registration data"""
    phone_numbers = [
        "+919876543210",
        "919876543211", 
        "8765432109",
        "7654321098"
    ]
    names = ["राम शर्मा", "Priya Patel", "Mohammed Khan", "Lakshmi Reddy"]
    languages = ["hi", "en", "ta", "te", "bn", "mr", "gu"]
    
    return {
        "phone_number": draw(st.sampled_from(phone_numbers)),
        "name": draw(st.sampled_from(names)),
        "preferred_language": draw(st.sampled_from(languages))
    }

@pytest.mark.asyncio
@given(endpoint=api_endpoints())
@settings(max_examples=20, deadline=10000)
async def test_cross_platform_api_consistency(endpoint: str):
    """
    Property 21: Cross-Platform Consistency
    
    For any API endpoint, responses should be identical across web and mobile platforms.
    This ensures that the core functionality works consistently regardless of the client platform.
    """
    
    # Create clients for different platforms
    web_client = PlatformClient(WEB_USER_AGENT, "web")
    mobile_client = PlatformClient(MOBILE_USER_AGENT, "mobile")
    
    try:
        # Make requests from both platforms
        web_response = await web_client.make_request("GET", endpoint)
        mobile_response = await mobile_client.make_request("GET", endpoint)
        
        # Core consistency checks
        assert web_response["status_code"] == mobile_response["status_code"], \
            f"Status codes differ: web={web_response['status_code']}, mobile={mobile_response['status_code']}"
        
        # Response data should be identical (excluding platform-specific headers)
        web_data = web_response["data"]
        mobile_data = mobile_response["data"]
        
        if isinstance(web_data, dict) and isinstance(mobile_data, dict):
            # For JSON responses, core data should be identical
            assert web_data == mobile_data, \
                f"Response data differs between platforms: web={web_data}, mobile={mobile_data}"
        
        # Content-Type should be consistent
        web_content_type = web_response["headers"].get("content-type", "").split(";")[0]
        mobile_content_type = mobile_response["headers"].get("content-type", "").split(";")[0]
        
        assert web_content_type == mobile_content_type, \
            f"Content types differ: web={web_content_type}, mobile={mobile_content_type}"
            
    except httpx.ConnectError:
        # Skip test if service is not running
        pytest.skip("API service not available for testing")
    except Exception as e:
        pytest.fail(f"Cross-platform consistency test failed: {str(e)}")

@pytest.mark.asyncio
@given(user_data=user_registration_data())
@settings(max_examples=10, deadline=15000)
async def test_cross_platform_user_registration_consistency(user_data: Dict[str, str]):
    """
    Property 21: Cross-Platform Consistency - User Registration
    
    For any user registration data, the registration process should work identically
    across web and mobile platforms, returning the same user data structure.
    """
    
    web_client = PlatformClient(WEB_USER_AGENT, "web")
    mobile_client = PlatformClient(MOBILE_USER_AGENT, "mobile")
    
    try:
        # Test registration from web platform
        web_response = await web_client.make_request(
            "POST", 
            "/auth/register",
            json=user_data
        )
        
        # Modify phone number slightly for mobile test to avoid duplicate user error
        mobile_user_data = user_data.copy()
        mobile_user_data["phone_number"] = mobile_user_data["phone_number"].replace("0", "1", 1)
        
        # Test registration from mobile platform
        mobile_response = await mobile_client.make_request(
            "POST",
            "/auth/register", 
            json=mobile_user_data
        )
        
        # Both should have same status code (success or failure)
        assert web_response["status_code"] == mobile_response["status_code"], \
            f"Registration status codes differ: web={web_response['status_code']}, mobile={mobile_response['status_code']}"
        
        # If successful, response structure should be identical
        if web_response["status_code"] == 200:
            web_data = web_response["data"]
            mobile_data = mobile_response["data"]
            
            # Check that response has same structure
            assert set(web_data.keys()) == set(mobile_data.keys()), \
                f"Response structure differs: web_keys={set(web_data.keys())}, mobile_keys={set(mobile_data.keys())}"
            
            # Check that user data fields are present and correctly formatted
            required_fields = ["id", "phone_number", "name", "preferred_language", "created_at", "updated_at", "is_active"]
            for field in required_fields:
                assert field in web_data, f"Missing field {field} in web response"
                assert field in mobile_data, f"Missing field {field} in mobile response"
                
                # Field types should be consistent
                assert type(web_data[field]) == type(mobile_data[field]), \
                    f"Field {field} type differs: web={type(web_data[field])}, mobile={type(mobile_data[field])}"
                    
    except httpx.ConnectError:
        pytest.skip("API service not available for testing")
    except Exception as e:
        pytest.fail(f"Cross-platform user registration consistency test failed: {str(e)}")

@pytest.mark.asyncio
async def test_cross_platform_health_check_consistency():
    """
    Property 21: Cross-Platform Consistency - Health Checks
    
    Health check endpoints should return identical information regardless of platform.
    This is critical for monitoring and debugging across different client types.
    """
    
    web_client = PlatformClient(WEB_USER_AGENT, "web")
    mobile_client = PlatformClient(MOBILE_USER_AGENT, "mobile")
    
    try:
        # Test basic health check
        web_health = await web_client.make_request("GET", "/health")
        mobile_health = await mobile_client.make_request("GET", "/health")
        
        # Status codes should be identical
        assert web_health["status_code"] == mobile_health["status_code"]
        
        # Health data should be identical
        if web_health["status_code"] == 200:
            web_data = web_health["data"]
            mobile_data = mobile_health["data"]
            
            # Core health fields should be present and identical
            assert "status" in web_data and "status" in mobile_data
            assert web_data["status"] == mobile_data["status"]
            
            if "services" in web_data and "services" in mobile_data:
                assert web_data["services"] == mobile_data["services"]
                
    except httpx.ConnectError:
        pytest.skip("API service not available for testing")
    except Exception as e:
        pytest.fail(f"Cross-platform health check consistency test failed: {str(e)}")

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])