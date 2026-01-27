"""
MANDI EAR™ API Gateway
Main entry point for the agricultural intelligence platform
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
import structlog
from contextlib import asynccontextmanager
import time
import httpx
import asyncio
from typing import Dict, Any

from config import settings
from auth.middleware import AuthMiddleware, RateLimitMiddleware
from auth.dependencies import get_current_user
from routes import auth, health, services, docs
from database import init_db, close_db
from health_monitor import health_monitor

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting MANDI EAR API Gateway")
    await init_db()
    
    # Start health monitoring in background
    health_task = asyncio.create_task(health_monitor.start_monitoring())
    logger.info("Health monitoring started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MANDI EAR API Gateway")
    health_task.cancel()
    try:
        await health_task
    except asyncio.CancelledError:
        pass
    await close_db()

# Create FastAPI application
app = FastAPI(
    title="MANDI EAR™ API Gateway",
    description="India's first ambient AI-powered agricultural intelligence platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication and rate limiting middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(services.router, prefix="/api/v1", tags=["Services"])
app.include_router(docs.router, prefix="/docs-api", tags=["Documentation"])

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler"""
    logger.warning(
        "HTTP exception occurred",
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code,
        detail=exc.detail
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": time.time()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors"""
    logger.error(
        "Unexpected error occurred",
        path=request.url.path,
        method=request.method,
        error=str(exc)
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": time.time()
            }
        }
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to MANDI EAR™ - Agricultural Intelligence Platform",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/protected")
async def protected_endpoint(current_user = Depends(get_current_user)):
    """Example protected endpoint"""
    return {
        "message": f"Hello {current_user.name}!",
        "user_id": str(current_user.id)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)