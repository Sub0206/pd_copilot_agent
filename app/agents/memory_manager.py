# app/agents/memory_manager.py
"""
Memory Management System for PD Copilot
Handles conversation memory, parameter tracking, and learning from feedback
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import json

@dataclass
class ConversationMemory:
    """Stores conversation-specific memory"""
    session_id: str
    messages: List[Dict[str, str]] = field(default_factory=list)
    extracted_params: Dict[str, str] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    current_topic: Optional[str] = None
    topic_history: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "session_id": self.session_id,
            "messages": self.messages,
            "extracted_params": self.extracted_params,
            "user_preferences": self.user_preferences,
            "current_topic": self.current_topic,
            "topic_history": self.topic_history,
            "created_at": self.created_at,
            "last_activity": self.last_activity
        }
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_activity = datetime.now().isoformat()
    
    def get_recent_messages(self, count: int = 10) -> List[Dict]:
        """Get recent messages"""
        return self.messages[-count:]
    
    def update_topic(self, topic: str):
        """Update current topic and track history"""
        if self.current_topic and self.current_topic != topic:
            self.topic_history.append(self.current_topic)
        self.current_topic = topic
    
    def get_context_summary(self) -> str:
        """Get summary of current context"""
        summary_parts = []
        
        # Add extracted parameters
        if self.extracted_params:
            params_str = ", ".join([f"{k}={v}" for k, v in self.extracted_params.items()])
            summary_parts.append(f"Parameters: {params_str}")
        
        # Add current topic
        if self.current_topic:
            summary_parts.append(f"Topic: {self.current_topic}")
        
        # Add message count
        summary_parts.append(f"Messages: {len(self.messages)}")
        
        return " | ".join(summary_parts)


class MemoryManager:
    """
    Manages all types of memory for the agent:
    1. Conversation Memory (short-term)
    2. Vector Database access (long-term, external)
    3. Learning Memory (from user feedback)
    """
    
    def __init__(self):
        self.sessions: Dict[str, ConversationMemory] = {}
        self._vector_store = None
    
    @property
    def vector_store(self):
        """Lazy load vector store"""
        if self._vector_store is None:
            from ..core.vector_store import vector_store
            self._vector_store = vector_store
        return self._vector_store
    
    # ========== CONVERSATION MEMORY (Short-term) ==========
    
    def get_or_create_session(self, session_id: str) -> ConversationMemory:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationMemory(session_id=session_id)
        return self.sessions[session_id]
    
    def add_to_conversation(self, session_id: str, role: str, content: str):
        """Add message to conversation memory"""
        session = self.get_or_create_session(session_id)
        session.add_message(role, content)
    
    def extract_and_store_params(self, session_id: str, message: str):
        """Extract parameters from message and store in memory"""
        import re
        
        session = self.get_or_create_session(session_id)
        message_lower = message.lower()
        
        # Extract pt_id
        pt_patterns = [
            r'pt_id[:\s]+(\d+)',
            r'pt[:\s]+(\d+)',
            r'product\s+type[:\s]+(\d+)'
        ]
        for pattern in pt_patterns:
            match = re.search(pattern, message_lower)
            if match:
                session.extracted_params["pt_id"] = match.group(1)
                break
        
        # Extract vTag
        vtag_patterns = [
            r'vtag[:\s]+(\w+)',
            r'v_tag[:\s]+(\w+)',
            r'view\s+tag[:\s]+(\w+)'
        ]
        for pattern in vtag_patterns:
            match = re.search(pattern, message_lower)
            if match:
                session.extracted_params["vTag"] = match.group(1)
                break
        
        # Extract iTag
        itag_patterns = [
            r'itag[:\s]+(\w+)',
            r'i_tag[:\s]+(\w+)',
            r'interface\s+tag[:\s]+(\w+)',
            r'interface[:\s]+(\w+)'
        ]
        for pattern in itag_patterns:
            match = re.search(pattern, message_lower)
            if match:
                session.extracted_params["iTag"] = match.group(1)
                break
    
    def detect_topic(self, message: str) -> Optional[str]:
        """Detect topic from message"""
        message_lower = message.lower()
        
        # Topic detection keywords
        if any(kw in message_lower for kw in ['validate', 'validation', 'ordersense', 'tab order']):
            return "validation"
        elif any(kw in message_lower for kw in ['configure', 'configuration', 'setup', 'create']):
            return "configuration"
        elif any(kw in message_lower for kw in ['what is', 'explain', 'how does', 'feature']):
            return "feature_explanation"
        elif any(kw in message_lower for kw in ['action', 'step', 'outcome', 'attribute']):
            return "actions"
        elif any(kw in message_lower for kw in ['view', 'entity', 'interface']):
            return "views_entities"
        
        return None
    
    def update_session_topic(self, session_id: str, message: str):
        """Detect and update session topic"""
        topic = self.detect_topic(message)
        if topic:
            session = self.get_or_create_session(session_id)
            session.update_topic(topic)
    
    def build_context_for_agent(self, session_id: str, current_message: str) -> str:
        """
        Build comprehensive context for agent including:
        1. Conversation history
        2. Extracted parameters
        3. Current topic
        """
        session = self.get_or_create_session(session_id)
        
        # Get recent conversation history
        recent_messages = session.get_recent_messages(10)
        conversation_history = "\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in recent_messages
        ])
        
        # Build context
        context_parts = [conversation_history, f"User: {current_message}"]
        
        # Add extracted parameters if available
        if session.extracted_params:
            params_str = ", ".join([f"{k}={v}" for k, v in session.extracted_params.items()])
            context_parts.append(f"\n[Session Context - Previously mentioned parameters: {params_str}]")
        
        # Add current topic if available
        if session.current_topic:
            context_parts.append(f"[Current Topic: {session.current_topic}]")
        
        # Add topic history if available
        if session.topic_history:
            topics_str = " → ".join(session.topic_history[-3:])  # Last 3 topics
            context_parts.append(f"[Previous Topics: {topics_str}]")
        
        return "\n".join(context_parts)
    
    def get_session_summary(self, session_id: str) -> Dict:
        """Get comprehensive session summary"""
        if session_id not in self.sessions:
            return {"error": "Session not found"}
        
        session = self.sessions[session_id]
        
        return {
            "session_id": session_id,
            "message_count": len(session.messages),
            "user_messages": sum(1 for msg in session.messages if msg["role"] == "user"),
            "assistant_messages": sum(1 for msg in session.messages if msg["role"] == "assistant"),
            "extracted_params": session.extracted_params,
            "current_topic": session.current_topic,
            "topic_history": session.topic_history,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "duration_minutes": self._calculate_duration(session.created_at, session.last_activity)
        }
    
    def _calculate_duration(self, start: str, end: str) -> float:
        """Calculate duration between two timestamps in minutes"""
        try:
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            duration = (end_dt - start_dt).total_seconds() / 60
            return round(duration, 2)
        except:
            return 0.0
    
    def clear_session(self, session_id: str):
        """Clear conversation memory for session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_all_sessions_summary(self) -> List[Dict]:
        """Get summary of all active sessions"""
        return [
            self.get_session_summary(session_id)
            for session_id in self.sessions.keys()
        ]
    
    # ========== VECTOR DATABASE (Long-term, External) ==========
    
    def search_knowledge_base(self, query: str, limit: int = 3, doc_type: Optional[str] = None) -> List[Dict]:
        """
        Search vector database for relevant knowledge
        This is your RAG (Retrieval Augmented Generation) component
        """
        try:
            return self.vector_store.search(query, limit=limit, doc_type=doc_type)
        except Exception as e:
            print(f"Error searching knowledge base: {e}")
            return []
    
    def get_knowledge_stats(self) -> Dict:
        """Get statistics about knowledge base"""
        try:
            return {
                "total_documents": self.vector_store.count(),
                "feature_docs": self.vector_store.count(doc_type="feature"),
                "config_docs": self.vector_store.count(doc_type="config"),
                "general_docs": self.vector_store.count(doc_type="general"),
                "is_connected": self.vector_store.is_connected()
            }
        except Exception as e:
            return {"error": str(e)}
    
    # ========== LEARNING MEMORY (From Feedback) ==========
    
    def store_successful_interaction(self, session_id: str, user_query: str, 
                                     assistant_response: str, doc_type: str = "general"):
        """
        Store user-approved interactions back into vector database
        This allows the agent to learn from successful interactions
        """
        try:
            doc_id = f"learned_{session_id}_{int(datetime.now().timestamp())}"
            content = f"User Query: {user_query}\n\nApproved Response:\n{assistant_response}"
            
            metadata = {
                "type": "learned_interaction",
                "session_id": session_id,
                "learned_at": datetime.now().isoformat()
            }
            
            self.vector_store.add(
                doc_id=doc_id,
                content=content,
                metadata=metadata,
                doc_type=doc_type
            )
            
            return {"status": "success", "doc_id": doc_id}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_learned_interactions_count(self) -> int:
        """Get count of learned interactions"""
        try:
            # This would require a custom query to count learned interactions
            # For now, return 0 as placeholder
            return 0
        except:
            return 0


# Global memory manager instance
memory_manager = MemoryManager()