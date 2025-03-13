import streamlit as st
import requests
import json
import base64
from io import BytesIO
import tempfile
import os

# Set page config
st.set_page_config(
    page_title="Cashly Copilot",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Apply custom CSS for Cashly Copilot branding
st.markdown("""
<style>
    /* Cashly branded colors */
    :root {
        --cashly-primary: #003ba3;
        --cashly-secondary: #4a8cff;
        --cashly-light: #efefef;
        --cashly-white: #ffffff;
        --cashly-gray: #f5f7fa;
    }
    
    /* Global styles */
    .stApp {
        background-color: var(--cashly-white);
    }
    
    /* Header styling */
    header {
        background-color: var(--cashly-primary) !important;
        margin-bottom: 0 !important;
    }
    
    /* Reduce top padding aggressively */
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 100%;
    }
    
    /* Remove any default margins from the title and subtitle */
    h2, p {
        margin-top: 0 !important;
        margin-bottom: 0.3rem !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        line-height: 1.2 !important;
    }
    
    /* Target Streamlit's vertical spacing between components */
    [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    
    /* Additional override for Streamlit's default spacing */
    .element-container {
        margin-bottom: 0.2rem !important;
    }
    

    
    /* Message styling for Streamlit's built-in chat components */
    .stChatMessage {
        background-color: transparent !important;
        padding: 0 !important;
        margin: 0.3rem 0 !important;
    }
    
    .stChatMessage [data-testid="stChatMessageContent"] {
        padding: 0.7rem 1rem !important;
        border-radius: 1rem !important;
        max-width: 85% !important;
        font-size: 0.9rem !important;
        line-height: 1.35 !important;
    }
    
    /* User message styling */
    .stChatMessage[data-testid="stChatMessageUser"] [data-testid="stChatMessageContent"] {
        background-color: #4a8cff !important;
        color: white !important;
        margin-left: auto !important;
        border-bottom-right-radius: 0.3rem !important;
    }
    
    /* Assistant message styling */
    .stChatMessage:not([data-testid="stChatMessageUser"]) [data-testid="stChatMessageContent"] {
        background-color: #efefef !important;
        color: #333333 !important;
        margin-right: auto !important;
        border-bottom-left-radius: 0.3rem !important;
    }
    
    /* File upload styling */
    .file-upload {
        background-color: var(--cashly-gray);
        padding: 0.5rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        font-size: 0.8rem;
    }
    
    .file-attachment {
        display: inline-block;
        background-color: rgba(74, 140, 255, 0.1);
        color: var(--cashly-primary);
        padding: 0.3rem 0.6rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        margin: 0.2rem 0;
    }
    
    /* Input area */
    .input-area {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    
    /* Custom file uploader */
    .stFileUploader > div > button {
        background-color: var(--cashly-primary);
        color: white;
    }
    
    /* Streamlit element adjustments */
    div.stButton > button {
        background-color: var(--cashly-primary);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    div.stButton > button:hover {
        background-color: var(--cashly-secondary);
        color: white;
    }
    
    .stTextInput > div > div > input {
        border-color: rgba(0, 59, 163, 0.2);
    }
    
    /* Hide streamlit branding */
    footer {display: none !important;}
    #MainMenu {visibility: hidden;}
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #c1c9d2;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--cashly-secondary);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# n8n webhook URL to start the chat
N8N_WEBHOOK_URL = "https://n8n.gocashly.io/webhook-test/cashly-copilot"

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file"""
    try:
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            text += pdf_reader.pages[page_num].extract_text() + "\n"
        return text
    except ImportError:
        # Fallback if PyPDF2 is not available
        return f"[PDF content from {pdf_file.name} - PDF processing library not available]"

def send_message_to_agent(message_text, uploaded_files=None):
    """Send message to the n8n webhook and get response"""
    payload = {"message": message_text}
    
    # Add file content if available
    if uploaded_files:
        file_contents = []
        for file in uploaded_files:
            if file.name.lower().endswith('.pdf'):
                text = extract_text_from_pdf(file)
                file_contents.append({
                    "filename": file.name,
                    "content_type": "application/pdf",
                    "content": text
                })
            else:
                # For text files or other formats
                content = file.getvalue().decode("utf-8") if file.name.lower().endswith('.txt') else f"[Binary file: {file.name}]"
                file_contents.append({
                    "filename": file.name,
                    "content_type": file.type,
                    "content": content
                })
        
        if file_contents:
            payload["files"] = file_contents
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        # Check response content
        content_type = response.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            # JSON response
            try:
                response_data = response.json()
                if isinstance(response_data, dict):
                    return response_data.get("response", str(response_data))
                else:
                    return str(response_data)
            except ValueError:
                # Invalid JSON
                return f"Received invalid JSON response: {response.text[:100]}..."
        else:
            # Non-JSON response (text, etc)
            return response.text
            
    except requests.exceptions.RequestException as e:
        return f"Network error communicating with Cashly Copilot: {str(e)}"
    except Exception as e:
        return f"Error processing response from Cashly Copilot: {str(e)}"

# More compact logo and title
st.markdown("""
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.3rem;">
    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 128 128">
        <circle cx="64" cy="64" r="64" fill="#003ba3"/>
        <path d="M92 56c0-13.255-10.745-24-24-24H44c-13.255 0-24 10.745-24 24v16c0 13.255 10.745 24 24 24h2v16l16-16h6c13.255 0 24-10.745 24-24V56z" fill="#4a8cff"/>
        <circle cx="46" cy="64" r="6" fill="#ffffff"/>
        <circle cx="64" cy="64" r="6" fill="#ffffff"/>
        <circle cx="82" cy="64" r="6" fill="#ffffff"/>
    </svg>
    <div>
        <h2 style="color: #003ba3; margin: 0; font-size: 1.3rem;">Cashly Copilot</h2>
        <p style="font-size: 0.7rem; color: #666; margin: 0;">Your AI financial assistant</p>
    </div>
</div>
""", unsafe_allow_html=True)

# Create a container for messages with fixed height
chat_area = st.container()
with chat_area:
    # Add custom class
    st.markdown('<div class="messages-container">', unsafe_allow_html=True)
    
    # Display messages using Streamlit's built-in message function
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "files" in msg:
                for file in msg["files"]:
                    st.write(f"📎 {file}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# File uploader
uploaded_files = st.file_uploader("Upload PDF or text files", 
                               type=["pdf", "txt"], 
                               accept_multiple_files=True,
                               label_visibility="collapsed")

# Input area
col1, col2 = st.columns([5, 1])
with col1:
    user_input = st.text_input("Message", 
                              label_visibility="collapsed", 
                              placeholder="Ask Cashly Copilot a question...")
with col2:
    send_button = st.button("Send")

# Add a scroll to bottom JavaScript
st.markdown("""
<script>
    function scrollToBottom() {
        const messageContainers = document.getElementsByClassName('messages-container');
        if (messageContainers.length > 0) {
            const container = messageContainers[0];
            container.scrollTop = container.scrollHeight;
        }
    }
    
    // Run on load and whenever the DOM changes
    window.addEventListener('load', scrollToBottom);
    const observer = new MutationObserver(scrollToBottom);
    observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# Process input
if send_button and (user_input or uploaded_files):
    file_names = []
    
    # Process uploaded files
    if uploaded_files:
        for file in uploaded_files:
            file_names.append(file.name)
            st.session_state.uploaded_files.append(file)
    
    # Add user message to chat history
    user_message = {"role": "user", "content": user_input}
    if file_names:
        user_message["files"] = file_names
    
    st.session_state.messages.append(user_message)
    
    # Get response from agent
    agent_response = send_message_to_agent(user_input, uploaded_files)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": agent_response})
    
    # Clear the input
    st.rerun()