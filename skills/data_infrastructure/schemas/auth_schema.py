# schemas/auth_schema.py

#Import Libraries
from pydantic import BaseModel, EmailStr
from typing import Optional

# Model for user signup request
class SignupRequest(BaseModel):
    email: EmailStr  # User's email address
    full_name: Optional[str] = None  # Optional full name of the user
    password: str  # User's password

# Model for user login request
class LoginRequest(BaseModel):
    email: EmailStr  # User's email address
    password: str  # User's password

# Model for the response containing the access token
class TokenResponse(BaseModel):
    access_token: str  # JWT access token
    token_type: str  # Type of the token (e.g., "bearer")
