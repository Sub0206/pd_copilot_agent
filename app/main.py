from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatRequest, ChatResponse, AgentStatus, HealthCheck, FeedbackRequest
from .api import (
    health_check,
    chat_endpoint,
    agent_status,
    clear_session_endpoint,
    get_session_context,
    submit_feedback
)

app = FastAPI(
    title="PD Copilot Agent API",
    description="AI Agent for Product Designer with Agentic SDK + RAG",
    version="1.0.0"
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

@app.post("/api/feedback")
def feedback(request: FeedbackRequest):
    return submit_feedback(request)

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
    print("🚀 PD COPILOT AGENT API (Agentic SDK + RAG)")
    print("=" * 60)
    
    # Initialize vector store and process documents
    try:
        from .core.vector_store import vector_store
        from .core.document_processor import doc_processor
        
        print("📂 Checking for new documents...")
        if doc_processor.has_new_documents():
            print("📄 Processing new documents...")
            result = doc_processor.process_new_documents()
            
            if result["processed"]:
                print(f"✓ Processing {len(result['processed'])} documents...")
                for doc in result["processed"]:
                    vector_store.add(
                        doc_id=doc["doc_id"],
                        content=doc["content"],
                        metadata=doc["metadata"],
                        doc_type=doc["doc_type"]
                    )
                print(f"✓ Successfully indexed {len(result['processed'])} documents")
            
            if result["errors"]:
                print(f"⚠️  Errors processing {len(result['errors'])} documents:")
                for error in result["errors"]:
                    print(f"   - {error}")
        else:
            print("✓ No new documents to process")
            
        # Show current document count
        total_docs = vector_store.count()
        feature_docs = vector_store.count(doc_type="feature")
        config_docs = vector_store.count(doc_type="config")
        print(f"📊 Vector store contains {total_docs} documents")
        print(f"   - Feature docs: {feature_docs}")
        print(f"   - Config docs: {config_docs}")
        
    except Exception as e:
        print(f"⚠️  Error during startup indexing: {e}")
        print("   Vector store features will be limited")
    
    print("✓ OrderSense validation ready")
    print("✓ Feature & Config agents initialized")
    print("✓ Documentation at /docs")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
