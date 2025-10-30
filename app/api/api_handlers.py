"""
API handlers for PD Copilot Agent
Handles all endpoint logic for FastAPI routes
"""

from fastapi import HTTPException, Response
from ..models import ChatRequest, ChatResponse, AgentStatus, HealthCheck
from ..agents.pd_copilot_agent import PDCopilotAgent
import uuid
from datetime import datetime

# Initialize the agent globally
pd_copilot = PDCopilotAgent()


# ============================================================================
# ENDPOINT HANDLERS
# ============================================================================

def root():
    """Root endpoint - service information"""
    return {
        "message": "PD Copilot Agent is running successfully!",
        "service": "PD Copilot Agent API",
        "version": "1.0.0",
        "status": "healthy",
        "documentation": "/docs",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "status": "/agent/status"
        }
    }


def health_check() -> HealthCheck:
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        service="PD Copilot Agent",
        version="1.0.0"
    )


async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Process chat messages with PD Copilot Agent
    
    Args:
        request: ChatRequest with user message and optional session info
        
    Returns:
        ChatResponse with agent's response and metadata
        
    Raises:
        HTTPException: If agent processing fails
    """
    try:
        # Use the PD Copilot Agent to process the message
        result = await pd_copilot.process_message(
            message=request.message,
            session_id=request.session_id or "default"
        )
        
        # Return response in the correct format that matches ChatResponse model
        return ChatResponse(
            message=result["response"],  # Use 'message' not 'response'
            session_id=request.session_id or "default",
            status="success",
            metadata={
                "timestamp": datetime.now().isoformat(),
                "model": "pd-copilot-agent",
                "tokens_used": 0,
                "processing_time": 0.1
            }
        )
        
    except Exception as e:
        # Return error response in correct format
        return ChatResponse(
            message=f"Error processing request: {str(e)}",
            session_id=request.session_id or "default", 
            status="error",
            metadata={
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )


async def chat_stream_endpoint(request: ChatRequest):
    """
    Streaming chat endpoint (future implementation)
    
    Will support real-time streaming of agent responses
    """
    return {
        "message": "Streaming endpoint - to be implemented",
        "status": "not_implemented",
        "note": "Use /chat endpoint for non-streaming responses"
    }


def agent_status() -> AgentStatus:
    """
    Agent status endpoint
    
    Returns current status and capabilities of PD Copilot Agent
    """
    return AgentStatus(
        agent_status="ready",
        agent_name="PD Copilot Agent",
        capabilities=[
            "intent_recognition",
            "ordersense_validation", 
            "tab_order_analysis",
            "feature_information",
            "configuration_guidance",
            "conversation_context"
        ],
        tools=[
            "fetch_database_info",
            "parse_database_info",
            "analyze_view_items",
            "generate_report",
            "evaluate_report"
        ]
    )


def clear_session_endpoint(session_id: str):
    """
    Clear conversation context for a session
    
    Args:
        session_id: Session identifier to clear
        
    Returns:
        Confirmation message
    """
    try:
        pd_copilot.clear_session(session_id)
        return {
            "status": "success",
            "message": f"Session {session_id} cleared successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing session: {str(e)}"
        )


def get_session_context(session_id: str):
    """
    Get conversation context for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session context with conversation history
    """
    try:
        context = pd_copilot.get_session_context(session_id)
        return {
            "status": "success",
            "session_id": session_id,
            "context": context
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving session context: {str(e)}"
        )


def favicon():
    """Favicon endpoint - returns 204 No Content"""
    return Response(status_code=204)
