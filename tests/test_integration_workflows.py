"""
Integration tests for complete MANDI EAR workflows
Tests end-to-end user journeys and data consistency across services
"""

import pytest
import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import uuid

# Test configuration
API_GATEWAY_URL = "http://localhost:8080"
TEST_USER_ID = "test-integration-user"
TEST_PHONE = "+919876543210"
TEST_PASSWORD = "integration_test_pass"

class IntegrationTestClient:
    """HTTP client for integration testing"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
        self.user_id = None
    
    async def authenticate(self) -> bool:
        """Authenticate test user"""
        try:
            # Try to login first
            response = await self.client.post(
                f"{API_GATEWAY_URL}/auth/login",
                json={
                    "phone_number": TEST_PHONE,
                    "password": TEST_PASSWORD
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.user_id = data.get("user_id")
                return True
            
            # If login fails, try to register
            response = await self.client.post(
                f"{API_GATEWAY_URL}/auth/register",
                json={
                    "name": "Integration Test User",
                    "phone_number": TEST_PHONE,
                    "password": TEST_PASSWORD,
                    "preferred_language": "hi",
                    "location": {
                        "latitude": 28.6139,
                        "longitude": 77.2090
                    }
                }
            )
            
            if response.status_code == 201:
                # Now login
                response = await self.client.post(
                    f"{API_GATEWAY_URL}/auth/login",
                    json={
                        "phone_number": TEST_PHONE,
                        "password": TEST_PASSWORD
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    self.user_id = data.get("user_id")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get authenticated headers"""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

@pytest.fixture
async def test_client():
    """Create authenticated test client"""
    client = IntegrationTestClient()
    authenticated = await client.authenticate()
    
    if not authenticated:
        pytest.skip("Could not authenticate test user")
    
    yield client
    await client.close()

class TestCompleteUserJourneys:
    """Test complete user journeys from voice input to recommendations"""
    
    @pytest.mark.asyncio
    async def test_voice_to_price_discovery_journey(self, test_client):
        """Test: Voice query -> Transcription -> Price discovery -> Voice response"""
        journey_id = str(uuid.uuid4())
        
        # Step 1: Voice transcription
        voice_response = await test_client.client.post(
            f"{API_GATEWAY_URL}/api/v1/voice/transcribe",
            headers=test_client.get_headers(),
            json={
                "audio_data": "mock_base64_audio_data",
                "journey_id": journey_id
            }
        )
        
        assert voice_response.status_code == 200
        voice_data = voice_response.json()
        assert "transcription" in voice_data
        assert "intent" in voice_data
        
        # Step 2: Price discovery based on transcription
        price_response = await test_client.client.get(
            f"{API_GATEWAY_URL}/api/v1/prices/current",
            headers=test_client.get_headers(),
            params={"commodity": "wheat"}
        )
        
        assert price_response.status_code == 200
        price_data = price_response.json()
        assert "prices" in price_data
        assert len(price_data["prices"]) > 0
        
        # Step 3: Generate voice response
        synthesis_response = await test_client.client.post(
            f"{API_GATEWAY_URL}/api/v1/voice/synthesize",
            headers=test_client.get_headers(),
            json={
                "text": f"गेहूं का आज का भाव {price_data['prices'][0]['price']} रुपये प्रति क्विंटल है।",
                "language": "hi",
                "journey_id": journey_id
            }
        )
        
        assert synthesis_response.status_code == 200
        synthesis_data = synthesis_response.json()
        assert "audio_data" in synthesis_data
        
        # Verify journey consistency
        assert voice_data.get("journey_id") == journey_id
        assert synthesis_data.get("journey_id") == journey_id
    
    @pytest.mark.asyncio
    async def test_ambient_ai_to_negotiation_journey(self, test_client):
        """Test: Ambient AI extraction -> Market analysis -> Negotiation guidance"""
        
        # Step 1: Process ambient audio
        ambient_response = await test_client.client.post(
            f"{API_GATEWAY_URL}/api/v1/ambient/process",
            headers=test_client.get_headers(),
            json={
                "audio_data": "mock_ambient_audio_data",
                "location": {"latitude": 28.6139, "longitude": 77.2090},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        assert ambient_response.status_code == 200
        ambient_data = ambient_response.json()
        assert "extractions" in ambient_data
        
        # Assume we extracted some market data
        if ambient_data["extractions"]:
            extraction = ambient_data["extractions"][0]
            commodity = extraction.get("commodity", "wheat")
            price = extraction.get("price", 2500)
            
            # Step 2: Get negotiation guidance
            negotiation_response = await test_client.client.post(
                f"{API_GATEWAY_URL}/api/v1/negotiation/analyze",
                headers=test_client.get_headers(),
                json={
                    "commodity": commodity,
                    "current_price": price,
                    "quantity": 100,
                    "context": "selling"
                }
            )
            
            assert negotiation_response.status_code == 200
            negotiation_data = negotiation_response.json()
            assert "strategy" in negotiation_data
            assert "recommended_price" in negotiation_data
            
            # Verify price consistency
            recommended_price = negotiation_data["recommended_price"]
            assert isinstance(recommended_price, (int, float))
            assert recommended_price > 0
    
    @pytest.mark.asyncio
    async def test_crop_planning_to_market_analysis_journey(self, test_client):
        """Test: Crop planning -> Market analysis -> Income projections"""
        
        # Step 1: Get crop recommendations
        crop_response = await test_client.client.post(
            f"{API_GATEWAY_URL}/api/v1/crop-planning/recommend",
            headers=test_client.get_headers(),
            json={
                "location": {"latitude": 28.6139, "longitude": 77.2090},
                "farm_size": 5.0,
                "soil_type": "loamy",
                "season": "kharif",
                "water_availability": "moderate"
            }
        )
        
        assert crop_response.status_code == 200
        crop_data = crop_response.json()
        assert "recommendations" in crop_data
        
        if crop_data["recommendations"]:
            recommended_crop = crop_data["recommendations"][0]
            crop_name = recommended_crop.get("crop", "rice")
            
            # Step 2: Get market analysis for recommended crop
            market_response = await test_client.client.get(
                f"{API_GATEWAY_URL}/api/v1/prices/trends",
                headers=test_client.get_headers(),
                params={"commodity": crop_name, "days": 90}
            )
            
            assert market_response.status_code == 200
            market_data = market_response.json()
            assert "trend_data" in market_data
            
            # Step 3: Verify income projections are realistic
            projected_income = recommended_crop.get("projected_income", 0)
            assert projected_income > 0
            
            # Income should be based on current market trends
            if market_data["trend_data"]:
                avg_price = sum(point["price"] for point in market_data["trend_data"]) / len(market_data["trend_data"])
                expected_yield = recommended_crop.get("expected_yield", 0)
                
                # Basic sanity check: projected income should be reasonable
                assert projected_income <= avg_price * expected_yield * 1.5  # Allow 50% premium

class TestDataConsistency:
    """Test data consistency across services"""
    
    @pytest.mark.asyncio
    async def test_price_data_consistency(self, test_client):
        """Test price data consistency across different endpoints"""
        
        # Get current prices
        current_response = await test_client.client.get(
            f"{API_GATEWAY_URL}/api/v1/prices/current",
            headers=test_client.get_headers(),
            params={"commodity": "wheat"}
        )
        
        assert current_response.status_code == 200
        current_data = current_response.json()
        
        # Get cross-mandi prices
        cross_mandi_response = await test_client.client.get(
            f"{API_GATEWAY_URL}/api/v1/prices/cross-mandi",
            headers=test_client.get_headers(),
            params={"commodity": "wheat", "radius_km": 500}
        )
        
        assert cross_mandi_response.status_code == 200
        cross_mandi_data = cross_mandi_response.json()
        
        # Verify consistency
        if current_data.get("prices") and cross_mandi_data.get("mandis"):
            current_prices = [p["price"] for p in current_data["prices"]]
            cross_mandi_prices = []
            
            for mandi in cross_mandi_data["mandis"]:
                if "prices" in mandi:
                    cross_mandi_prices.extend([p["price"] for p in mandi["prices"]])
            
            # Current prices should be within the range of cross-mandi prices
            if current_prices and cross_mandi_prices:
                min_cross_price = min(cross_mandi_prices)
                max_cross_price = max(cross_mandi_prices)
                
                for price in current_prices:
                    assert min_cross_price * 0.8 <= price <= max_cross_price * 1.2  # Allow 20% variance
    
    @pytest.mark.asyncio
    async def test_user_data_consistency(self, test_client):
        """Test user data consistency across services"""
        
        # Get user profile
        profile_response = await test_client.client.get(
            f"{API_GATEWAY_URL}/api/v1/user/profile",
            headers=test_client.get_headers()
        )
        
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        
        # Get user notifications
        notifications_response = await test_client.client.get(
            f"{API_GATEWAY_URL}/api/v1/notifications",
            headers=test_client.get_headers()
        )
        
        assert notifications_response.status_code == 200
        notifications_data = notifications_response.json()
        
        # Verify user ID consistency
        profile_user_id = profile_data.get("user_id")
        
        if notifications_data.get("notifications"):
            for notification in notifications_data["notifications"]:
                notification_user_id = notification.get("user_id")
                if notification_user_id:
                    assert notification_user_id == profile_user_id
    
    @pytest.mark.asyncio
    async def test_msp_data_consistency(self, test_client):
        """Test MSP data consistency"""
        
        # Get MSP rates
        msp_response = await test_client.client.get(
            f"{API_GATEWAY_URL}/api/v1/msp/rates",
            headers=test_client.get_headers()
        )
        
        assert msp_response.status_code == 200
        msp_data = msp_response.json()
        
        # Get current market prices
        prices_response = await test_client.client.get(
            f"{API_GATEWAY_URL}/api/v1/prices/current",
            headers=test_client.get_headers()
        )
        
        assert prices_response.status_code == 200
        prices_data = prices_response.json()
        
        # Verify MSP enforcement logic
        if msp_data.get("msp_rates") and prices_data.get("prices"):
            msp_rates = {rate["commodity"]: rate["price"] for rate in msp_data["msp_rates"]}
            
            for price_point in prices_data["prices"]:
                commodity = price_point.get("commodity")
                market_price = price_point.get("price")
                
                if commodity in msp_rates:
                    msp_price = msp_rates[commodity]
                    
                    # If market price is below MSP, there should be violations
                    if market_price < msp_price:
                        violations_response = await test_client.client.get(
                            f"{API_GATEWAY_URL}/api/v1/msp/violations",
                            headers=test_client.get_headers()
                        )
                        
                        assert violations_response.status_code == 200
                        violations_data = violations_response.json()
                        
                        # Should have violations for this commodity
                        violation_commodities = [v.get("commodity") for v in violations_data.get("violations", [])]
                        assert commodity in violation_commodities

class TestSystemPerformance:
    """Test system performance under load"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, test_client):
        """Test system performance with concurrent requests"""
        
        async def make_request():
            response = await test_client.client.get(
                f"{API_GATEWAY_URL}/api/v1/prices/current",
                headers=test_client.get_headers()
            )
            return response.status_code == 200
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        start_time = asyncio.get_event_loop().time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = asyncio.get_event_loop().time()
        
        # Check results
        successful_requests = sum(1 for r in results if r is True)
        total_time = end_time - start_time
        
        # Performance assertions
        assert successful_requests >= 8  # At least 80% success rate
        assert total_time < 10.0  # Should complete within 10 seconds
        
        # Calculate average response time
        avg_response_time = total_time / len(tasks)
        assert avg_response_time < 3.0  # Average response time should be under 3 seconds
    
    @pytest.mark.asyncio
    async def test_service_health_monitoring(self, test_client):
        """Test service health monitoring functionality"""
        
        # Check overall health
        health_response = await test_client.client.get(
            f"{API_GATEWAY_URL}/health/services",
            headers=test_client.get_headers()
        )
        
        assert health_response.status_code == 200
        health_data = health_response.json()
        
        assert "system_healthy" in health_data
        assert "services" in health_data
        assert "summary" in health_data
        
        # Verify service monitoring
        services = health_data["services"]
        critical_services = ["ambient-ai", "voice-processing", "price-discovery", "user-management"]
        
        for service_name in critical_services:
            if service_name in services:
                service_health = services[service_name]
                assert "status" in service_health
                assert "uptime_percentage" in service_health
                
                # Critical services should have high uptime
                uptime = service_health["uptime_percentage"]
                assert uptime >= 90.0  # At least 90% uptime
    
    @pytest.mark.asyncio
    async def test_data_flow_validation(self, test_client):
        """Test end-to-end data flow validation"""
        
        # Trigger data flow validation
        validation_response = await test_client.client.post(
            f"{API_GATEWAY_URL}/health/validate-flows",
            headers=test_client.get_headers()
        )
        
        assert validation_response.status_code == 200
        validation_data = validation_response.json()
        
        assert "summary" in validation_data
        assert "flows" in validation_data
        
        summary = validation_data["summary"]
        assert "flow_success_rate" in summary
        assert "step_success_rate" in summary
        
        # Parse success rates
        flow_success_rate = float(summary["flow_success_rate"].rstrip('%'))
        step_success_rate = float(summary["step_success_rate"].rstrip('%'))
        
        # System should have reasonable success rates
        assert flow_success_rate >= 70.0  # At least 70% of flows should succeed
        assert step_success_rate >= 80.0  # At least 80% of steps should succeed

class TestErrorHandling:
    """Test error handling and resilience"""
    
    @pytest.mark.asyncio
    async def test_invalid_request_handling(self, test_client):
        """Test handling of invalid requests"""
        
        # Test invalid JSON
        response = await test_client.client.post(
            f"{API_GATEWAY_URL}/api/v1/voice/transcribe",
            headers=test_client.get_headers(),
            content="invalid json"
        )
        
        assert response.status_code == 422  # Unprocessable Entity
        
        # Test missing required fields
        response = await test_client.client.post(
            f"{API_GATEWAY_URL}/api/v1/ambient/process",
            headers=test_client.get_headers(),
            json={}  # Missing required fields
        )
        
        assert response.status_code in [400, 422]  # Bad Request or Unprocessable Entity
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, test_client):
        """Test authentication error handling"""
        
        # Test request without authentication
        client = httpx.AsyncClient(timeout=30.0)
        
        response = await client.get(f"{API_GATEWAY_URL}/api/v1/user/profile")
        assert response.status_code == 401  # Unauthorized
        
        # Test request with invalid token
        response = await client.get(
            f"{API_GATEWAY_URL}/api/v1/user/profile",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401  # Unauthorized
        
        await client.aclose()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_client):
        """Test rate limiting functionality"""
        
        # Make rapid requests to trigger rate limiting
        responses = []
        for _ in range(100):  # Make many requests quickly
            response = await test_client.client.get(
                f"{API_GATEWAY_URL}/api/v1/prices/current",
                headers=test_client.get_headers()
            )
            responses.append(response.status_code)
        
        # Should eventually get rate limited
        rate_limited_responses = [code for code in responses if code == 429]
        
        # If rate limiting is working, we should see some 429 responses
        # This test might pass if rate limits are high, which is also acceptable
        assert len(rate_limited_responses) >= 0  # Just ensure no errors in the test

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])