"""
PD Copilot Agent Package
Main exports for easy importing
"""

from .models import ChatRequest, ChatResponse, AgentStatus, HealthCheck

__all__ = [
    # Main agent
    "PDCopilotAgent",
    "pd_copilot_agent",
    
    # OrderSense tools
    "fetch_database_info",
    "parse_database_info",
    "analyze_view_items",
    "generate_report",
    "evaluate_report",
    "format_ordersense_result",
    
    # Models
    "ChatRequest",
    "ChatResponse",
    "AgentStatus",
    "HealthCheck",
]

__version__ = "1.0.0"
__author__ = "PD Copilot Team"
