from agents import Agent, Runner
from dotenv import load_dotenv
from .ordersense_agent import run_ordersense_validation
from .feature_summarizer_agent import explain_feature, search_documentation
from .config_guide_agent import guide_configuration, validate_configuration

load_dotenv(override=True)

PD_COPILOT_INSTRUCTIONS = """You are PD Copilot for Product Designer application with access to comprehensive knowledge base.

CAPABILITIES:
1. Tab Order Validation - Validate view item dependencies
2. Feature Explanation - Explain PD features using documentation
3. Configuration Guidance - Provide step-by-step config help
4. Documentation Search - Search through all PD documentation

ROUTING:
- Tab order validation → run_ordersense_validation(pt_id, vTag or iTag)
- Feature questions → explain_feature(feature_name) or search_documentation(query)
- Configuration help → guide_configuration(task_name) or validate_configuration(config)
- General questions → search_documentation(query)

PARAMETER EXTRACTION:
Extract from conversation:
- pt_id: "1345", "pt 1345", "pt_id 1345"
- vTag: "acctDT", "vtag acctDT"  
- iTag: "interface X", "itag X"

BEHAVIOR:
✓ Use tools to access knowledge base
✓ Scan conversation for parameters
✓ Execute when you have required parameters
✓ Ask for missing parameters once with examples
✓ Provide actionable guidance
✓ Reference documentation sources

All tools have access to the vector database memory."""

pd_copilot_agent = Agent(
    name="PD Copilot",
    instructions=PD_COPILOT_INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[
        run_ordersense_validation,
        explain_feature,
        search_documentation,
        guide_configuration,
        validate_configuration
    ]
)

class PDCopilotAgent:
    def __init__(self):
        self.agent = pd_copilot_agent
        self.sessions = {}
    
    async def process_message(self, message: str, session_id: str = "default") -> dict:
        try:
            if session_id not in self.sessions:
                self.sessions[session_id] = {"messages": [], "context": ""}
            
            session = self.sessions[session_id]
            session["messages"].append({"role": "user", "content": message})
            
            # Build conversation context for the agent
            conversation_history = "\n".join([
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in session["messages"][-10:]  # Keep last 10 messages for context
            ])
            
            # Run the agent with conversation context
            result = await Runner.run(
                self.agent,
                conversation_history
            )
            
            response = result.final_output if hasattr(result, 'final_output') else str(result)
            
            session["messages"].append({"role": "assistant", "content": response})
            
            return {
                "response": response,
                "status": "success",
                "session_id": session_id
            }
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            return {
                "response": error_msg,
                "status": "error",
                "session_id": session_id
            }
    
    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_session(self, session_id: str) -> dict:
        return self.sessions.get(session_id, {"messages": []})