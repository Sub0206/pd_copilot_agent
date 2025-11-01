from agents import Agent, function_tool, Runner
from typing import Optional

def _get_vector_store():
    from ..core.vector_store import vector_store
    return vector_store

def _get_doc_processor():
    from ..core.document_processor import doc_processor
    return doc_processor

def _ensure_indexed():
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
def query_config_knowledge(query: str, limit: int = 4) -> str:
    """Query vector database for Product Designer configuration knowledge"""
    try:
        _ensure_indexed()
        vector_store = _get_vector_store()
        
        docs = vector_store.search(query, limit=limit, doc_type="config")
        
        if not docs:
            docs = vector_store.search(query, limit=limit)
            if not docs:
                return "No configuration documentation found in database."
        
        context = "\n\n".join([
            f"[{doc['metadata']['filename']}]\n{doc['content'][:1500]}"
            for doc in docs
        ])
        
        return f"Configuration documentation found:\n\n{context}"
    except Exception as e:
        return f"Unable to search configuration documentation: {str(e)}"

class ConfigGuideAgent:
    def __init__(self):
        self._agent = None
    
    @property
    def agent(self) -> Agent:
        if self._agent is None:
            self._agent = Agent(
                name="ConfigGuide",
                instructions="""You are a Product Designer configuration expert.

When users need configuration help:
1. Use query_config_knowledge() to retrieve relevant guides
2. Provide clear step-by-step instructions
3. Format responses as:

**Configuration: [Task Name]**
**Prerequisites:** What's needed
**Steps:**
1. First step with details
2. Second step with details
**Validation:** How to verify
**Sources:** Documentation sources

Always search your knowledge base before answering.""",
                model="gpt-4o-mini",
                tools=[query_config_knowledge]
            )
        return self._agent

config_guide_agent = ConfigGuideAgent()

@function_tool
async def guide_configuration(task_name: str, context: Optional[str] = None) -> str:
    """Get step-by-step configuration guidance"""
    try:
        prompt = f"Provide step-by-step configuration guide for: {task_name}"
        if context:
            prompt += f"\nContext: {context}"
        
        # Use async run instead of run_sync
        result = await Runner.run(config_guide_agent.agent, prompt)
        return result.final_output if hasattr(result, 'final_output') else str(result)
    except Exception as e:
        return f"Configuration guidance for '{task_name}': Currently unavailable ({str(e)}). Please ensure documentation is loaded."

@function_tool
async def validate_configuration(config_description: str) -> str:
    """Validate configuration against best practices"""
    try:
        prompt = f"Review and validate this configuration:\n\n{config_description}"
        
        # Use async run instead of run_sync
        result = await Runner.run(config_guide_agent.agent, prompt)
        return result.final_output if hasattr(result, 'final_output') else str(result)
    except Exception as e:
        return f"Configuration validation: Currently unavailable ({str(e)}). Please ensure documentation is loaded."