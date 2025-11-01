from fastapi import HTTPException
from ..models import FeedbackRequest
from datetime import datetime

def submit_feedback(feedback: FeedbackRequest):
    """Store user-approved responses for continuous learning"""
    
    if feedback.feedback_type != "like":
        return {"status": "skipped", "message": "Only liked responses are stored"}
    
    try:
        from ..core.vector_store import vector_store
        
        doc_id = f"approved_{feedback.session_id}_{feedback.message_id}_{int(datetime.now().timestamp())}"
        content = f"User Query: {feedback.user_query}\n\nApproved Response:\n{feedback.assistant_response}"
        
        metadata = {
            "type": "user_approved",
            "session_id": feedback.session_id,
            "message_id": feedback.message_id,
            "query": feedback.user_query,
            "approved_at": datetime.now().isoformat()
        }
        
        vector_store.add(
            doc_id=doc_id,
            content=content,
            metadata=metadata,
            doc_type=feedback.doc_type
        )
        
        return {
            "status": "success",
            "message": "Response approved and stored for learning",
            "doc_id": doc_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store feedback: {str(e)}")