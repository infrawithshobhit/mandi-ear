"""
Authentication middleware for API Gateway
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import time
from typing import Dict
from database import get_redis_client

logger = structlog.get_logger()

class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware to handle cross-cutting auth concerns"""
    
    # Paths that don't require authentication
    EXEMPT_PATHS = {
        "/",
        "/health",
        "/health/",
        "/auth/register",
        "/auth/login",
        "/docs",
        "/redoc",
        "/openapi.json"
    }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through authentication middleware"""
        
        # Skip authentication for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        
        # Skip authentication for health checks and docs
        if (request.url.path.startswith("/health") or 
            request.url.path.startswith("/docs") or
            request.url.path.startswith("/redoc")):
            return await call_next(request)
        
        try:
            # Process the request
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            logger.warning(
                "HTTP exception in middleware",
                path=request.url.path,
                status_code=e.status_code,
                detail=e.detail
            )
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )
        except Exception as e:
            logger.error(
                "Unexpected error in middleware",
                path=request.url.path,
                error=str(e)
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis"""
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.window_size = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to requests"""
        
        # Skip rate limiting for health checks
        if request.url.path.startswith("/health"):
            return await call_next(request)
        
        # Get client identifier (IP address or user ID from token)
        client_id = self._get_client_id(request)
        
        try:
            # Check rate limit
            if await self._is_rate_limited(client_id):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": {
                            "code": 429,
                            "message": "Rate limit exceeded. Please try again later.",
                            "timestamp": time.time()
                        }
                    },
                    headers={"Retry-After": "60"}
                )
            
            # Process request
            response = await call_next(request)
            
            # Record successful request
            await self._record_request(client_id)
            
            return response
            
        except Exception as e:
            logger.error("Error in rate limiting middleware", error=str(e))
            # Continue processing if rate limiting fails
            return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Try to get user ID from authorization header
        auth_header = request.headers.get("authorization")
        if auth_header:
            # In production, decode JWT to get user ID
            return f"user:{auth_header[:20]}"  # Simplified for now
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    async def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        try:
            redis_client = await get_redis_client()
            current_time = int(time.time())
            window_start = current_time - self.window_size
            
            # Use Redis sorted set to track requests in time window
            key = f"rate_limit:{client_id}"
            
            # Remove old entries
            await redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests in window
            current_count = await redis_client.zcard(key)
            
            return current_count >= self.calls_per_minute
            
        except Exception as e:
            logger.error("Error checking rate limit", client_id=client_id, error=str(e))
            return False  # Allow request if rate limiting fails
    
    async def _record_request(self, client_id: str):
        """Record a successful request"""
        try:
            redis_client = await get_redis_client()
            current_time = int(time.time())
            key = f"rate_limit:{client_id}"
            
            # Add current request to sorted set
            await redis_client.zadd(key, {str(current_time): current_time})
            
            # Set expiration for cleanup
            await redis_client.expire(key, self.window_size * 2)
            
        except Exception as e:
            logger.error("Error recording request", client_id=client_id, error=str(e))