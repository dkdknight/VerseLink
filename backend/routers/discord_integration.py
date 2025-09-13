from fastapi import APIRouter, HTTPException, status, Depends, Header, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import hmac
import hashlib
import httpx
import json
import logging
from datetime import datetime
from decouple import config

from database import get_database
from middleware.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()

DISCORD_BOT_WEBHOOK_SECRET = config("DISCORD_BOT_WEBHOOK_SECRET", default="your-super-secret-webhook-key-change-this-in-production")
DISCORD_BOT_WEBHOOK_URL = config("DISCORD_BOT_WEBHOOK_URL", default="http://localhost:8050/webhook")

# Modèles Pydantic pour les webhooks
class EventWebhookData(BaseModel):
    event: Dict[str, Any]
    org_id: str

class TournamentWebhookData(BaseModel):
    tournament: Dict[str, Any]
    org_id: str

class TestConnectionData(BaseModel):
    org_id: str
    test_type: str = "connection"  # connection, events_channel, tournaments_channel

class OrganizationDiscordConfig(BaseModel):
    discord_guild_id: str
    discord_guild_name: str
    events_channel_id: str
    events_channel_name: str
    tournaments_channel_id: Optional[str] = None
    tournaments_channel_name: Optional[str] = None
    auto_publish_events: bool = True
    auto_publish_tournaments: bool = True

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify Discord webhook HMAC signature"""
    if not DISCORD_BOT_WEBHOOK_SECRET:
        return True  # Skip verification if no secret configured
    
    expected_signature = hmac.new(
        DISCORD_BOT_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

def create_webhook_signature(payload: bytes, secret: str) -> str:
    """Crée une signature HMAC pour sécuriser les webhooks sortants"""
    return hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()

async def send_webhook_to_bot(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Envoie un webhook au bot Discord"""
    try:
        payload = json.dumps(data).encode('utf-8')
        signature = f"sha256={create_webhook_signature(payload, DISCORD_BOT_WEBHOOK_SECRET)}"
        
        headers = {
            'Content-Type': 'application/json',
            'X-Webhook-Signature': signature
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{DISCORD_BOT_WEBHOOK_URL}/{endpoint}",
                content=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
            
    except httpx.RequestError as e:
        logger.error(f"Network error sending webhook to bot: {e}")
        raise HTTPException(status_code=503, detail="Discord bot unavailable")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error from bot webhook: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=f"Bot webhook error: {e.response.text}")
    except Exception as e:
        logger.error(f"Unexpected error sending webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/events/announce")
async def discord_event_announce(
    payload: Dict[str, Any],
    x_signature_256: Optional[str] = Header(None)
):
    """Webhook endpoint for Discord bot to announce events"""
    # TODO: Implement signature verification
    # if x_signature_256 and not verify_webhook_signature(request.body, x_signature_256):
    #     raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Placeholder for Discord bot integration
    return {"message": "Event announcement received", "payload": payload}

@router.post("/matches/announce")
async def discord_match_announce(
    payload: Dict[str, Any],
    x_signature_256: Optional[str] = Header(None)
):
    """Webhook endpoint for Discord bot to announce matches"""
    # TODO: Implement signature verification
    
    # Placeholder for Discord bot integration
    return {"message": "Match announcement received", "payload": payload}

@router.post("/relay/event")
async def relay_event_to_discord(
    payload: Dict[str, Any],
    current_user = Depends(get_current_active_user)
):
    """API endpoint for site to request Discord bot to relay events"""
    # TODO: Implement actual Discord bot API calls
    
    required_fields = ["event_id", "targets", "action"]
    for field in required_fields:
        if field not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    # Validate action
    if payload["action"] not in ["create", "update", "delete"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be create, update, or delete"
        )
    
    # TODO: Queue job to call Discord bot API
    return {
        "message": "Event relay queued",
        "event_id": payload["event_id"],
        "targets": payload["targets"],
        "action": payload["action"]
    }

@router.post("/relay/remind")
async def relay_reminder_to_discord(
    payload: Dict[str, Any],
    current_user = Depends(get_current_active_user)
):
    """API endpoint for site to request Discord bot to send reminders"""
    required_fields = ["event_id", "when"]
    for field in required_fields:
        if field not in payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
    
    # Validate when
    if payload["when"] not in ["J-3", "J-1", "H-1", "custom"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="When must be J-3, J-1, H-1, or custom"
        )
    
    # TODO: Queue reminder job
    return {
        "message": "Reminder queued",
        "event_id": payload["event_id"],
        "when": payload["when"]
    }

@router.get("/health")
async def discord_integration_health():
    """Health check for Discord integration"""
    return {
        "status": "healthy",
        "webhook_secret_configured": bool(DISCORD_BOT_WEBHOOK_SECRET),
        "message": "Discord integration endpoints ready"
    }

# NOUVELLES ROUTES POUR LA PUBLICATION AUTOMATIQUE

@router.post("/publish-event")
async def publish_event_to_discord(
    webhook_data: EventWebhookData,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_active_user)
):
    """Publie un événement sur Discord depuis le site web"""
    try:
        # Vérifier que l'utilisateur a les permissions sur l'organisation
        db = get_database()
        org = await db.organizations.find_one({"_id": webhook_data.org_id})
        
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Vérifier les permissions (owner ou admin)
        if org["owner_id"] != current_user.id:
            # Vérifier si l'utilisateur est admin de l'organisation
            member = await db.organization_members.find_one({
                "organization_id": webhook_data.org_id,
                "user_id": current_user.id,
                "role": {"$in": ["admin", "moderator"]}
            })
            if not member:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Envoyer le webhook au bot Discord
        result = await send_webhook_to_bot("event-created", webhook_data.dict())
        
        return {
            "message": "Event publication triggered",
            "discord_result": result
        }
        
    except Exception as e:
        logger.error(f"Error publishing event to Discord: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/publish-tournament")
async def publish_tournament_to_discord(
    webhook_data: TournamentWebhookData,
    background_tasks: BackgroundTasks,
    current_user = Depends(get_current_active_user)
):
    """Publie un tournoi sur Discord depuis le site web"""
    try:
        # Vérifications de permissions similaires
        db = get_database()
        org = await db.organizations.find_one({"_id": webhook_data.org_id})
        
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        if org["owner_id"] != current_user.id:
            member = await db.organization_members.find_one({
                "organization_id": webhook_data.org_id,
                "user_id": current_user.id,
                "role": {"$in": ["admin", "moderator"]}
            })
            if not member:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        result = await send_webhook_to_bot("tournament-created", webhook_data.dict())
        
        return {
            "message": "Tournament publication triggered",
            "discord_result": result
        }
        
    except Exception as e:
        logger.error(f"Error publishing tournament to Discord: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-connection")
async def test_discord_connection(
    test_data: TestConnectionData,
    current_user = Depends(get_current_active_user)
):
    """Teste la connexion Discord pour une organisation depuis le site web"""
    try:
        # Vérifications de permissions
        db = get_database()
        org = await db.organizations.find_one({"_id": test_data.org_id})
        
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        if org["owner_id"] != current_user.id:
            member = await db.organization_members.find_one({
                "organization_id": test_data.org_id,
                "user_id": current_user.id,
                "role": {"$in": ["admin", "moderator"]}
            })
            if not member:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        result = await send_webhook_to_bot("test-connection", test_data.dict())
        
        return result
        
    except Exception as e:
        logger.error(f"Error testing Discord connection: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/orgs/{org_id}/discord-config")
async def update_discord_config(
    org_id: str,
    config: OrganizationDiscordConfig,
    current_user = Depends(get_current_active_user)
):
    """Met à jour la configuration Discord d'une organisation"""
    try:
        db = get_database()
        
        # Vérifier les permissions
        org = await db.organizations.find_one({"_id": org_id})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        if org["owner_id"] != current_user.id:
            member = await db.organization_members.find_one({
                "organization_id": org_id,
                "user_id": current_user.id,
                "role": {"$in": ["admin", "moderator"]}
            })
            if not member:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Mettre à jour la configuration Discord
        config_data = config.dict()
        config_data["updated_at"] = datetime.utcnow()
        config_data["updated_by"] = current_user.id
        
        result = await db.organization_discord_configs.update_one(
            {"organization_id": org_id},
            {"$set": config_data},
            upsert=True
        )
        
        return {
            "message": "Discord configuration updated successfully",
            "config": config_data
        }
        
    except Exception as e:
        logger.error(f"Error updating Discord config: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orgs/{org_id}/discord-config")
async def get_discord_config(
    org_id: str,
    current_user = Depends(get_current_active_user)
):
    """Récupère la configuration Discord d'une organisation"""
    try:
        db = get_database()
        
        # Vérifier l'accès à l'organisation
        org = await db.organizations.find_one({"_id": org_id})
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Récupérer la configuration
        config = await db.organization_discord_configs.find_one({"organization_id": org_id})
        
        if not config:
            raise HTTPException(status_code=404, detail="Discord configuration not found")
        
        # Supprimer les champs internes MongoDB
        config.pop("_id", None)
        
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Discord config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/signup-notification")
async def handle_discord_signup_notification(notification: Dict[str, Any]):
    """Reçoit les notifications d'inscription depuis Discord"""
    try:
        db = get_database()
        
        event_id = notification.get("event_id")
        user_id = notification.get("user_id")
        signup_data = notification.get("signup_data", {})
        
        if not event_id or not user_id:
            raise HTTPException(status_code=400, detail="Missing event_id or user_id")
        
        # Mettre à jour les données d'inscription avec les infos Discord
        signup_update = {
            "discord_signup": True,
            "discord_user_id": signup_data.get("discord_user_id"),
            "discord_username": signup_data.get("discord_username"),
            "signup_source": "discord",
            "discord_notified_at": datetime.utcnow()
        }
        
        # Mettre à jour l'inscription existante
        result = await db.event_signups.update_one(
            {
                "event_id": event_id,
                "user_id": user_id
            },
            {"$set": signup_update}
        )
        
        if result.matched_count == 0:
            logger.warning(f"No existing signup found for user {user_id} in event {event_id}")
        
        return {"message": "Discord signup notification processed"}
        
    except Exception as e:
        logger.error(f"Error processing Discord signup notification: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message-mappings")
async def save_message_mapping(mapping_data: Dict[str, Any]):
    """Sauvegarde le mapping entre message Discord et événement"""
    try:
        db = get_database()
        
        mapping_data["created_at"] = datetime.utcnow()
        
        result = await db.discord_message_mappings.insert_one(mapping_data)
        
        return {
            "message": "Message mapping saved",
            "mapping_id": str(result.inserted_id)
        }
        
    except Exception as e:
        logger.error(f"Error saving message mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/message-mappings/{message_id}")
async def get_message_mapping(message_id: str):
    """Récupère le mapping d'un message Discord"""
    try:
        db = get_database()
        
        mapping = await db.discord_message_mappings.find_one({"message_id": message_id})
        
        if not mapping:
            raise HTTPException(status_code=404, detail="Message mapping not found")
        
        mapping.pop("_id", None)
        return mapping
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting message mapping: {e}")
        raise HTTPException(status_code=500, detail=str(e))