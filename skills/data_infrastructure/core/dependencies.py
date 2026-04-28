from fastapi import Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import os
from loguru import logger  # Loguru import for logging

# OAuth2 password bearer used to retrieve the token from requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Optional variant — does not raise 403 when Authorization header is absent (for demo/public endpoints)
_oauth2_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# JWT settings (secret key and algorithm) fetched from environment variables
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Loguru configuration
logger.add("app.log", level="INFO")  # Log to app.log with INFO level

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Decodes the JWT token to retrieve the current user's details, such as user ID, email, and role.
    If decoding or validation fails, raises a 401 Unauthorized error.
    
    Parameters:
    - token: The OAuth2 token passed from the request header.
    
    Returns:
    - A dictionary containing 'id', 'email', and 'role' of the user if the token is valid.
    
    Raises:
    - HTTPException: If the token is invalid or if required fields are missing.
    """
    # Define the exception in case of invalid credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Attempt to decode the JWT token
        logger.info("Decoding JWT token...")
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Extract user details from the payload
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")

        # If any required field is missing, raise an exception
        if not user_id or not email or not role:
            logger.warning(f"Missing user_id, email, or role in payload for token: {token}")
            raise credentials_exception

    except JWTError as e:
        # Log and raise an exception if there is an error during token decoding
        logger.error(f"JWT decoding error: {e}")
        raise credentials_exception

    # Successfully decoded and validated the token, log the details
    logger.info(f"User decoded successfully: ID={user_id}, Email={email}, Role={role}")
    
    # Return the user details
    return {
        "id": user_id,
        "email": email,
        "role": role
    }


def get_current_user_optional(token: str = Security(_oauth2_optional)) -> dict:
    """Returns a demo user dict when no token is provided — allows unauthenticated demo access."""
    if not token:
        return {"id": None, "email": "demo", "role": "user"}
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role", "user")
        if user_id and email:
            return {"id": user_id, "email": email, "role": role}
    except JWTError:
        pass
    return {"id": None, "email": "demo", "role": "user"}


def require_researcher(current_user=Depends(get_current_user)):
    """
    Ensures the current user has 'researcher' role. If not, raises a 403 Forbidden error.
    
    Parameters:
    - current_user: The user details obtained from the `get_current_user` function.
    
    Returns:
    - current_user: If the user has the 'researcher' role.
    
    Raises:
    - HTTPException: If the user does not have the 'researcher' role.
    """
    # Check if the current user has 'researcher' role
    logger.debug(f"Checking if user {current_user['email']} has 'researcher' role.")
    if current_user["role"].lower() != "researcher":
        # Log the failed access attempt
        logger.warning(f"Access denied for {current_user['email']}: Researcher role required.")
        raise HTTPException(status_code=403, detail="Researcher access required")
    
    # Log successful role validation
    logger.info(f"User {current_user['email']} has 'researcher' role.")
    return current_user


def require_admin(current_user=Depends(get_current_user)):
    """
    Ensures the current user has 'admin' role. If not, raises a 403 Forbidden error.
    
    Parameters:
    - current_user: The user details obtained from the `get_current_user` function.
    
    Returns:
    - current_user: If the user has the 'admin' role.
    
    Raises:
    - HTTPException: If the user does not have the 'admin' role.
    """
    # Check if the current user has 'admin' role
    logger.debug(f"Checking if user {current_user['email']} has 'admin' role.")
    if current_user["role"].lower() != "admin":
        # Log the failed access attempt
        logger.warning(f"Access denied for {current_user['email']}: Admin role required.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    # Log successful role validation
    logger.info(f"User {current_user['email']} has 'admin' role.")
    return current_user


def require_editor(current_user: dict = Depends(get_current_user)):
    """
    Ensures the current user has 'editor' role. If not, raises a 403 Forbidden error.
    
    Parameters:
    - current_user: The user details obtained from the `get_current_user` function.
    
    Returns:
    - current_user: If the user has the 'editor' role.
    
    Raises:
    - HTTPException: If the user does not have the 'editor' role.
    """
    # Check if the current user has 'editor' role
    logger.debug(f"Checking if user {current_user['email']} has 'editor' role.")
    if current_user["role"].lower() != "editor":
        # Log the failed access attempt
        logger.warning(f"Access denied for {current_user['email']}: Editor role required.")
        raise HTTPException(status_code=403, detail="Editor access only")
    
    # Log successful role validation
    logger.info(f"User {current_user['email']} has 'editor' role.")
    return current_user
