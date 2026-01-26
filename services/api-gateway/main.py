"""
MANDI EAR™ API Gateway
Main entry point for the agricultural intelligence platform
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import structlog
from contextlib import asynccontextmanager

from config import settings
from auth.middleware import AuthMiddleware
from auth.dependencies import get_current_user
from routes import auth, health
from database import init_db, close_db

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
    yield
    # Shutdown
    logger.info("Shutting down MANDI EAR API Gateway")
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

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])

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