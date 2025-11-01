from agents import Agent, function_tool, Runner
from typing import Optional

def _get_vector_store():
    """Lazy import to avoid circular dependencies"""
    from ..core.vector_store import vector_store
    return vector_store

def _get_doc_processor():
    """Lazy import to avoid circular dependencies"""
    from ..core.document_processor import doc_processor
    return doc_processor

def _ensure_indexed():
    """Index new documents if available"""
    try:
        doc_processor = _get_doc_processor()
        vector_store = _get_vector_store()
        
        if doc_processor.has_new_documents():
            result = doc_processor.process_new_documents()
            for doc in result["processed"]:
                vector_store.add(
                    doc_id=doc["doc_id"],
                    content=doc["content"],
                    metadata=doc["metadata"],
                    doc_type=doc["doc_type"]
                )
    except Exception as e:
        print(f"⚠️  Indexing error: {e}")

@function_tool
def query_feature_knowledge(query: str, limit: int = 3) -> str:
    """Query vector database for Product Designer feature knowledge"""
    try:
        _ensure_indexed()
        vector_store = _get_vector_store()
        
        docs = vector_store.search(query, limit=limit, doc_type="feature")
        
        if not docs:
            return "No feature documentation found in database."
        
        context = "\n\n".join([
            f"[{doc['metadata']['filename']}]\n{doc['content'][:1500]}"
            for doc in docs
        ])
        
        return f"Documentation found:\n\n{context}"
    except Exception as e:
        return f"Unable to search documentation: {str(e)}"

class FeatureSummarizerAgent:
    def __init__(self):
        self._agent = None
    
    @property
    def agent(self) -> Agent:
        if self._agent is None:
            self._agent = Agent(
                name="FeatureSummarizer",
                instructions="""You are a Product Designer feature expert with access to documentation.

When users ask about features:
1. Use query_feature_knowledge() to retrieve relevant documentation
2. Synthesize information into clear explanations
3. Format responses as:

**Feature: [Name]**
**Description:** Clear 2-3 sentence explanation
**Key Capabilities:**
- Main capability 1
- Main capability 2
**Example Use Case:** Practical example
**Sources:** Documentation sources

Always search your knowledge base before answering.""",
                model="gpt-4o-mini",
                tools=[query_feature_knowledge]
            )
        return self._agent

feature_summarizer_agent = FeatureSummarizerAgent()

@function_tool
def explain_feature(feature_name: str, detail_level: str = "standard") -> str:
    """Explain Product Designer features using the agent's knowledge base"""
    try:
        prompt = f"Explain the '{feature_name}' feature in Product Designer"
        if detail_level == "detailed":
            prompt += " with detailed examples"
        elif detail_level == "brief":
            prompt += " briefly"
        
        result = Runner.run_sync(feature_summarizer_agent.agent, prompt)
        return result.final_output if hasattr(result, 'final_output') else str(result)
    except Exception as e:
        return f"Feature explanation unavailable: {str(e)}"

@function_tool
def search_documentation(query: str) -> str:
    """Search Product Designer documentation"""
    try:
        result = Runner.run_sync(feature_summarizer_agent.agent, f"Search documentation for: {query}")
        return result.final_output if hasattr(result, 'final_output') else str(result)
    except Exception as e:
        return f"Documentation search unavailable: {str(e)}"