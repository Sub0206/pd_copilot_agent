from agents import function_tool
from typing import Dict, Optional


@function_tool
def guide_configuration(task_name: str, context: Optional[str] = None) -> Dict:
    """
    Provide step-by-step configuration guidance for PD tasks like actions, views, entities.
    Learns from existing configurations and approved responses.
    """
    return {
        "status": "in_development",
        "message": "ConfigGuide agent - Coming soon",
        "task_requested": task_name,
        "context": context
    }


@function_tool
def validate_configuration(config_data: str) -> Dict:
    """Validate user's configuration against best practices"""
    return {
        "status": "in_development",
        "message": "Configuration validation - Coming soon",
        "config_data": config_data
    }
