"""
Chat-related Pydantic models
"""

from pydantic import BaseModel
from typing import Dict, Any, Optional


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    status: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None