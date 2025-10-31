from fastapi import HTTPException
from ..models import ChatRequest, ChatResponse, AgentStatus, HealthCheck
from ..agents.pd_copilot_agent import PDCopilotAgent
from datetime import datetime

pd_copilot = PDCopilotAgent()


def health_check() -> HealthCheck:
    return HealthCheck(
        status="healthy",
        service="PD Copilot Agent",
        version="1.0.0"
    )


async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    try:
        result = await pd_copilot.process_message(
            message=request.message,
            session_id=request.session_id or "default"
        )
        
        return ChatResponse(
            message=result["response"],
            session_id=result["session_id"],
            status=result["status"],
            metadata={
                "timestamp": datetime.now().isoformat(),
                "model": "pd-copilot-agent"
            }
        )
    except Exception as e:
        return ChatResponse(
            message=f"Error: {str(e)}",
            session_id=request.session_id or "default",
            status="error",
            metadata={"timestamp": datetime.now().isoformat(), "error": str(e)}
        )


def agent_status() -> AgentStatus:
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
        ]
    )


def clear_session_endpoint(session_id: str):
    try:
        pd_copilot.clear_session(session_id)
        return {"status": "success", "message": f"Session {session_id} cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_session_context(session_id: str):
    try:
        context = pd_copilot.get_session(session_id)
        return {
            "status": "success",
            "session_id": session_id,
            "context": context,
            "message_count": len(context.get("messages", []))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
