# app/gradio_testing/chatbot_test.py
import gradio as gr
import requests

# Configuration
CHAT_URL = "http://127.0.0.1:8000/chat"

def send_message(message, history):
    """Send message to PD Copilot Agent"""
    if not message.strip():
        return "", history
    
    # Send to agent
    payload = {"message": message, "session_id": "chat"}
    
    print(f"🔍 Sending POST to: {CHAT_URL}")
    print(f"📦 Payload: {payload}")
    
    try:
        response = requests.post(CHAT_URL, json=payload, timeout=30)
        
        print(f"📡 Response status: {response.status_code}")
        print(f"📄 Response text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            agent_response = result.get('response', 'No response')
        else:
            agent_response = f"Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        agent_response = f"Connection error: {str(e)}"
    
    # Add to history
    history.append([message, agent_response])
    return "", history

# Create interface
with gr.Blocks(title="PD Copilot Chatbot") as demo:
    gr.Markdown("# 🤖 PD Copilot Chatbot")
    
    chatbot = gr.Chatbot()
    msg = gr.Textbox(placeholder="Type your message...")
    clear = gr.Button("Clear")
    
    msg.submit(send_message, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: [], None, chatbot)

if __name__ == "__main__":
    demo.launch(
        server_port=7860,
        show_error=True,
        quiet=True  # This reduces console warnings
    )