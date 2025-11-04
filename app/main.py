from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatRequest, ChatResponse, AgentStatus, HealthCheck, FeedbackRequest
from .api import (
    health_check,
    chat_endpoint,
    agent_status,
    clear_session_endpoint,
    get_session_context,
    get_all_sessions,
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

@app.get("/sessions")
def list_sessions():
    """Get all active sessions summary"""
    return get_all_sessions()

@app.get("/debug/vector-store")
def debug_vector_store():
    """Debug endpoint to check vector store status"""
    from .core.vector_store import vector_store
    from .core.document_processor import doc_processor
    
    try:
        return {
            "status": "ok",
            "vector_store_connected": vector_store.is_connected(),
            "total_documents": vector_store.count(),
            "feature_docs": vector_store.count(doc_type="feature"),
            "config_docs": vector_store.count(doc_type="config"),
            "general_docs": vector_store.count(doc_type="general"),
            "has_new_docs_to_process": doc_processor.has_new_documents(),
            "docs_path": doc_processor.docs_path.as_posix()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.on_event("startup")
async def startup():
    print("\n" + "=" * 60)
    print("🚀 PD COPILOT AGENT API (Agentic SDK + RAG)")
    print("=" * 60)
    
    try:
        from .core.vector_store import vector_store
        from .core.document_processor import doc_processor
        
        print("📂 Checking vector store connection...")
        if not vector_store.is_connected():
            print("⚠️  Vector store not connected! Connecting now...")
            vector_store._ensure_connection()
        
        print("✓ Vector store connected")
        
        print("\n📊 Current Vector Store Status:")
        print(f"   Total documents: {vector_store.count()}")
        print(f"   Feature docs: {vector_store.count(doc_type='feature')}")
        print(f"   Config docs: {vector_store.count(doc_type='config')}")
        print(f"   General docs: {vector_store.count(doc_type='general')}")
        
        if vector_store.count() == 0:
            print("\n⚠️  WARNING: No documents in vector store!")
            print("   Action needed: Add documents to ./resource/pd_docs/")
            print("   Then restart the server to index them.")
        
        print("\n📄 Checking for new documents...")
        if doc_processor.has_new_documents():
            print("✓ Found new documents to process")
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
                print(f"⚠️  Errors: {len(result['errors'])}")
                for error in result["errors"]:
                    print(f"   - {error}")
        else:
            print("✓ No new documents to process")
        
        print("\n✓ OrderSense validation ready")
        print("✓ Feature & Config agents initialized")
        print("✓ Documentation at /docs")
        print("✓ Debug endpoint at /debug/vector-store")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n⚠️  STARTUP ERROR: {e}")
        print("   Some features may not work correctly")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
