"""
Simple MANDI EAR™ API Gateway for initial testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
from datetime import datetime

# Create FastAPI application
app = FastAPI(
    title="MANDI EAR™ API Gateway",
    description="India's first ambient AI-powered agricultural intelligence platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to MANDI EAR™ - Agricultural Intelligence Platform",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "api_gateway": "healthy"
        }
    }

@app.get("/health/services")
async def detailed_health():
    """Detailed health check"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system_healthy": True,
        "services": {
            "api-gateway": {
                "status": "healthy",
                "uptime_percentage": 100.0,
                "response_time": 50,
                "url": "http://api-gateway:8000"
            }
        },
        "summary": {
            "total_services": 1,
            "healthy_services": 1,
            "unhealthy_services": 0
        }
    }

@app.get("/api/v1/test")
async def test_endpoint():
    """Test API endpoint"""
    return {
        "message": "MANDI EAR™ API is working!",
        "timestamp": datetime.utcnow().isoformat(),
        "test": "success"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)