# Import Libraries
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional
import os
from dotenv import load_dotenv
from loguru import logger  # Using Loguru for logging

# Load environment variables
load_dotenv()

# Get environment secrets for JWT and token expiration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day default

# Setup password hashing context for bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Loguru configuration for logging
logger.add("app.log", level="INFO")  # Log to app.log file with INFO level

def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt and return the hashed version.
    
    Parameters:
    - password: The plain password string to hash.
    
    Returns:
    - The hashed password string.
    """
    logger.info("Hashing password...")  # Log that password hashing has started
    hashed_password = pwd_context.hash(password)
    logger.debug(f"Password hashed successfully: {hashed_password[:8]}****")  # Log first few characters of the hash for privacy
    return hashed_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if the provided plain password matches the hashed password.
    
    Parameters:
    - plain_password: The plain password to verify.
    - hashed_password: The hashed password to compare against.
    
    Returns:
    - True if the password matches, otherwise False.
    """
    logger.info("Verifying password...")  # Log that password verification is happening
    is_valid = pwd_context.verify(plain_password, hashed_password)
    if is_valid:
        logger.info("Password verified successfully.")  # Log successful verification
    else:
        logger.warning("Password verification failed.")  # Log failed verification
    return is_valid


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the provided user data and an optional expiration time.
    
    Parameters:
    - data: The user data (e.g., user ID, email) to encode into the JWT token.
    - expires_delta: Optional expiration time for the token. Defaults to 24 hours if not provided.
    
    Returns:
    - A JWT token as a string.
    """
    logger.info("Creating access token...")  # Log that token creation is in process
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    
    encoded_token = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    logger.debug(f"Access token created successfully. Expiration: {expire}")  # Log token expiration
    return encoded_token


def decode_token(token: str) -> Optional[dict]:
    """
    Decode a JWT token to extract the user payload and verify its validity.
    
    Parameters:
    - token: The JWT token to decode.
    
    Returns:
    - The decoded payload if valid, otherwise None.
    """
    logger.info("Decoding JWT token...")  # Log that the token decoding process has started
    try:
        decoded_payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        logger.info("Token decoded successfully.")  # Log successful decoding
        return decoded_payload
    except JWTError as e:
        logger.error(f"Error decoding token: {e}")  # Log the error if token decoding fails
        return None
