from agents import Agent
from dotenv import load_dotenv
from .ordersense_agent import run_ordersense_validation
from .feature_summarizer_agent import explain_feature, search_documentation
from .config_guide_agent import guide_configuration, validate_configuration

load_dotenv(override=True)


PD_COPILOT_INSTRUCTIONS = """You are PD Copilot for Product Designer application.

ROUTING:
- Tab order validation → use run_ordersense_validation(pt_id, vTag or iTag)
- Feature questions → use explain_feature(feature_name)
- Configuration help → use guide_configuration(task_name)

PARAMETER EXTRACTION:
Extract from entire conversation history:
- pt_id: "1345", "pt 1345", "pt_id 1345"
- vTag: "acctDT", "vtag acctDT"
- iTag: "interface X", "itag X"

BEHAVIOR:
✓ Scan full conversation for parameters
✓ Execute when all required params available
✓ Ask for missing params with examples
✓ Never ask for same param twice

EXAMPLES:
User: "check violations in acctDT"
You: "Need pt_id. Example: pt_id='1368'"

User: "1345"
You: [Execute run_ordersense_validation(pt_id="1345", vTag="acctDT")]

User: "what is an entity?"
You: [Execute explain_feature("entity")]
"""


pd_copilot_agent = Agent(
    name="PD Copilot",
    instructions=PD_COPILOT_INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[
        run_ordersense_validation,
        explain_feature,
        guide_configuration,
        validate_configuration
    ]
)


class PDCopilotAgent:
    def __init__(self):
        self.agent = pd_copilot_agent
        self.sessions = {}
    
    async def process_message(self, message: str, session_id: str = "default") -> dict:
        from agents import Runner
        
        try:
            if session_id not in self.sessions:
                self.sessions[session_id] = {"messages": []}
            
            session = self.sessions[session_id]
            session["messages"].append({"role": "user", "content": message})
            
            conversation = "\n".join([
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in session["messages"]
            ])
            
            result = await Runner.run(self.agent, conversation)
            response = result.final_output if hasattr(result, 'final_output') else str(result)
            
            session["messages"].append({"role": "assistant", "content": response})
            
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
    
    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_session(self, session_id: str) -> dict:
        return self.sessions.get(session_id, {"messages": []})
