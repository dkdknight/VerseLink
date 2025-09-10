from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid

class ChatContext(str, Enum):
    EVENT = "event"
    MATCH = "match"

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    context: ChatContext
    context_id: str
    sender_id: str
    sender_handle: str
    content: str = Field(..., max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True