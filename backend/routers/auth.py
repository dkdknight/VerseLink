from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from decouple import config
import httpx
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel

from database import get_database
from models.user import User, UserCreate, UserResponse, UserProfile
from middleware.auth import create_access_token, get_current_active_user

router = APIRouter()

# Discord OAuth Configuration
DISCORD_CLIENT_ID = config("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = config("DISCORD_CLIENT_SECRET")  
DISCORD_REDIRECT_URI = config("DISCORD_REDIRECT_URI")

oauth = OAuth()
oauth.register(
    name='discord',
    client_id=DISCORD_CLIENT_ID,
    client_secret=DISCORD_CLIENT_SECRET,
    server_metadata_url='https://discord.com/.well-known/openid_configuration',
    client_kwargs={
        'scope': 'identify email guilds'
    }
)

@router.get("/discord/redirect")
async def discord_auth_redirect():
    """Redirect to Discord OAuth"""
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify email guilds"
    )
    return {"auth_url": discord_auth_url}

@router.post("/discord/callback")
async def discord_auth_callback(code: str):
    """Handle Discord OAuth callback"""
    try:
        # Exchange code for access token
        token_data = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI,
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://discord.com/api/oauth2/token",
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            token_response.raise_for_status()
            tokens = token_response.json()
            
            # Get user info from Discord
            user_response = await client.get(
                "https://discord.com/api/users/@me",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            user_response.raise_for_status()
            discord_user = user_response.json()
            
            # Get user guilds (optional, for org integration later)
            guilds_response = await client.get(
                "https://discord.com/api/users/@me/guilds",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            guilds_response.raise_for_status()
            user_guilds = guilds_response.json()
        
        db = get_database()
        
        # Check if user exists
        existing_user = await db.users.find_one({"discord_id": discord_user["id"]})
        
        if existing_user:
            # Update existing user info
            update_data = {
                "discord_username": f"{discord_user['username']}#{discord_user['discriminator']}" if discord_user.get('discriminator') != '0' else discord_user['username'],
                "avatar_url": f"https://cdn.discordapp.com/avatars/{discord_user['id']}/{discord_user['avatar']}.png" if discord_user.get('avatar') else None,
                "updated_at": datetime.utcnow()
            }
            
            await db.users.update_one(
                {"discord_id": discord_user["id"]},
                {"$set": update_data}
            )
            
            user = User(**existing_user, **update_data)
        else:
            # Create new user
            username = f"{discord_user['username']}#{discord_user['discriminator']}" if discord_user.get('discriminator') != '0' else discord_user['username']
            
            # Generate unique handle from Discord username
            base_handle = discord_user['username'].lower().replace(' ', '_')
            handle = base_handle
            counter = 1
            while await db.users.find_one({"handle": handle}):
                handle = f"{base_handle}_{counter}"
                counter += 1
            
            user_data = UserCreate(
                discord_id=discord_user["id"],
                discord_username=username,
                handle=handle,
                email=discord_user.get("email"),
                avatar_url=f"https://cdn.discordapp.com/avatars/{discord_user['id']}/{discord_user['avatar']}.png" if discord_user.get('avatar') else None
            )
            
            user = User(**user_data.dict())
            await db.users.insert_one(user.dict())
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse(**user.dict())
        }
        
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Discord API error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return UserProfile(**current_user.dict())

@router.post("/logout")
async def logout():
    """Logout user (client should remove token)"""
    return {"message": "Successfully logged out"}

@router.get("/check")
async def check_auth(current_user: User = Depends(get_current_active_user)):
    """Check if user is authenticated"""
    return {
        "authenticated": True,
        "user": UserResponse(**current_user.dict())
    }