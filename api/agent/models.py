from typing import Optional, Literal
from pydantic import BaseModel

class IncomingMessage(BaseModel):
    type: Literal["text", "image", "audio", "video", "document"]
    path: Optional[str] = None
    caption: Optional[str] = None
    mime_type: Optional[str] = None


class AgentResponse(BaseModel):
    type: Literal[
        "text",
        "image",
        "document",
        "video",
        "not_found"
    ]
    message: str | None
    path: str | None