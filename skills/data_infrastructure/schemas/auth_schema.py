# schemas/auth_schema.py

#Import Libraries
from pydantic import BaseModel, EmailStr
from typing import Optional

# Model for user signup request
class SignupRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    password: str
    experience: Optional[str] = "researcher"   # "researcher" | "grower" | "breeder"
    organization: Optional[str] = None

# Model for user login request
class LoginRequest(BaseModel):
    email: EmailStr  # User's email address
    password: str  # User's password

# Model for the response containing the access token
class TokenResponse(BaseModel):
    access_token: str  # JWT access token
    token_type: str  # Type of the token (e.g., "bearer")
