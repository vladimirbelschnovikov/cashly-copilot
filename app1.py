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
        height: 100vh;
    }
    
    /* Header styling */
    header {
        background-color: var(--cashly-primary) !important;
        padding: 0.5rem 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    h2 {
        margin: 0.2rem 0 !important;
    }
    
    /* Chat container */
    .chat-container {
        flex: 1;
        min-height: 400px;
        border-radius: 8px;
        background-color: var(--cashly-white);
        padding: 0.5rem;
        overflow-y: auto;
        border: 1px solid rgba(0, 59, 163, 0.1);
        margin-bottom: 0.5rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    /* Message bubbles */
    .user-message, .bot-message {
        padding: 0.7rem 1rem;
        border-radius: 1rem;
        margin: 0.3rem 0;
        max-width: 85%;
        font-size: 0.9rem;
        line-height: 1.35;
        word-wrap: break-word;
    }
    
    .user-message {
        background-color: var(--cashly-secondary);
        color: var(--cashly-white);
        align-self: flex-end;
        margin-left: auto;
        border-bottom-right-radius: 0.3rem;
    }
    
    .bot-message {
        background-color: var(--cashly-light);
        color: #333333;
        align-self: flex-start;
        margin-right: auto;
        border-bottom-left-radius: 0.3rem;
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
        margin-top: auto;
    }
    
    /* Streamlit element adjustments */
    div[data-testid="stVerticalBlock"] {
        gap: 0.2rem !important;
    }
    
    section[data-testid="stFileUploader"] {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    div.stButton > button {
        background-color: var(--cashly-primary);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        height: 100%;
    }
    
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
N8N_WEBHOOK_URL = "https://n8n.gocashly.io/webhook/cashly-copilot"

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
        return f"[PDF content from {pdf_file.name} - PDF processing library not available]"

def send_message_to_agent(message_text, uploaded_files=None):
    """Send message to the n8n webhook and get response"""
    payload = {"message": message_text}
    
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
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        
        if 'application/json' in content_type:
            try:
                response_data = response.json()
                return response_data.get("response", str(response_data))
            except ValueError:
                return f"Invalid JSON response: {response.text[:100]}..."
        else:
            return response.text
            
    except requests.exceptions.RequestException as e:
        return f"Network error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

# Main layout
with st.container():
    # Header
    col1, col2 = st.columns([1, 4])
    with col1:
        st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
            <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 128 128">
                <circle cx="64" cy="64" r="64" fill="#003ba3"/>
                <path d="M92 56c0-13.255-10.745-24-24-24H44c-13.255 0-24 10.745-24 24v16c0 13.255 10.745 24 24 24h2v16l16-16h6c13.255 0 24-10.745 24-24V56z" fill="#4a8cff"/>
                <circle cx="46" cy="64" r="6" fill="#ffffff"/>
                <circle cx="64" cy="64" r="6" fill="#ffffff"/>
                <circle cx="82" cy="64" r="6" fill="#ffffff"/>
            </svg>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown('<h2 style="color: #003ba3; margin-bottom: 0;">Cashly Copilot</h2>', unsafe_allow_html=True)
        st.markdown('<p style="font-size: 0.9rem; color: #666; margin-top: 0;">Your AI financial assistant</p>', unsafe_allow_html=True)

    # Chat container
    st.markdown("""
    <div style="display: flex; flex-direction: column; height: 70vh;">
        <div class="chat-container" id="chat-container">
    """, unsafe_allow_html=True)

    # Messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            message_html = f'<div class="user-message">{msg["content"]}</div>'
            if "files" in msg:
                for file in msg["files"]:
                    message_html += f'<div class="file-attachment">📎 {file}</div>'
            st.markdown(message_html, unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">{msg["content"]}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # End chat-container

    # File uploader and input
    uploaded_files = st.file_uploader("Upload PDF or text files", 
                                    type=["pdf", "txt"], 
                                    accept_multiple_files=True,
                                    label_visibility="collapsed")

    input_col1, input_col2 = st.columns([5, 1])
    with input_col1:
        user_input = st.text_input("Message", 
                                 label_visibility="collapsed", 
                                 placeholder="Ask Cashly Copilot a question...")
    with input_col2:
        send_button = st.button("Send")

    st.markdown('</div>', unsafe_allow_html=True)  # End main flex container

# Scroll and interaction logic
st.markdown("""
<script>
    function scrollToBottom() {
        const chatContainer = document.getElementById('chat-container');
        if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    window.addEventListener('load', scrollToBottom);
    const observer = new MutationObserver(scrollToBottom);
    observer.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)

# Message processing
if send_button and (user_input or uploaded_files):
    file_names = [file.name for file in uploaded_files]
    
    user_message = {"role": "user", "content": user_input}
    if file_names:
        user_message["files"] = file_names
        st.session_state.uploaded_files.extend(uploaded_files)
    
    st.session_state.messages.append(user_message)
    agent_response = send_message_to_agent(user_input, uploaded_files)
    st.session_state.messages.append({"role": "assistant", "content": agent_response})
    st.rerun()