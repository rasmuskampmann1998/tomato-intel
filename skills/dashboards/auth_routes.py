# routes/auth_routes.py

#Import libraries
from fastapi import APIRouter, HTTPException
from datetime import timedelta
from schemas.auth_schema import SignupRequest, LoginRequest, TokenResponse
from supabase_service.auth_service import create_user_with_default_role, get_user_with_roles_by_email
from core.security import verify_password, create_access_token
from loguru import logger

# Set up logger
logger.add("app.log", level="INFO") 

router = APIRouter(prefix="/auth", tags=["Auth"])

# 1. Signup Route: User creation
@router.post("/signup")
def signup(user: SignupRequest):
    """
    Create a new user with the default role.
    """
    logger.info(f"Attempting to create user with email: {user.email}")
    
    created_user = create_user_with_default_role(user)
    if not created_user:
        logger.warning(f"User creation failed or already exists for email: {user.email}")
        raise HTTPException(status_code=400, detail="User already exists or creation failed")
    
    logger.info(f"User created successfully: {user.email}")
    return {"message": "User created successfully"}


# 2. Login Route: User authentication and token generation
@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest):
    """
    Authenticate a user and return an access token.
    """
    logger.info(f"User login attempt for email: {login_data.email}")
    
    # Fetch user based on email
    user = get_user_with_roles_by_email(login_data.email)
    if not user or not verify_password(login_data.password, user["password_hash"]):
        logger.warning(f"Invalid login attempt for email: {login_data.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate JWT token payload
    token_payload = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],  # Use role, not roles
    }
    
    # Create and return token
    token = create_access_token(token_payload, timedelta(minutes=60 * 24))
    logger.info(f"Login successful for email: {login_data.email}")
    
    return {"access_token": token, "token_type": "bearer"}
