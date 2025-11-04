# app/models.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(default="default", description="Session identifier")
    context: Optional[Dict] = Field(default={}, description="Additional context")

class ChatResponse(BaseModel):
    message: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session identifier")
    status: str = Field(..., description="Response status")
    metadata: Optional[Dict] = Field(default={}, description="Response metadata")

class HealthCheck(BaseModel):
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    metadata: Optional[Dict] = Field(default={}, description="Additional health info")

class AgentStatus(BaseModel):
    agent_status: str = Field(..., description="Agent operational status")
    agent_name: str = Field(..., description="Agent name")
    capabilities: List[str] = Field(..., description="Agent capabilities")
    tools: List[str] = Field(..., description="Available tools")
    metadata: Optional[Dict] = Field(default={}, description="Additional agent metadata")

class FeedbackRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    message_id: str = Field(..., description="Message identifier")
    user_query: str = Field(..., description="Original user query")
    assistant_response: str = Field(..., description="Assistant response to approve")
    feedback_type: str = Field(..., description="'like' or 'dislike'")
    doc_type: Optional[str] = Field(default="general", description="Document type")