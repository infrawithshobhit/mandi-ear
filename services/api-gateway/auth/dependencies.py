"""
Authentication dependencies for FastAPI
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import structlog

from config import settings
from models import TokenData, UserResponse
from database import get_db_connection

logger = structlog.get_logger()
security = HTTPBearer()

async def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    return token_data

async def get_current_user(token_data: TokenData = Depends(verify_token)):
    """Get current user from token"""
    user_not_found_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        conn = await get_db_connection()
        try:
            user_record = await conn.fetchrow(
                """
                SELECT id, phone_number, name, preferred_language, 
                       ST_X(location::geometry) as longitude,
                       ST_Y(location::geometry) as latitude,
                       created_at, updated_at, is_active
                FROM auth.users 
                WHERE id = $1 AND is_active = true
                """,
                token_data.user_id
            )
            
            if not user_record:
                raise user_not_found_exception
            
            return UserResponse(
                id=user_record['id'],
                phone_number=user_record['phone_number'],
                name=user_record['name'],
                preferred_language=user_record['preferred_language'],
                created_at=user_record['created_at'],
                updated_at=user_record['updated_at'],
                is_active=user_record['is_active']
            )
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error("Error fetching user", user_id=token_data.user_id, error=str(e))
        raise user_not_found_exception