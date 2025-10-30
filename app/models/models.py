"""
Pydantic models for PD Copilot Agent API
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="User's message to the agent")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    session_id: Optional[str] = Field(None, description="Session identifier for conversation tracking")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Check order violations in interface tag X",
                "user_id": "user123",
                "session_id": "session456",
                "context": {}
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    message: str = Field(..., description="Agent's response message")
    status: str = Field(..., description="Response status (success/error)")
    session_id: Optional[str] = Field(None, description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional response metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "I understand you want to validate tab orders...",
                "status": "success",
                "session_id": "session456",
                "metadata": {
                    "agent": "PD Copilot",
                    "tools_available": 5
                }
            }
        }


class AgentStatus(BaseModel):
    """Agent status information"""
    agent_status: str = Field(..., description="Current agent status")
    agent_name: str = Field(..., description="Name of the agent")
    capabilities: list[str] = Field(..., description="List of agent capabilities")
    tools: Optional[list[str]] = Field(None, description="Available tools")


class HealthCheck(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")
