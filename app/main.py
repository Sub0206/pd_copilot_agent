from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import models with relative imports
from .models import ChatRequest, ChatResponse

# Import API handlers with relative imports
from .api.api_handlers import (
    root,
    health_check,
    chat_endpoint,
    chat_stream_endpoint,
    agent_status,
    favicon
)

app = FastAPI(
    title="PD Copilot Agent",
    description="AI Agent service for chatbot integration",
    version="1.0.0"
)

# Add CORS middleware for chatbot integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API endpoints
@app.get("/")
def root_endpoint():
    return root()

@app.get("/health")
def health_endpoint():
    return health_check()

@app.post("/chat", response_model=ChatResponse)
async def chat_api(request: ChatRequest):
    return await chat_endpoint(request)

@app.post("/chat/stream")
async def chat_stream_api(request: ChatRequest):
    return await chat_stream_endpoint(request)

@app.get("/agent/status")
def agent_status_api():
    return agent_status()

@app.get("/favicon.ico")
def favicon_api():
    return favicon()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
