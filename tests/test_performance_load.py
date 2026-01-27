"""
Performance and load testing for MANDI EAR system
Tests system behavior under various load conditions
"""

import pytest
import asyncio
import httpx
import time
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import json

# Test configuration
API_GATEWAY_URL = "http://localhost:8080"
MAX_CONCURRENT_USERS = 50
TEST_DURATION_SECONDS = 60

class PerformanceMetrics:
    """Collect and analyze performance metrics"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.status_codes: Dict[int, int] = {}
        self.start_time = None
        self.end_time = None
    
    def add_result(self, response_time: float, status_code: int):
        """Add a test result"""
        self.response_times.append(response_time)
        
        if 200 <= status_code < 300:
            self.success_count += 1
        else:
            self.error_count += 1
        
        self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.response_times:
            return {"error": "No data collected"}
        
        total_requests = len(self.response_times)
        duration = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        
        return {
            "total_requests": total_requests,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": (self.success_count / total_requests) * 100,
            "requests_per_second": total_requests / duration if duration > 0 else 0,
            "response_times": {
                "min": min(self.response_times),
                "max": max(self.response_times),
                "mean": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "p95": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) >= 20 else max(self.response_times),
                "p99": statistics.quantiles(self.response_times, n=100)[98] if len(self.response_times) >= 100 else max(self.response_times)
            },
            "status_codes": self.status_codes,
            "duration_seconds": duration
        }

class LoadTestClient:
    """HTTP client for load testing"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.client = httpx.AsyncClient(timeout=30.0)
        self.metrics = PerformanceMetrics()
    
    async def authenticate(self) -> bool:
        """Authenticate test user"""
        try:
            response = await self.client.post(
                f"{API_GATEWAY_URL}/auth/login",
                json={
                    "phone_number": f"+9187654321{self.user_id:02d}",
                    "password": "load_test_pass"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                return True
            
            # Try to register if login fails
            response = await self.client.post(
                f"{API_GATEWAY_URL}/auth/register",
                json={
                    "name": f"Load Test User {self.user_id}",
                    "phone_number": f"+9187654321{self.user_id:02d}",
                    "password": "load_test_pass",
                    "preferred_language": "hi",
                    "location": {"latitude": 28.6139, "longitude": 77.2090}
                }
            )
            
            if response.status_code == 201:
                # Login after registration
                response = await self.client.post(
                    f"{API_GATEWAY_URL}/auth/login",
                    json={
                        "phone_number": f"+9187654321{self.user_id:02d}",
                        "password": "load_test_pass"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    return True
            
            return False
            
        except Exception:
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get authenticated headers"""
        headers = {"Content-Type": "application/json"}
        if hasattr(self, 'access_token') and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    async def make_request(self, method: str, endpoint: str, json_data: Dict = None) -> None:
        """Make a timed request and record metrics"""
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(
                    f"{API_GATEWAY_URL}{endpoint}",
                    headers=self.get_headers()
                )
            elif method.upper() == "POST":
                response = await self.client.post(
                    f"{API_GATEWAY_URL}{endpoint}",
                    headers=self.get_headers(),
                    json=json_data
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response_time = (time.time() - start_time) * 1000  # ms
            self.metrics.add_result(response_time, response.status_code)
            
        except Exception:
            response_time = (time.time() - start_time) * 1000  # ms
            self.metrics.add_result(response_time, 500)  # Treat exceptions as server errors
    
    async def simulate_user_session(self, duration_seconds: int):
        """Simulate a realistic user session"""
        self.metrics.start_time = time.time()
        end_time = self.metrics.start_time + duration_seconds
        
        # Authenticate first
        authenticated = await self.authenticate()
        if not authenticated:
            self.metrics.end_time = time.time()
            return
        
        # Simulate user behavior
        while time.time() < end_time:
            # Random user actions
            actions = [
                ("GET", "/api/v1/prices/current"),
                ("GET", "/api/v1/user/profile"),
                ("GET", "/api/v1/notifications"),
                ("GET", "/api/v1/msp/rates"),
                ("POST", "/api/v1/voice/transcribe", {"audio_data": "mock_audio", "language": "hi"}),
                ("GET", "/api/v1/prices/trends", {"commodity": "wheat", "days": 30}),
                ("POST", "/api/v1/negotiation/analyze", {"commodity": "rice", "current_price": 3000, "quantity": 50}),
            ]
            
            # Pick a random action
            import random
            action = random.choice(actions)
            
            if len(action) == 3:
                method, endpoint, data = action
                await self.make_request(method, endpoint, data)
            else:
                method, endpoint = action
                await self.make_request(method, endpoint)
            
            # Wait between requests (simulate human behavior)
            await asyncio.sleep(random.uniform(0.5, 2.0))
        
        self.metrics.end_time = time.time()
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

class TestSystemPerformance:
    """Performance testing suite"""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_single_user_performance(self):
        """Test performance with a single user"""
        client = LoadTestClient(1)
        
        try:
            await client.simulate_user_session(30)  # 30 second test
            summary = client.metrics.get_summary()
            
            # Performance assertions
            assert summary["success_rate"] >= 95.0, f"Success rate too low: {summary['success_rate']}%"
            assert summary["response_times"]["mean"] <= 2000, f"Mean response time too high: {summary['response_times']['mean']}ms"
            assert summary["response_times"]["p95"] <= 5000, f"95th percentile too high: {summary['response_times']['p95']}ms"
            
            print(f"Single user performance: {json.dumps(summary, indent=2)}")
            
        finally:
            await client.close()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_users_performance(self):
        """Test performance with multiple concurrent users"""
        num_users = min(10, MAX_CONCURRENT_USERS)  # Start with 10 users
        test_duration = 60  # 1 minute test
        
        # Create clients
        clients = [LoadTestClient(i) for i in range(num_users)]
        
        try:
            # Run concurrent user sessions
            tasks = [client.simulate_user_session(test_duration) for client in clients]
            await asyncio.gather(*tasks)
            
            # Aggregate metrics
            total_requests = sum(len(client.metrics.response_times) for client in clients)
            total_success = sum(client.metrics.success_count for client in clients)
            total_errors = sum(client.metrics.error_count for client in clients)
            
            all_response_times = []
            for client in clients:
                all_response_times.extend(client.metrics.response_times)
            
            if all_response_times:
                aggregate_summary = {
                    "concurrent_users": num_users,
                    "test_duration": test_duration,
                    "total_requests": total_requests,
                    "success_count": total_success,
                    "error_count": total_errors,
                    "success_rate": (total_success / total_requests) * 100 if total_requests > 0 else 0,
                    "requests_per_second": total_requests / test_duration,
                    "response_times": {
                        "min": min(all_response_times),
                        "max": max(all_response_times),
                        "mean": statistics.mean(all_response_times),
                        "median": statistics.median(all_response_times),
                        "p95": statistics.quantiles(all_response_times, n=20)[18] if len(all_response_times) >= 20 else max(all_response_times),
                        "p99": statistics.quantiles(all_response_times, n=100)[98] if len(all_response_times) >= 100 else max(all_response_times)
                    }
                }
                
                # Performance assertions for concurrent users
                assert aggregate_summary["success_rate"] >= 90.0, f"Success rate too low: {aggregate_summary['success_rate']}%"
                assert aggregate_summary["response_times"]["mean"] <= 3000, f"Mean response time too high: {aggregate_summary['response_times']['mean']}ms"
                assert aggregate_summary["response_times"]["p95"] <= 8000, f"95th percentile too high: {aggregate_summary['response_times']['p95']}ms"
                assert aggregate_summary["requests_per_second"] >= 1.0, f"Throughput too low: {aggregate_summary['requests_per_second']} req/s"
                
                print(f"Concurrent users performance: {json.dumps(aggregate_summary, indent=2)}")
            
        finally:
            # Close all clients
            for client in clients:
                await client.close()
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_stress_test(self):
        """Stress test with high load"""
        num_users = min(25, MAX_CONCURRENT_USERS)
        test_duration = 30  # Shorter duration for stress test
        
        clients = [LoadTestClient(i) for i in range(num_users)]
        
        try:
            # Run stress test
            tasks = [client.simulate_user_session(test_duration) for client in clients]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect metrics
            total_requests = sum(len(client.metrics.response_times) for client in clients)
            total_success = sum(client.metrics.success_count for client in clients)
            
            stress_summary = {
                "stress_users": num_users,
                "total_requests": total_requests,
                "success_count": total_success,
                "success_rate": (total_success / total_requests) * 100 if total_requests > 0 else 0
            }
            
            # Under stress, we expect some degradation but system should remain functional
            assert stress_summary["success_rate"] >= 70.0, f"System failed under stress: {stress_summary['success_rate']}% success rate"
            assert total_requests > 0, "No requests completed during stress test"
            
            print(f"Stress test results: {json.dumps(stress_summary, indent=2)}")
            
        finally:
            for client in clients:
                await client.close()
    
    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self):
        """Test health endpoint performance under load"""
        client = httpx.AsyncClient(timeout=10.0)
        
        try:
            # Make rapid health checks
            response_times = []
            success_count = 0
            
            for _ in range(50):
                start_time = time.time()
                response = await client.get(f"{API_GATEWAY_URL}/health/")
                response_time = (time.time() - start_time) * 1000
                
                response_times.append(response_time)
                if response.status_code == 200:
                    success_count += 1
            
            # Health endpoint should be very fast and reliable
            assert success_count >= 48, f"Health endpoint reliability too low: {success_count}/50"
            assert statistics.mean(response_times) <= 500, f"Health endpoint too slow: {statistics.mean(response_times)}ms"
            assert max(response_times) <= 2000, f"Health endpoint max response time too high: {max(response_times)}ms"
            
            print(f"Health endpoint performance: {statistics.mean(response_times):.2f}ms average")
            
        finally:
            await client.aclose()

class TestResourceUtilization:
    """Test resource utilization and limits"""
    
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self):
        """Test that memory usage remains stable under load"""
        # This would typically require system monitoring tools
        # For now, we'll test that the system continues to respond
        
        client = httpx.AsyncClient(timeout=30.0)
        
        try:
            # Make many requests to potentially trigger memory issues
            for i in range(100):
                response = await client.get(f"{API_GATEWAY_URL}/health/")
                assert response.status_code == 200, f"System became unresponsive at request {i}"
                
                # Small delay to avoid overwhelming
                await asyncio.sleep(0.1)
            
            # System should still be responsive
            response = await client.get(f"{API_GATEWAY_URL}/health/services")
            assert response.status_code == 200, "System unresponsive after load test"
            
        finally:
            await client.aclose()
    
    @pytest.mark.asyncio
    async def test_connection_handling(self):
        """Test connection handling and cleanup"""
        # Test that the system can handle many connections
        clients = [httpx.AsyncClient(timeout=10.0) for _ in range(20)]
        
        try:
            # Make concurrent requests from all clients
            tasks = []
            for client in clients:
                task = client.get(f"{API_GATEWAY_URL}/health/")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful responses
            success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
            
            # Should handle most connections successfully
            assert success_count >= 18, f"Connection handling failed: {success_count}/20 successful"
            
        finally:
            # Clean up all clients
            for client in clients:
                await client.aclose()

if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-m", "not slow"])  # Skip slow tests by default