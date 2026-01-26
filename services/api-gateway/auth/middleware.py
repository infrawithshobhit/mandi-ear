"""
Authentication middleware for API Gateway
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

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