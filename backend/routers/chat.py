from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from typing import List
from models.chat import ChatMessage, ChatContext
from models.user import User
from middleware.auth import get_current_active_user, JWT_SECRET_KEY, JWT_ALGORITHM
from jose import jwt, JWTError
from services.chat_service import ChatService

router = APIRouter(tags=["Chat"])
chat_service = ChatService()

class ConnectionManager:
    def __init__(self):
        self.rooms: dict[str, list[WebSocket]] = {}

    def _room(self, context: ChatContext, context_id: str) -> str:
        return f"{context}:{context_id}"

    async def connect(self, websocket: WebSocket, context: ChatContext, context_id: str):
        room = self._room(context, context_id)
        await websocket.accept()
        self.rooms.setdefault(room, []).append(websocket)

    def disconnect(self, websocket: WebSocket, context: ChatContext, context_id: str):
        room = self._room(context, context_id)
        if room in self.rooms and websocket in self.rooms[room]:
            self.rooms[room].remove(websocket)

    async def broadcast(self, context: ChatContext, context_id: str, message: ChatMessage):
        room = self._room(context, context_id)
        for ws in self.rooms.get(room, []):
            await ws.send_json(jsonable_encoder(message))

manager = ConnectionManager()

@router.get("/events/{event_id}/messages", response_model=List[ChatMessage])
async def get_event_messages(event_id: str, current_user: User = Depends(get_current_active_user)):
    if not await chat_service._is_event_participant(event_id, current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    return await chat_service.get_messages(ChatContext.EVENT, event_id)

@router.post("/events/{event_id}/messages", response_model=ChatMessage)
async def post_event_message(event_id: str, data: dict, current_user: User = Depends(get_current_active_user)):
    content = data.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="Content required")
    message = await chat_service.create_event_message(event_id, current_user, content)
    await manager.broadcast(ChatContext.EVENT, event_id, message)
    return message

@router.get("/matches/{match_id}/messages", response_model=List[ChatMessage])
async def get_match_messages(match_id: str, current_user: User = Depends(get_current_active_user)):
    if not await chat_service._is_match_captain(match_id, current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    return await chat_service.get_messages(ChatContext.MATCH, match_id)

@router.post("/matches/{match_id}/messages", response_model=ChatMessage)
async def post_match_message(match_id: str, data: dict, current_user: User = Depends(get_current_active_user)):
    content = data.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="Content required")
    message = await chat_service.create_match_message(match_id, current_user, content)
    await manager.broadcast(ChatContext.MATCH, match_id, message)
    return message

@router.websocket("/ws/{context}/{context_id}")
async def websocket_endpoint(websocket: WebSocket, context: ChatContext, context_id: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close()
        return
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
    except JWTError:
        await websocket.close()
        return
    # Permission check
    if context == ChatContext.EVENT:
        allowed = await chat_service._is_event_participant(context_id, user_id)
    else:
        allowed = await chat_service._is_match_captain(context_id, user_id)
    if not allowed:
        await websocket.close()
        return
    await manager.connect(websocket, context, context_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, context, context_id)