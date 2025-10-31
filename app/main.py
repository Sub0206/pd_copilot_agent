from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import ChatRequest, ChatResponse, AgentStatus, HealthCheck
from app.api.api_handlers import (
    health_check,
    chat_endpoint,
    agent_status,
    clear_session_endpoint,
    get_session_context
)

app = FastAPI(
    title="PD Copilot Agent API",
    description="AI Agent for Product Designer - Tab order validation, feature help, and configuration guidance",
    version="1.0.0",
    debug=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthCheck)
def health():
    return health_check()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    return await chat_endpoint(request)


@app.get("/agent/status", response_model=AgentStatus)
def status():
    return agent_status()


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    return clear_session_endpoint(session_id)


@app.get("/session/{session_id}")
def get_session(session_id: str):
    return get_session_context(session_id)


@app.on_event("startup")
async def startup():
    print("\n" + "=" * 60)
    print("🚀 PD COPILOT AGENT API")
    print("=" * 60)
    print("✓ OrderSense validation ready")
    print("✓ Documentation at /docs")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
