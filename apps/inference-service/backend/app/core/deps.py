from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
import app.db.mongodb as mongodb
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_owner(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Check if database is connected and get the database instance
    if mongodb.db is None or mongodb.db.db is None:
        logger.error("Database not initialized in get_current_owner")
        raise HTTPException(500, "Database not initialized")
    
    # Get the database instance
    database = mongodb.db.db
    if database is None:
        logger.error("Database instance is None")
        raise HTTPException(500, "Database instance not available")
    
    # Access the users collection
    try:
        user = await database.users.find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise credentials_exception
        return user
    except Exception as e:
        logger.error(f"Error finding user: {e}")
        raise credentials_exception

async def get_current_admin(current_user = Depends(get_current_owner)):
    """
    Dependency to ensure the user is an Admin.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions. Admin access required."
        )
    return current_user