"""
PD Copilot Agent - Gradio Testing Interface
"""

import gradio as gr
import requests
import json
from datetime import datetime
import uuid
import os
from typing import List, Tuple

# Backend API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
CHAT_ENDPOINT = f"{API_BASE_URL}/api/chat"
STATUS_ENDPOINT = f"{API_BASE_URL}/agent/status"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"

# Session Management
session_id = str(uuid.uuid4())


def check_backend_status() -> Tuple[str, str]:
    """Check if the FastAPI backend is running"""
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return "🟢 Connected", f"Service: {data.get('service', 'Unknown')}"
        return "🔴 Error", f"Status code: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "🔴 Disconnected", "Cannot connect to backend. Is the server running?"
    except Exception as e:
        return "🔴 Error", f"Error: {str(e)}"


def get_agent_capabilities() -> str:
    """Fetch agent capabilities from backend"""
    try:
        response = requests.get(STATUS_ENDPOINT, timeout=5)
        if response.status_code == 200:
            data = response.json()
            caps = data.get('capabilities', [])
            tools = data.get('tools', [])
            
            info = f"**Agent:** {data.get('agent_name', 'Unknown')}\n\n"
            info += "**Capabilities:**\n"
            for cap in caps:
                info += f"- {cap}\n"
            info += "\n**Available Tools:**\n"
            for tool in tools:
                info += f"- {tool}\n"
            return info
        return "Unable to fetch agent information"
    except Exception as e:
        return f"Error: {str(e)}"


def send_message(message: str, history: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], str]:
    """Send message to PD Copilot Agent and return response"""
    if not message.strip():
        return history, ""
    
    try:
        # Prepare request payload
        payload = {
            "message": message,
            "session_id": session_id,
            "context": {}
        }
        
        # Send request to backend
        response = requests.post(
            CHAT_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # Increased timeout for agent processing
        )
        
        if response.status_code == 200:
            data = response.json()
            assistant_message = data.get("message", "No response received")
            status = data.get("status", "unknown")
            
            # Add status indicator if error
            if status == "error":
                assistant_message = f"⚠️ **Error:** {assistant_message}"
            
            # Update history
            history.append((message, assistant_message))
            
        else:
            error_msg = f"❌ Backend returned status code: {response.status_code}"
            history.append((message, error_msg))
    
    except requests.exceptions.Timeout:
        error_msg = "⏱️ Request timed out. The agent might be processing a complex query."
        history.append((message, error_msg))
    
    except requests.exceptions.ConnectionError:
        error_msg = "🔴 Cannot connect to backend. Please ensure the FastAPI server is running on port 8000."
        history.append((message, error_msg))
    
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        history.append((message, error_msg))
    
    return history, ""


def clear_chat():
    """Clear chat history and create new session"""
    global session_id
    session_id = str(uuid.uuid4())
    return [], ""


def export_chat(history: List[Tuple[str, str]]) -> str:
    """Export chat history as formatted text"""
    if not history:
        return "No chat history to export"
    
    export_text = f"PD Copilot Chat Export\n"
    export_text += f"Session ID: {session_id}\n"
    export_text += f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    export_text += "=" * 60 + "\n\n"
    
    for i, (user_msg, agent_msg) in enumerate(history, 1):
        export_text += f"Message {i}\n"
        export_text += f"User: {user_msg}\n"
        export_text += f"Agent: {agent_msg}\n"
        export_text += "-" * 60 + "\n\n"
    
    return export_text


# Custom CSS for better styling
custom_css = """
#chatbot {
    height: 600px;
}
.example-box {
    padding: 10px;
    margin: 5px;
    border-radius: 5px;
    background-color: #f0f0f0;
}
"""

# Example queries for users
EXAMPLE_QUERIES = [
    "Explain the Entity feature in Product Designer",
    "How do I configure a new view?",
    "Run OrderSense validation for pt_id 1345 and vTag acctDT",
    "What are the best practices for tab ordering?",
    "Search documentation for interface setup"
]


# Build Gradio Interface
with gr.Blocks(css=custom_css, title="PD Copilot Testing") as demo:
    
    # Header
    gr.Markdown("""
    # 🤖 PD Copilot Agent - Testing Interface
    ### AI Assistant for Product Designer with RAG & Agentic SDK
    """)
    
    # Backend Status
    with gr.Row():
        with gr.Column(scale=1):
            status_box = gr.Textbox(
                label="Backend Status",
                value=check_backend_status()[0],
                interactive=False
            )
        with gr.Column(scale=3):
            status_msg = gr.Textbox(
                label="Status Details",
                value=check_backend_status()[1],
                interactive=False
            )
    
    refresh_btn = gr.Button("🔄 Refresh Status", size="sm")
    
    # Main Chat Interface
    with gr.Row():
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(
                elem_id="chatbot",
                label="Chat with PD Copilot",
                height=600,
                show_label=True
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    label="Your Message",
                    placeholder="Ask me about Product Designer features, configuration, or run OrderSense validation...",
                    lines=2,
                    scale=4
                )
                send_btn = gr.Button("📤 Send", scale=1, variant="primary")
            
            with gr.Row():
                clear_btn = gr.Button("🗑️ Clear Chat")
                export_btn = gr.Button("💾 Export Chat")
        
        # Sidebar with info and examples
        with gr.Column(scale=1):
            gr.Markdown("### 📚 Agent Info")
            agent_info = gr.Textbox(
                value=get_agent_capabilities(),
                label="Capabilities",
                lines=15,
                interactive=False
            )
            
            gr.Markdown("### 💡 Example Queries")
            for example in EXAMPLE_QUERIES:
                gr.Button(
                    example,
                    size="sm"
                ).click(
                    fn=lambda e=example: e,
                    outputs=msg_input
                )
    
    # Export output
    export_output = gr.Textbox(
        label="Exported Chat",
        lines=10,
        visible=False
    )
    
    # Session info
    gr.Markdown(f"**Current Session ID:** `{session_id}`")
    
    # Event Handlers
    def show_export(history):
        return {
            export_output: gr.update(value=export_chat(history), visible=True)
        }
    
    def update_status():
        status, msg = check_backend_status()
        return status, msg, get_agent_capabilities()
    
    # Wire up events
    send_btn.click(
        fn=send_message,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input]
    )
    
    msg_input.submit(
        fn=send_message,
        inputs=[msg_input, chatbot],
        outputs=[chatbot, msg_input]
    )
    
    clear_btn.click(
        fn=clear_chat,
        outputs=[chatbot, msg_input]
    )
    
    export_btn.click(
        fn=show_export,
        inputs=[chatbot],
        outputs=[export_output]
    )
    
    refresh_btn.click(
        fn=update_status,
        outputs=[status_box, status_msg, agent_info]
    )
    
    # Instructions
    gr.Markdown("""
    ---
    ### 📖 How to Use:
    1. **Ensure Backend is Running**: Start your FastAPI server (`python -m app.main`)
    2. **Check Status**: Green indicator means backend is connected
    3. **Ask Questions**: Type your query or click example queries
    4. **Test Features**:
        - Feature explanations: "Explain Entity feature"
        - Configuration help: "How to configure a view?"
        - OrderSense validation: "Validate pt_id 1345 vTag acctDT"
        - Documentation search: "Search for interface setup"
    
    ### 🛠️ Troubleshooting:
    - **Red Status**: Ensure FastAPI server is running on port 8000
    - **Timeout**: Agent is processing complex queries (normal for OrderSense)
    - **No Response**: Check backend logs for errors
    """)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Starting PD Copilot Gradio Testing Interface")
    print("=" * 60)
    print(f"📡 Backend URL: {API_BASE_URL}")
    print(f"🔗 Chat Endpoint: {CHAT_ENDPOINT}")
    print(f"🆔 Session ID: {session_id}")
    
    # Check backend status
    status, msg = check_backend_status()
    print(f"📊 Backend Status: {status}")
    print(f"   {msg}")
    
    if "Disconnected" in status:
        print("\n⚠️  WARNING: Cannot connect to backend!")
        print("   Please start the FastAPI server first:")
        print("   python -m app.main")
    
    print("\n🌐 Launching Gradio interface...")
    print("=" * 60 + "\n")
    
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=True
    )