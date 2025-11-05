from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from .models import ChatRequest, ChatResponse, AgentStatus, HealthCheck, FeedbackRequest
from .api import (
    health_check,
    chat_endpoint,
    agent_status,
    clear_session_endpoint,
    get_session_context,
    submit_feedback,
    create_session
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
async def feedback(request: Request):
    """Enhanced feedback endpoint that handles both strict and flexible formats"""
    try:
        data = await request.json()
        print(f"Raw feedback data received: {data}")
        
        # Try to parse as FeedbackRequest first
        try:
            feedback_req = FeedbackRequest(**data)
            print(f"Successfully parsed as FeedbackRequest: {feedback_req}")
            return submit_feedback(feedback_req)
        except Exception as validation_error:
            print(f"Validation failed, using flexible parsing: {validation_error}")
            
            # Fall back to flexible parsing - handle various field names
            session_id = data.get("session_id", data.get("sessionId", "unknown"))
            message_id = data.get("message_id", data.get("messageId", data.get("conversation_id", "unknown")))
            
            # Handle feedback_type - check multiple possible fields
            feedback_type = data.get("feedback_type", "unknown")
            if feedback_type == "unknown" and "liked" in data:
                feedback_type = "like" if data["liked"] else "dislike"
                
            user_query = data.get("user_query", data.get("query", ""))
            assistant_response = data.get("assistant_response", data.get("response_text", data.get("response", "")))
            
            from .core.vector_store import vector_store
            
            feedback_id = vector_store.store_conversation_feedback(
                session_id=session_id,
                message_id=message_id,
                user_query=user_query,
                assistant_response=assistant_response,
                feedback_type=feedback_type
            )
            
            message = "helpful" if feedback_type == "like" else "not helpful"
            
            return {
                "status": "success",
                "message": f"Conversation marked as {message}",
                "feedback_id": feedback_id
            }
        
    except Exception as e:
        print(f"Feedback endpoint error: {e}")
        return {
            "status": "error",
            "message": f"Failed to process feedback: {str(e)}"
        }

@app.post("/feedback")
async def feedback_alt(request: Request):
    """Flexible feedback endpoint that accepts any JSON"""
    try:
        data = await request.json()
        print(f"Received feedback data: {data}")
        
        # Extract required fields with defaults - handle all field variations
        session_id = data.get("session_id", "unknown")
        message_id = data.get("message_id", "unknown") 
        feedback_type = data.get("feedback_type", data.get("type", "unknown"))
        user_query = data.get("user_query", data.get("query", ""))
        assistant_response = data.get("assistant_response", 
                                     data.get("response_text", 
                                             data.get("response", "")))
        
        from .core.vector_store import vector_store
        
        feedback_id = vector_store.store_conversation_feedback(
            session_id=session_id,
            message_id=message_id,
            user_query=user_query,
            assistant_response=assistant_response,
            feedback_type=feedback_type
        )
        
        message = "helpful" if feedback_type == "like" else "not helpful"
        
        return {
            "status": "success",
            "message": f"Conversation marked as {message}",
            "feedback_id": feedback_id
        }
        
    except Exception as e:
        print(f"Feedback error: {e}")
        return {
            "status": "error", 
            "message": f"Failed to store feedback: {str(e)}"
        }

@app.get("/agent/status", response_model=AgentStatus)
def status():
    return agent_status()

@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    return clear_session_endpoint(session_id)

@app.get("/session/{session_id}")
def get_session(session_id: str):
    return get_session_context(session_id)

@app.post("/session/create")
def new_session():
    return create_session()

@app.post("/admin/reprocess-documents")
def reprocess_documents():
    """Manually trigger document reprocessing (including image extraction)"""
    try:
        from .core.vector_store import vector_store
        from .core.document_processor import doc_processor
        
        # Check for new documents
        if not doc_processor.has_new_documents():
            return {"status": "info", "message": "No new documents to process"}
        
        # Process documents
        result = doc_processor.process_new_documents()
        
        if result['processed']:
            # Store in vector database
            for doc in result['processed']:
                vector_store.add_document(
                    doc_id=doc['doc_id'],
                    content=doc['content'],
                    metadata=doc['metadata'],
                    doc_type=doc['doc_type']
                )
        
        return {
            "status": "success",
            "message": f"Processed {result['count']} documents",
            "processed_files": [doc['metadata']['filename'] for doc in result['processed']],
            "errors": result['errors'],
            "images_extracted": sum(len(doc['metadata'].get('images', [])) for doc in result['processed'])
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to reprocess documents: {str(e)}"}

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
