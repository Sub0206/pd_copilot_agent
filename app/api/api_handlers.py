from fastapi import HTTPException
from ..models import ChatRequest, ChatResponse, AgentStatus, HealthCheck
from ..agents.pd_copilot_agent import PDCopilotAgent
from datetime import datetime

pd_copilot = PDCopilotAgent()


def health_check() -> HealthCheck:
    """Health check endpoint with vector store status"""
    try:
        from ..core.vector_store import vector_store
        
        # Check if vector store is connected
        is_connected = vector_store.is_connected()
        doc_count = vector_store.count() if is_connected else 0
        
        return HealthCheck(
            status="healthy" if is_connected else "degraded",
            service="PD Copilot Agent",
            version="1.0.0",
            metadata={
                "vector_store_connected": is_connected,
                "indexed_documents": doc_count
            }
        )
    except Exception:
        return HealthCheck(
            status="healthy",
            service="PD Copilot Agent",
            version="1.0.0"
        )


async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Process chat messages with enhanced metadata tracking
    
    Returns response with:
    - Message content
    - Session ID
    - Status (success/error)
    - Metadata (timestamp, message count, extracted params)
    """
    try:
        result = await pd_copilot.process_message(
            message=request.message,
            session_id=request.session_id or "default"
        )
        
        # Extract metadata from result
        result_metadata = result.get("metadata", {})
        
        return ChatResponse(
            message=result["response"],
            session_id=result["session_id"],
            status=result["status"],
            metadata={
                "timestamp": datetime.now().isoformat(),
                "model": "pd-copilot-agent",
                "message_count": result_metadata.get("message_count", 0),
                "extracted_params": result_metadata.get("extracted_params", {}),
                "session_active": True
            }
        )
    except Exception as e:
        return ChatResponse(
            message=f"Error: {str(e)}",
            session_id=request.session_id or "default",
            status="error",
            metadata={
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "error_type": type(e).__name__
            }
        )


def agent_status() -> AgentStatus:
    """
    Get agent status with enhanced capability tracking
    """
    try:
        from ..core.vector_store import vector_store
        
        # Get vector store stats
        total_docs = vector_store.count() if vector_store.is_connected() else 0
        feature_docs = vector_store.count(doc_type="feature") if vector_store.is_connected() else 0
        config_docs = vector_store.count(doc_type="config") if vector_store.is_connected() else 0
        
        # Get active sessions count
        active_sessions = len(pd_copilot.sessions)
        
        return AgentStatus(
            agent_status="ready",
            agent_name="PD Copilot",
            capabilities=[
                "tab_order_validation",
                "feature_explanation",
                "configuration_guidance",
                "documentation_search",
                "conversation_memory",
                "parameter_extraction"
            ],
            tools=[
                "run_ordersense_validation",
                "explain_feature",
                "search_documentation",
                "guide_configuration",
                "validate_configuration"
            ],
            metadata={
                "vector_store_docs": total_docs,
                "feature_docs": feature_docs,
                "config_docs": config_docs,
                "active_sessions": active_sessions,
                "sub_agents": ["Feature Expert", "Config Copilot", "OrderSense Validator"]
            }
        )
    except Exception as e:
        # Fallback if vector store is not available
        return AgentStatus(
            agent_status="ready",
            agent_name="PD Copilot",
            capabilities=[
                "tab_order_validation",
                "feature_explanation",
                "configuration_guidance",
                "conversation_memory"
            ],
            tools=[
                "run_ordersense_validation",
                "explain_feature",
                "guide_configuration"
            ],
            metadata={
                "error": "Vector store status unavailable",
                "active_sessions": len(pd_copilot.sessions)
            }
        )


def clear_session_endpoint(session_id: str):
    """
    Clear a specific session and all its context
    """
    try:
        # Get session info before clearing
        session = pd_copilot.get_session(session_id)
        message_count = len(session.get("messages", []))
        
        pd_copilot.clear_session(session_id)
        
        return {
            "status": "success",
            "message": f"Session {session_id} cleared",
            "details": {
                "session_id": session_id,
                "messages_cleared": message_count,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        )


def get_session_context(session_id: str):
    """
    Get detailed session context including messages and extracted parameters
    """
    try:
        session = pd_copilot.get_session(session_id)
        
        # Get session statistics
        messages = session.get("messages", [])
        extracted_params = session.get("extracted_params", {})
        current_topic = session.get("current_topic")
        
        # Calculate message statistics
        user_messages = sum(1 for msg in messages if msg.get("role") == "user")
        assistant_messages = sum(1 for msg in messages if msg.get("role") == "assistant")
        
        return {
            "status": "success",
            "session_id": session_id,
            "context": {
                "messages": messages[-10:],  # Return last 10 messages only
                "extracted_params": extracted_params,
                "current_topic": current_topic
            },
            "statistics": {
                "total_messages": len(messages),
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "parameters_extracted": len(extracted_params),
                "session_created": messages[0].get("timestamp") if messages else None
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "session_active": len(messages) > 0
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        )


def get_all_sessions():
    """
    Get summary of all active sessions (new endpoint)
    """
    try:
        sessions_summary = []
        
        for session_id, session_data in pd_copilot.sessions.items():
            messages = session_data.get("messages", [])
            extracted_params = session_data.get("extracted_params", {})
            
            sessions_summary.append({
                "session_id": session_id,
                "message_count": len(messages),
                "extracted_params": extracted_params,
                "last_activity": messages[-1].get("timestamp") if messages else None,
                "active": len(messages) > 0
            })
        
        return {
            "status": "success",
            "total_sessions": len(sessions_summary),
            "sessions": sessions_summary,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )