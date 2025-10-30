"""
FastAPI Application for PD Copilot Agent
Main entry point for the API service
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatRequest, ChatResponse, AgentStatus, HealthCheck
from .api.api_handlers import (
    root,
    health_check,
    chat_endpoint,
    chat_stream_endpoint,
    agent_status,
    clear_session_endpoint,
    get_session_context,
    favicon
)

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="PD Copilot Agent API",
    description="""
    AI Agent service for Product Designer application.
    
    Features:
    - Intent recognition and classification
    - OrderSense tab order validation
    - Feature information and guidance
    - Configuration assistance
    - Conversation context management
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# CORS MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", tags=["General"])
def root_endpoint():
    """
    Root endpoint - Returns service information
    """
    return root()


@app.get("/health", response_model=HealthCheck, tags=["General"])
def health_endpoint():
    """
    Health check endpoint - Returns service health status
    """
    return health_check()


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_api(request: ChatRequest):
    """
    Main chat endpoint - Process user messages with PD Copilot Agent
    
    Supports:
    - OrderSense validation workflows
    - Feature information queries
    - Configuration guidance
    - Context-aware conversations
    
    Example Request:
    ```json
    {
        "message": "Check order violations in interface tag X",
        "session_id": "user123",
        "context": {}
    }
    ```
    """
    return await chat_endpoint(request)


@app.post("/chat/stream", tags=["Chat"])
async def chat_stream_api(request: ChatRequest):
    """
    Streaming chat endpoint - For real-time response streaming (Future)
    
    Note: Currently not implemented. Use /chat for standard responses.
    """
    return await chat_stream_endpoint(request)


@app.get("/agent/status", response_model=AgentStatus, tags=["Agent"])
def agent_status_api():
    """
    Agent status endpoint - Returns agent capabilities and status
    
    Provides information about:
    - Agent operational status
    - Available capabilities
    - Integrated tools
    """
    return agent_status()


@app.delete("/session/{session_id}", tags=["Session"])
def clear_session_api(session_id: str):
    """
    Clear session context - Removes conversation history for a session
    
    Args:
        session_id: Session identifier to clear
    """
    return clear_session_endpoint(session_id)


@app.get("/session/{session_id}", tags=["Session"])
def get_session_api(session_id: str):
    """
    Get session context - Retrieves conversation history for a session
    
    Args:
        session_id: Session identifier
    """
    return get_session_context(session_id)


@app.get("/favicon.ico", include_in_schema=False)
def favicon_api():
    """Favicon endpoint"""
    return favicon()


# ============================================================================
# APPLICATION STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Application startup event
    Prints initialization information
    """
    print("\n" + "=" * 70)
    print("🚀 PD COPILOT AGENT API STARTING")
    print("=" * 70)
    print("✓ Agent initialized with OrderSense tools")
    print("✓ FastAPI application ready")
    print("✓ API documentation available at /docs")
    print("=" * 70 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown event
    """
    print("\n" + "=" * 70)
    print("🛑 PD COPILOT AGENT API SHUTTING DOWN")
    print("=" * 70 + "\n")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
