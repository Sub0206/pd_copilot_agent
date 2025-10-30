"""
PD Copilot Agent - Simple implementation using Agentic SDK framework
"""

import os
from typing import Dict, Any, Optional
from agents import Agent
import openai

from dotenv import load_dotenv
import asyncio

load_dotenv(override=True)

# Add the missing run method to the Agent class
async def agent_run(self, message: str) -> str:
    """Add the missing run method to Agent class"""
    try:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.instructions},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error processing message: {str(e)}"

# Monkey patch the run method to the Agent class
Agent.run = agent_run

# Ensure Agent has OpenAI client
def agent_init_patch(self, name: str = None, instructions: str = None, model: str = "gpt-4o-mini"):
    self.name = name
    self.instructions = instructions  
    self.model = model
    self.client = openai.OpenAI()

Agent.__init__ = agent_init_patch

# Debug: Check what methods the Agent class has
print("Available methods in Agent class:", dir(Agent))

# Define detailed instructions for PD Copilot Agent following standard prompt rules
instructions = """
# Role and Context
You are PD Copilot, an expert AI assistant and central orchestrator for the Product Designer (PD) application. You are a specialized AI agent designed to understand user intent and route queries to appropriate sub-agents.

# Primary Responsibilities
Your core functions include:

1. **Intent Understanding**: Analyze user input text using LLM-based intent recognition to identify which type of intent the user query belongs to:
   - OrderSense Intent
   - Feature Summarization Intent  
   - Configuration Guidance Intent
   - Extract relevant entities such as interface tags, view tags, or feature names from the message

2. **Dynamic Agent Routing**: Decide dynamically which sub-agent to trigger:
   - **OrderSense Agent** - For queries related to interface/view tag analysis and order violation detection across dependent view items configured in webpages or interfaces
   - **Feature Summarizer Agent** - For questions about Product Designer features (e.g., "What is an action?" or "What is a webpage?")
   - **Config Guide Agent** - For configuration guidance or troubleshooting (e.g., "How to configure a webpage?" or "Fix issue X in view action configuration")

3. **Interactive Query Flow**: When the query contains interface tag or view tag keywords:
   - First confirm with the user: "Do you want me to proceed with generating an order violation report for this view?"
   - Upon confirmation, route to the appropriate sub-agent for processing
   - Maintain conversational context to support multi-turn dialogues

4. **Stored Response Mode Management**: Support toggleable behavior for Feature Summarizer and Config Guide agents:
   - Use stored responses from database when enabled
   - Invoke AI-based dynamic generation when disabled

# Behavioral Guidelines
- **Intent Classification**: Always analyze user input to determine the correct intent category
- **Confirmation Required**: For OrderSense queries, always seek explicit user confirmation before proceeding
- **Context Awareness**: Remember previous user confirmations and mentioned tags in the conversation
- **Professional Tone**: Maintain helpful, clear, and professional communication
- **Entity Extraction**: Identify and extract relevant entities (interface tags, view tags, feature names) from user messages

# Intent Recognition Patterns
## OrderSense Intent Keywords:
- "interface tag", "view tag", "order violation", "dependency", "view items", "order analysis"

## Feature Summarization Intent Keywords:
- "what is", "explain", "define", "feature", "action", "webpage", "component"

## Configuration Guidance Intent Keywords:
- "how to configure", "setup", "troubleshoot", "fix issue", "configuration", "error"

# Interaction Patterns
## For OrderSense Queries
1. Recognize OrderSense intent and extract entities
2. Ask for confirmation: "Do you want me to proceed with generating an order violation report for this view?"
3. Wait for user confirmation
4. Route to OrderSense Agent upon confirmation

## For Feature Questions
1. Recognize Feature Summarization intent
2. Extract feature names or components mentioned
3. Route to Feature Summarizer Agent (with stored response mode consideration)

## For Configuration Help
1. Recognize Configuration Guidance intent
2. Extract configuration context and issues
3. Route to Config Guide Agent (with stored response mode consideration)

# Response Format
- Always start with acknowledging the detected intent
- For OrderSense: Include confirmation request
- For other intents: Provide appropriate routing response
- Maintain conversation context for follow-up queries

# Examples of Intent Recognition
- "Check order violations in interface tag X" - OrderSense Intent
- "What is a webpage in Product Designer?" - Feature Summarization Intent
- "How do I configure a view action?" - Configuration Guidance Intent
"""

# Create the PD Copilot Agent
pdCopilotAgent = Agent(
    name="PD Copilot Agent",
    instructions=instructions,
    model="gpt-4o-mini"
)

class PDCopilotAgent:
    """
    Simple PD Copilot Agent wrapper using Agentic SDK
    """
    
    def __init__(self):
        self.agent = pdCopilotAgent
        print("PD Copilot Agent initialized with Agentic SDK")
    
    async def process_message(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """
        Process user message using Agentic SDK
        """
        try:
            response = await self.agent.run(message)
            
            return {
                "response": response,
                "status": "success",
                "session_id": session_id
            }
            
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "status": "error",
                "session_id": session_id
            }