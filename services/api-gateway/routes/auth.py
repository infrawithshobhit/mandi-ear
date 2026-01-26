"""
Authentication routes
"""

from fastapi import APIRouter, HTTPException, status, Depends
from passlib.context import CryptContext
from datetime import timedelta
import structlog
from uuid import uuid4

from models import UserCreate, UserResponse, LoginRequest, LoginResponse
from auth.dependencies import create_access_token
from database import get_db_connection
from config import settings

logger = structlog.get_logger()
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        conn = await get_db_connection()
        try:
            # Check if user already exists
            existing_user = await conn.fetchrow(
                "SELECT id FROM auth.users WHERE phone_number = $1",
                user_data.phone_number
            )
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this phone number already exists"
                )
            
            # Create new user
            user_id = uuid4()
            user_record = await conn.fetchrow(
                """
                INSERT INTO auth.users (id, phone_number, name, preferred_language)
                VALUES ($1, $2, $3, $4)
                RETURNING id, phone_number, name, preferred_language, 
                         created_at, updated_at, is_active
                """,
                user_id, user_data.phone_number, user_data.name, user_data.preferred_language
            )
            
            logger.info("User registered successfully", user_id=str(user_id))
            
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
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error registering user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )

@router.post("/login", response_model=LoginResponse)
async def login_user(login_data: LoginRequest):
    """Login user and return access token"""
    try:
        conn = await get_db_connection()
        try:
            # Find user by phone number
            user_record = await conn.fetchrow(
                """
                SELECT id, phone_number, name, preferred_language,
                       created_at, updated_at, is_active
                FROM auth.users 
                WHERE phone_number = $1 AND is_active = true
                """,
                login_data.phone_number
            )
            
            if not user_record:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid phone number or user not found"
                )
            
            # In production, verify OTP here
            # For now, we'll create a token directly
            
            # Create access token
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = await create_access_token(
                data={"sub": str(user_record['id'])},
                expires_delta=access_token_expires
            )
            
            # Create session record
            await conn.execute(
                """
                INSERT INTO auth.user_sessions (user_id, session_token, expires_at)
                VALUES ($1, $2, NOW() + INTERVAL '%s minutes')
                """,
                user_record['id'], access_token, settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            
            user_response = UserResponse(
                id=user_record['id'],
                phone_number=user_record['phone_number'],
                name=user_record['name'],
                preferred_language=user_record['preferred_language'],
                created_at=user_record['created_at'],
                updated_at=user_record['updated_at'],
                is_active=user_record['is_active']
            )
            
            logger.info("User logged in successfully", user_id=str(user_record['id']))
            
            return LoginResponse(
                access_token=access_token,
                token_type="bearer",
                user=user_response
            )
        finally:
            await conn.close()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error during login", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )