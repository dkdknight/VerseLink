from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from decouple import config
import httpx
from typing import Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid
import secrets
from fastapi.security import HTTPAuthorizationCredentials

from database import get_database
from models.user import User, UserCreate, UserResponse, UserProfile
from middleware.auth import (
    create_access_token,
    get_current_active_user,
    revoke_token,
    security,
)

class DiscordCallbackRequest(BaseModel):
    code: str
    state: str
    remember_me: bool = False

router = APIRouter()

# Discord OAuth Configuration
DISCORD_CLIENT_ID = config("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = config("DISCORD_CLIENT_SECRET")  
DISCORD_REDIRECT_URI = config("DISCORD_REDIRECT_URI")

# Environment Configuration
ENVIRONMENT = config("ENVIRONMENT", default="development")

# Validation de la configuration
if DISCORD_CLIENT_SECRET in ["dummy", "VOTRE_DISCORD_CLIENT_SECRET", "VOTRE_VRAI_CLIENT_SECRET_ICI"]:
    print("❌ ERREUR: DISCORD_CLIENT_SECRET n'est pas configuré correctement!")
    print("❌ Veuillez mettre à jour le fichier .env avec le vrai Client Secret Discord")

print(f"🔍 Discord Config - Client ID: {DISCORD_CLIENT_ID}")
print(f"🔍 Discord Config - Redirect URI: {DISCORD_REDIRECT_URI}")
print(f"🔍 Discord Config - Client Secret: {'✅ Configuré' if DISCORD_CLIENT_SECRET not in ['dummy', 'VOTRE_DISCORD_CLIENT_SECRET', 'VOTRE_VRAI_CLIENT_SECRET_ICI'] else '❌ Non configuré'}")

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

oauth_state_cache: Dict[str, datetime] = {}

@router.get("/discord/redirect")
async def discord_auth_redirect():
    """Redirect to Discord OAuth"""
    state = secrets.token_urlsafe(32)
    oauth_state_cache[state] = datetime.utcnow()

    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={DISCORD_CLIENT_ID}"
        f"&redirect_uri={DISCORD_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify email guilds"
        f"&state={state}"
    )
    return {"auth_url": discord_auth_url}

@router.post("/discord/callback")
async def discord_auth_callback(request: DiscordCallbackRequest):
    """Handle Discord OAuth callback"""
    if request.state not in oauth_state_cache:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    oauth_state_cache.pop(request.state, None)
    try:
        print(f"🔍 Discord callback received - Code: {request.code[:10]}...")
        print(f"🔍 Client ID: {DISCORD_CLIENT_ID}")
        print(f"🔍 Redirect URI: {DISCORD_REDIRECT_URI}")
        
        # Exchange code for access token
        token_data = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": request.code,
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
            # Merge existing data with updates and construct user model
            user_data = {**existing_user, **update_data}
            user_data.pop("_id", None)
            user = User(**user_data)
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
        
        # Create JWT token with optional extended expiration
        expires_delta = timedelta(days=30) if request.remember_me else None
        access_token = create_access_token(data={"sub": user.id}, expires_delta=expires_delta)
        
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

@router.get("/me")
async def get_current_user(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user"""
    return {
        "user": UserResponse(**current_user.dict())
    }

@router.post("/logout")
async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Handle user logout and revoke the current token"""
    await revoke_token(credentials.credentials)
    return {
        "message": "Déconnexion réussie",
        "success": True
    }

@router.post("/promote-admin")
async def promote_user_to_admin(
    target_discord_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Promote a user to site admin (only existing admins can do this)"""
    
    # Check if current user is admin
    if not current_user.is_site_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les administrateurs peuvent promouvoir d'autres utilisateurs"
        )
    
    db = get_database()
    
    # Find target user
    target_user = await db.users.find_one({"discord_id": target_discord_id})
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utilisateur avec Discord ID {target_discord_id} introuvable"
        )
    
    if target_user.get("is_site_admin"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet utilisateur est déjà administrateur"
        )
    
    # Promote user
    await db.users.update_one(
        {"discord_id": target_discord_id},
        {"$set": {"is_site_admin": True, "updated_at": datetime.utcnow()}}
    )
    
    return {
        "message": f"Utilisateur {target_user.get('handle', target_discord_id)} promu administrateur avec succès",
        "user_id": target_user.get("id"),
        "discord_id": target_discord_id
    }

@router.post("/init-admin")
async def initialize_first_admin():
    """Initialize first admin user (only works if no admins exist)"""
    
    db = get_database()
    
    # Check if any admin already exists
    existing_admin = await db.users.find_one({"is_site_admin": True})
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un administrateur existe déjà. Utilisez /auth/promote-admin pour promouvoir d'autres utilisateurs."
        )
    
    # Find the first user (usually the one who created the system)
    first_user = await db.users.find_one({}, sort=[("created_at", 1)])
    if not first_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun utilisateur trouvé dans le système"
        )
    
    # Promote first user to admin
    await db.users.update_one(
        {"id": first_user["id"]},
        {"$set": {"is_site_admin": True, "updated_at": datetime.utcnow()}}
    )
    
    return {
        "message": f"Premier administrateur initialisé : {first_user.get('handle', first_user.get('discord_username', 'Utilisateur'))}",
        "user_id": first_user["id"],
        "discord_id": first_user.get("discord_id"),
        "instructions": "Cet utilisateur peut maintenant promouvoir d'autres administrateurs via /auth/promote-admin"
    }

@router.post("/create-test-admin")
async def create_test_admin():
    """Create a test admin user for development (DEVELOPMENT ONLY)"""
    
    if ENVIRONMENT == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette fonction n'est disponible qu'en développement"
        )
    
    db = get_database()
    
    # Check if test admin already exists
    existing_test_admin = await db.users.find_one({"discord_id": "test_admin_123"})
    if existing_test_admin:
        # Just promote to admin if exists
        await db.users.update_one(
            {"discord_id": "test_admin_123"},
            {"$set": {"is_site_admin": True, "updated_at": datetime.utcnow()}}
        )
        
        # Create access token for this user
        user = User(**existing_test_admin)
        access_token = create_access_token(data={"sub": user.id})
        
        return {
            "message": "Test admin user ready",
            "access_token": access_token,
            "user": UserResponse(**user.dict()),
            "instructions": "Utilisez ce token pour vous connecter temporairement"
        }
    
    # Create test admin user
    test_user_id = str(uuid.uuid4())
    
    test_user_data = {
        "id": test_user_id,
        "discord_id": "test_admin_123",
        "discord_username": "TestAdmin#0000",
        "handle": "TestAdmin",
        "email": "admin@verselink.test",
        "avatar_url": None,
        "is_site_admin": True,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_login": datetime.utcnow(),
        "strikes": 0,
        "is_banned": False,
        "ban_reason": None,
        "ban_expires_at": None,
        "banned_at": None
    }
    
    await db.users.insert_one(test_user_data)
    
    # Create access token
    user = User(**test_user_data)
    access_token = create_access_token(data={"sub": user.id})
    
    return {
        "message": "Test admin user created successfully",
        "access_token": access_token,
        "user": UserResponse(**user.dict()),
        "instructions": "Sauvegardez ce token et utilisez-le pour vous connecter. Configurez ensuite Discord OAuth correctement."
    }

@router.get("/check")
async def check_auth(current_user: User = Depends(get_current_active_user)):
    """Check if user is authenticated"""
    return {
        "authenticated": True,
        "user": UserResponse(**current_user.dict())
    }