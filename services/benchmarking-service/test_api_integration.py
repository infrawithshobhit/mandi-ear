"""
API Integration tests for Benchmarking Service
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime

from main import app

class TestBenchmarkingAPI:
    """Test API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def sample_farmer_id(self):
        """Sample farmer ID"""
        return str(uuid4())
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Benchmarking Service"
        assert data["version"] == "1.0.0"
        assert data["status"] == "operational"
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_set_price_floor(self, client, sample_farmer_id):
        """Test setting price floor"""
        request_data = {
            "farmer_id": sample_farmer_id,
            "commodity": "wheat",
            "floor_price": 2000.0,
            "unit": "per_quintal",
            "reasoning": "Based on production costs"
        }
        
        response = client.post("/price-floors", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "price_floor" in data
        
        price_floor = data["price_floor"]
        assert price_floor["farmer_id"] == sample_farmer_id
        assert price_floor["commodity"] == "wheat"
        assert price_floor["floor_price"] == 2000.0
        assert price_floor["unit"] == "per_quintal"
        assert price_floor["reasoning"] == "Based on production costs"
        assert price_floor["is_active"] is True
    
    def test_get_price_floors(self, client, sample_farmer_id):
        """Test getting price floors"""
        response = client.get(f"/price-floors/{sample_farmer_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["farmer_id"] == sample_farmer_id
        assert "price_floors" in data
        assert "total_floors" in data
        assert isinstance(data["price_floors"], list)
    
    def test_create_benchmark(self, client, sample_farmer_id):
        """Test creating benchmark"""
        request_data = {
            "farmer_id": sample_farmer_id,
            "commodity": "wheat",
            "analysis_period_days": 30,
            "location_filter": "local_mandi"
        }
        
        response = client.post("/benchmarks/create", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "benchmark" in data
        
        benchmark = data["benchmark"]
        assert benchmark["farmer_id"] == sample_farmer_id
        assert benchmark["commodity"] == "wheat"
        assert benchmark["benchmark_price"] > 0
        assert 0.0 <= benchmark["confidence_score"] <= 1.0
        assert benchmark["data_points_count"] > 0
    
    def test_get_farmer_benchmarks(self, client, sample_farmer_id):
        """Test getting farmer benchmarks"""
        response = client.get(f"/benchmarks/{sample_farmer_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["farmer_id"] == sample_farmer_id
        assert "benchmarks" in data
        assert "total_benchmarks" in data
        assert isinstance(data["benchmarks"], list)
    
    def test_track_performance(self, client, sample_farmer_id):
        """Test tracking performance"""
        request_data = {
            "farmer_id": sample_farmer_id,
            "commodity": "wheat",
            "actual_price": 2200.0,
            "quantity_sold": 10.0,
            "sale_date": datetime.utcnow().isoformat(),
            "location": "local_mandi"
        }
        
        response = client.post("/performance/track", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "performance" in data
        
        performance = data["performance"]
        assert performance["farmer_id"] == sample_farmer_id
        assert performance["commodity"] == "wheat"
        assert performance["actual_price"] == 2200.0
        assert performance["quantity_sold"] == 10.0
        assert 0.0 <= performance["performance_score"] <= 100.0
        assert performance["total_revenue"] == 22000.0
    
    def test_get_performance_history(self, client, sample_farmer_id):
        """Test getting performance history"""
        response = client.get(f"/performance/{sample_farmer_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["farmer_id"] == sample_farmer_id
        assert "performance_summary" in data
        assert "performance_records" in data
        assert "trends" in data
        assert "recommendations" in data
    
    def test_record_conversation(self, client, sample_farmer_id):
        """Test recording conversation"""
        conversation_data = {
            "commodity": "wheat",
            "price": 2100.0,
            "quantity": 15.0,
            "intent": "selling",
            "location": "local_mandi",
            "confidence": 0.85,
            "text": "I want to sell wheat at 2100 per quintal",
            "segment_id": "segment_123"
        }
        
        response = client.post(
            f"/conversations/record?farmer_id={sample_farmer_id}",
            json=conversation_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["farmer_id"] == sample_farmer_id
        assert data["commodity"] == "wheat"
        assert data["price_extracted"] == 2100.0
        assert data["confidence"] == 0.85
    
    def test_get_farmer_analytics(self, client, sample_farmer_id):
        """Test getting farmer analytics"""
        response = client.get(f"/analytics/{sample_farmer_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert data["farmer_id"] == sample_farmer_id
        assert data["analysis_period"] == "30d"
        assert "analytics" in data
        
        analytics = data["analytics"]
        assert "summary" in analytics
        assert "benchmarks" in analytics
        assert "price_floors" in analytics
        assert "performance" in analytics
        assert "trends" in analytics
        assert "recommendations" in analytics
    
    def test_invalid_price_floor_request(self, client, sample_farmer_id):
        """Test invalid price floor request"""
        request_data = {
            "farmer_id": sample_farmer_id,
            "commodity": "",  # Empty commodity should fail
            "floor_price": 2000.0
        }
        
        response = client.post("/price-floors", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_performance_tracking(self, client, sample_farmer_id):
        """Test invalid performance tracking request"""
        request_data = {
            "farmer_id": sample_farmer_id,
            "commodity": "wheat",
            "actual_price": -100.0,  # Negative price should fail
            "quantity_sold": 10.0
        }
        
        response = client.post("/performance/track", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_nonexistent_farmer_endpoints(self, client):
        """Test endpoints with non-existent farmer ID"""
        fake_farmer_id = str(uuid4())
        
        # Should still return 200 but with empty data
        response = client.get(f"/price-floors/{fake_farmer_id}")
        assert response.status_code == 200
        
        response = client.get(f"/benchmarks/{fake_farmer_id}")
        assert response.status_code == 200
        
        response = client.get(f"/performance/{fake_farmer_id}")
        assert response.status_code == 200
        
        response = client.get(f"/analytics/{fake_farmer_id}")
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__, "-v"])