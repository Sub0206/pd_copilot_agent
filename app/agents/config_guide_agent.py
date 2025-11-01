from agents import Agent, function_tool
from typing import Dict, Optional
import os

CONFIG_DOCS_PATH = os.getenv("CONFIG_DOCS_PATH", "./resource/config_docs")

# Don't initialize at import time
config_store = None
guide_agent = None

def get_config_store():
    """Lazy initialization of config store"""
    global config_store
    if config_store is None:
        try:
            from .vector_store import VectorStore
            config_store = VectorStore(table_name="pd_configs")
        except Exception as e:
            print(f"⚠️ Config store disabled: {e}")
            config_store = False  # Mark as failed
    return config_store if config_store is not False else None

def get_guide_agent():
    """Lazy initialization of guide agent"""
    global guide_agent
    if guide_agent is None:
        guide_agent = Agent(
            name="ConfigGuide",
            instructions="""Provide configuration guidance for Product Designer.
            Include step-by-step instructions and best practices.""",
            model="gpt-4o-mini"
        )
    return guide_agent

@function_tool
def guide_configuration(task_name: str) -> dict:
    """Guide users through configuration tasks"""
    try:
        config_store = get_config_store()
        
        if config_store:
            docs = config_store.search(f"configure {task_name}", limit=3)
            
            if docs:
                context = "\n\n".join([doc["content"][:1000] for doc in docs])
                guide_agent = get_guide_agent()
                result = guide_agent.run(f"Task: {task_name}\n\nContext:\n{context}")
                guide = result.final_output if hasattr(result, 'final_output') else str(result)
                
                return {
                    "status": "success",
                    "task": task_name,
                    "guide": guide,
                    "sources": [doc["metadata"]["filename"] for doc in docs]
                }
        
        # Fallback when VectorStore is not available
        return {
            "status": "success",
            "task": task_name,
            "guide": f"Basic configuration guide for {task_name}:\n1. Identify requirements\n2. Configure settings\n3. Test configuration\n\n(Full documentation search temporarily unavailable)",
            "sources": ["built-in"]
        }
        
    except Exception as e:
        return {"status": "error", "error_message": f"Configuration guide failed: {str(e)}"}

@function_tool
def validate_configuration(config_data: str) -> dict:
    """Validate configuration against best practices"""
    try:
        import json
        data = json.loads(config_data) if isinstance(config_data, str) else config_data
        
        config_store = get_config_store()
        
        if config_store:
            query = f"validate configuration {list(data.keys()) if isinstance(data, dict) else 'settings'}"
            docs = config_store.search(query, limit=2)
            
            if docs:
                context = "\n\n".join([doc["content"][:800] for doc in docs])
                guide_agent = get_guide_agent()
                result = guide_agent.run(f"Validate this config:\n{data}\n\nRules:\n{context}")
                validation = result.final_output if hasattr(result, 'final_output') else str(result)
                
                return {"status": "success", "validation": validation}
        
        # Fallback validation
        validation_result = "Configuration appears valid (basic check - full validation temporarily unavailable)"
        if isinstance(data, dict) and data:
            validation_result += f"\nFound {len(data)} configuration keys: {list(data.keys())[:5]}"
        
        return {
            "status": "success", 
            "validation": validation_result
        }
        
    except Exception as e:
        return {"status": "error", "error_message": f"Configuration validation failed: {str(e)}"}
