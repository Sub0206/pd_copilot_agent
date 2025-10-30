"""
API handlers for PD Copilot Agent
"""

import sys
import os
from fastapi import HTTPException
from fastapi import Response
from ..models import ChatRequest, ChatResponse

# Import the PD Copilot Agent with relative import
from ..agents.pd_copilot_agent import PDCopilotAgent

# Initialize the agent globally
agent = PDCopilotAgent()

def root():
    return {
        "message": "PD Copilot Agent is running successfully!",
        "version": "1.0.0",
        "status": "healthy"
    }

def health_check():
    return {"status": "healthy", "service": "PD Copilot Agent"}

async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint using PD Copilot Agent
    """
    try:
        # Use the PD Copilot Agent to process the message
        result = await agent.process_message(
            message=request.message,
            session_id=request.session_id or "default"
        )
        
        return ChatResponse(
            response=result["response"],
            status=result["status"],
            session_id=result["session_id"],
            metadata={"agent": "PD Copilot", "processed": True}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent processing error: {str(e)}")

async def chat_stream_endpoint(request: ChatRequest):
    return {"message": "Streaming endpoint - to be implemented"}

def agent_status():
    return {
        "agent_status": "ready",
        "agent_name": "PD Copilot Agent",
        "capabilities": [
            "intent_understanding",
            "dynamic_agent_routing", 
            "ordersense_analysis",
            "feature_information",
            "configuration_guidance"
        ]
    }

def favicon():
    return Response(status_code=204)