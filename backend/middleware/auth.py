from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from decouple import config
from database import get_database
from models.user import User, UserRole

# Configuration
JWT_SECRET_KEY = config("JWT_SECRET_KEY")
JWT_ALGORITHM = config("JWT_ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30))

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def revoke_token(token: str):
    """Store a JWT token as revoked"""
    db = get_database()
    await db.revoked_tokens.insert_one({"token": token, "revoked_at": datetime.utcnow()})

async def is_token_revoked(token: str) -> bool:
    """Check if a JWT token has been revoked"""
    db = get_database()
    return await db.revoked_tokens.find_one({"token": token}) is not None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if await is_token_revoked(credentials.credentials):
        raise credentials_exception
    
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    db = get_database()
    user_doc = await db.users.find_one({"id": user_id})
    if user_doc is None:
        raise credentials_exception
    
    # Update last seen
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"last_seen_at": datetime.utcnow()}}
    )
    
    return User(**user_doc)

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get current active user (non-banned)"""
    if current_user.strikes >= 5:  # Banned if 5+ strikes
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended due to multiple violations"
        )
    return current_user

def require_roles(allowed_roles: list[UserRole]):
    """Decorator to require specific user roles"""
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if not any(role in current_user.roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

def require_site_admin(current_user: User = Depends(get_current_active_user)):
    """Require site admin role"""
    if not current_user.is_site_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Site admin access required"
        )
    return current_user