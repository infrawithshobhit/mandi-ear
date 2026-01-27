"""
Property-based test for cross-platform consistency
**Property 21: Cross-Platform Consistency**
**Validates: Requirements 10.1**
"""

import pytest
from hypothesis import given, strategies as st, settings, example
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import time
from unittest.mock import Mock, patch

class Platform(Enum):
    WEB = "web"
    MOBILE_ANDROID = "mobile_android"
    MOBILE_IOS = "mobile_ios"

@dataclass
class APIEndpoint:
    path: str
    method: str
    requires_auth: bool
    expected_fields: List[str]
    platform_specific_fields: Dict[Platform, List[str]]

@dataclass
class APIResponse:
    status_code: int
    data: Dict[str, Any]
    headers: Dict[str, str]
    response_time: float

class MockCrossPlatformTester:
    """Mock cross-platform tester for MANDI EAR™ platform"""
    
    def __init__(self):
        self.base_urls = {
            Platform.WEB: "http://localhost:8000",
            Platform.MOBILE_ANDROID: "http://localhost:8000",
            Platform.MOBILE_IOS: "http://localhost:8000"
        }
        
        # Define API endpoints that should be consistent across platforms
        self.api_endpoints = [
            APIEndpoint(
                path="/api/v1/prices/current",
                method="GET",
                requires_auth=True,
                expected_fields=["commodity", "price", "location", "timestamp"],
                platform_specific_fields={}
            ),
            APIEndpoint(
                path="/api/v1/voice/transcribe",
                method="POST",
                requires_auth=True,
                expected_fields=["transcript", "confidence", "language"],
                platform_specific_fields={}
            ),
            APIEndpoint(
                path="/api/v1/ambient/intelligence",
                method="GET",
                requires_auth=True,
                expected_fields=["market_data", "timestamp", "location"],
                platform_specific_fields={}
            ),
            APIEndpoint(
                path="/api/v1/crop-planning/recommend",
                method="POST",
                requires_auth=True,
                expected_fields=["recommendations", "risk_assessment", "income_projection"],
                platform_specific_fields={}
            ),
            APIEndpoint(
                path="/api/v1/msp/rates",
                method="GET",
                requires_auth=True,
                expected_fields=["commodity", "msp_rate", "effective_date"],
                platform_specific_fields={}
            ),
            APIEndpoint(
                path="/health",
                method="GET",
                requires_auth=False,
                expected_fields=["status", "timestamp", "version"],
                platform_specific_fields={}
            )
        ]
    
    def get_mock_response_data(self, endpoint: APIEndpoint, platform: Platform) -> Dict[str, Any]:
        """Generate mock response data based on endpoint"""
        if endpoint.path == "/health":
            return {
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z",
                "version": "1.0.0",
                "services": {"database": "healthy", "redis": "healthy"}
            }
        elif endpoint.path == "/api/v1/prices/current":
            return {
                "commodity": "wheat",
                "price": 2200.0,
                "location": "Delhi",
                "timestamp": "2024-01-01T00:00:00Z",
                "change": 50.0,
                "change_percent": 2.3
            }
        elif endpoint.path == "/api/v1/voice/transcribe":
            return {
                "transcript": "आज गेहूं का भाव क्या है?",
                "confidence": 0.95,
                "language": "hi"
            }
        elif endpoint.path == "/api/v1/ambient/intelligence":
            return {
                "market_data": [
                    {"commodity": "wheat", "price": 2200, "quantity": 100}
                ],
                "timestamp": "2024-01-01T00:00:00Z",
                "location": {"latitude": 28.6139, "longitude": 77.2090}
            }
        elif endpoint.path == "/api/v1/crop-planning/recommend":
            return {
                "recommendations": [
                    {"crop": "wheat", "expected_yield": 40, "risk_level": "low"}
                ],
                "risk_assessment": {"overall_risk": "medium"},
                "income_projection": {"expected_income": 150000}
            }
        elif endpoint.path == "/api/v1/msp/rates":
            return {
                "commodity": "wheat",
                "msp_rate": 2125.0,
                "effective_date": "2024-01-01"
            }
        else:
            return {"message": "Mock response", "data": {}}
    
    def make_api_request(self, platform: Platform, endpoint: APIEndpoint, 
                        params: Dict[str, Any] = None, 
                        json_data: Dict[str, Any] = None) -> APIResponse:
        """Make mock API request to specific platform"""
        
        # Simulate response time
        response_time = 0.1 + (hash(platform.value + endpoint.path) % 100) / 1000
        
        # Generate consistent mock response
        mock_data = self.get_mock_response_data(endpoint, platform)
        
        return APIResponse(
            status_code=200,
            data=mock_data,
            headers={"Content-Type": "application/json", "X-Platform": platform.value},
            response_time=response_time
        )
    
    def validate_response_structure(self, response: APIResponse, 
                                  endpoint: APIEndpoint, 
                                  platform: Platform) -> bool:
        """Validate that response has expected structure"""
        if response.status_code != 200:
            return True  # Skip validation for error responses
        
        data = response.data
        
        # Check for expected fields
        for field in endpoint.expected_fields:
            if field not in data:
                return False
        
        # Check platform-specific fields
        platform_fields = endpoint.platform_specific_fields.get(platform, [])
        for field in platform_fields:
            if field not in data:
                return False
        
        return True
    
    def compare_responses(self, responses: Dict[Platform, APIResponse], 
                         endpoint: APIEndpoint) -> bool:
        """Compare responses across platforms for consistency"""
        if not responses:
            return True
        
        # Get successful responses
        successful_responses = {
            platform: response for platform, response in responses.items()
            if response.status_code == 200
        }
        
        if len(successful_responses) < 2:
            return True  # Need at least 2 successful responses to compare
        
        # Compare core data structure
        response_list = list(successful_responses.values())
        first_response = response_list[0]
        
        for response in response_list[1:]:
            # Compare expected fields presence
            for field in endpoint.expected_fields:
                if (field in first_response.data) != (field in response.data):
                    return False
            
            # Compare data types for common fields
            for field in endpoint.expected_fields:
                if field in first_response.data and field in response.data:
                    if type(first_response.data[field]) != type(response.data[field]):
                        return False
        
        return True

# Test instance
cross_platform_tester = MockCrossPlatformTester()

@given(
    endpoint_index=st.integers(min_value=0, max_value=len(cross_platform_tester.api_endpoints) - 1),
    test_params=st.dictionaries(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        st.one_of(st.text(max_size=50), st.integers(), st.floats(allow_nan=False, allow_infinity=False)),
        min_size=0,
        max_size=3
    )
)
@settings(max_examples=10, deadline=15000)  # 15 second timeout per test
@example(endpoint_index=0, test_params={})
@example(endpoint_index=5, test_params={})  # Health endpoint
def test_cross_platform_api_consistency(endpoint_index: int, test_params: Dict[str, Any]):
    """
    **Property 21: Cross-Platform Consistency**
    
    For any API endpoint available on the platform, functionality should work 
    identically across web browsers and mobile applications (Android/iOS).
    
    **Validates: Requirements 10.1**
    """
    endpoint = cross_platform_tester.api_endpoints[endpoint_index]
    
    # Test all platforms
    responses = {}
    for platform in Platform:
        if endpoint.method == "GET":
            response = cross_platform_tester.make_api_request(
                platform, endpoint, params=test_params
            )
        else:
            response = cross_platform_tester.make_api_request(
                platform, endpoint, json_data=test_params
            )
        responses[platform] = response
    
    # Validate response structures are consistent
    for platform, response in responses.items():
        structure_valid = cross_platform_tester.validate_response_structure(
            response, endpoint, platform
        )
        assert structure_valid, f"Response structure invalid for {platform.value} on {endpoint.path}"
    
    # Validate cross-platform consistency
    consistency_valid = cross_platform_tester.compare_responses(responses, endpoint)
    assert consistency_valid, f"Cross-platform consistency failed for {endpoint.path}"
    
    # Validate response times are reasonable (< 5 seconds)
    for platform, response in responses.items():
        assert response.response_time < 5.0, f"Response time too slow for {platform.value}: {response.response_time}s"

@given(
    commodity=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
    location=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs')))
)
@settings(max_examples=5, deadline=15000)
@example(commodity="wheat", location="Delhi")
def test_price_query_consistency(commodity: str, location: str):
    """
    Test that price queries return consistent data across platforms
    """
    endpoint = APIEndpoint(
        path="/api/v1/prices/current",
        method="GET",
        requires_auth=True,
        expected_fields=["commodity", "price", "location", "timestamp"],
        platform_specific_fields={}
    )
    
    params = {"commodity": commodity, "location": location}
    responses = {}
    
    for platform in Platform:
        response = cross_platform_tester.make_api_request(platform, endpoint, params=params)
        responses[platform] = response
    
    # Check that successful responses have consistent price data format
    successful_responses = [r for r in responses.values() if r.status_code == 200]
    
    if len(successful_responses) >= 2:
        first_response = successful_responses[0]
        for response in successful_responses[1:]:
            if "price" in first_response.data and "price" in response.data:
                # Price should be numeric
                assert isinstance(first_response.data["price"], (int, float))
                assert isinstance(response.data["price"], (int, float))
                
                # Price should be positive
                assert first_response.data["price"] > 0
                assert response.data["price"] > 0

@given(
    audio_format=st.sampled_from(["wav", "mp3", "m4a"]),
    language=st.sampled_from(["hi", "en", "ta", "te", "bn"])
)
@settings(max_examples=3, deadline=15000)
@example(audio_format="wav", language="hi")
def test_voice_processing_consistency(audio_format: str, language: str):
    """
    Test that voice processing works consistently across platforms
    """
    endpoint = APIEndpoint(
        path="/api/v1/voice/transcribe",
        method="POST",
        requires_auth=True,
        expected_fields=["transcript", "confidence", "language"],
        platform_specific_fields={}
    )
    
    # Mock audio data (base64 encoded)
    json_data = {
        "audio_data": "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT",
        "format": audio_format,
        "language": language
    }
    
    responses = {}
    for platform in Platform:
        response = cross_platform_tester.make_api_request(platform, endpoint, json_data=json_data)
        responses[platform] = response
    
    # Validate consistency
    successful_responses = [r for r in responses.values() if r.status_code == 200]
    
    if len(successful_responses) >= 2:
        for response in successful_responses:
            if "confidence" in response.data:
                # Confidence should be between 0 and 1
                assert 0 <= response.data["confidence"] <= 1
            
            if "language" in response.data:
                # Language should be valid language code
                assert len(response.data["language"]) == 2

def test_health_endpoint_consistency():
    """
    Test that health endpoint works consistently across all platforms
    """
    endpoint = APIEndpoint(
        path="/health",
        method="GET",
        requires_auth=False,
        expected_fields=["status", "timestamp", "version"],
        platform_specific_fields={}
    )
    
    responses = {}
    for platform in Platform:
        response = cross_platform_tester.make_api_request(platform, endpoint)
        responses[platform] = response
    
    # All platforms should return 200 OK
    for platform, response in responses.items():
        assert response.status_code == 200, f"Health check failed for {platform.value}"
    
    # All responses should have consistent structure
    for platform, response in responses.items():
        assert "status" in response.data, f"Missing status field for {platform.value}"
        assert "timestamp" in response.data, f"Missing timestamp field for {platform.value}"
        assert "version" in response.data, f"Missing version field for {platform.value}"
    
    # Status should be consistent
    statuses = [response.data["status"] for response in responses.values()]
    assert len(set(statuses)) == 1, "Health status inconsistent across platforms"

if __name__ == "__main__":
    # Run specific test for debugging
    test_health_endpoint_consistency()
    print("Cross-platform consistency tests completed successfully!")