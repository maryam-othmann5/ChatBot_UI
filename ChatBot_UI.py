import time
from datetime import datetime
import streamlit as st

# ------------------- Session State -------------------

if "users" not in st.session_state:
    st.session_state.users = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "greeted" not in st.session_state:
    st.session_state.greeted = False

# ------------------- Auth UI -------------------

def auth_interface():
    st.title("🦙 Welcome to Llama 2 Chatbot")

    tabs = st.tabs(["🔐 Sign In", "🆕 Create Account"])

    with tabs[0]:
        with st.form("sign_in"):
            username = st.text_input("Username", key="sign_user")
            password = st.text_input("Password", type="password", key="sign_pass")
            if st.form_submit_button("Sign In"):
                if username in st.session_state.users and st.session_state.users[username] == password:
                    st.session_state.current_user = username
                    st.success(f"Signed in as {username}")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    with tabs[1]:
        with st.form("create_account"):
            new_user = st.text_input("New Username", key="new_user")
            new_pass = st.text_input("New Password", type="password", key="new_pass")
            if st.form_submit_button("Create Account"):
                if new_user in st.session_state.users:
                    st.warning("Username already exists.")
                elif new_user and new_pass:
                    st.session_state.users[new_user] = new_pass
                    st.session_state.current_user = new_user
                    st.success("Account created and signed in.")
                    st.rerun()
                else:
                    st.warning("Both fields are required.")

# ------------------- Main -------------------

def main():
    st.set_page_config("🦙 Chatbot", "🦙", layout="wide")

    # -------------------Design chat -----------------

    st.markdown("""
    <style>
    body {background-color: #f8f9fa;}
    .block-container {padding: 2rem;}
    .message {margin-bottom: 0.5rem;}
    .user-msg {color: #1565c0; font-weight: bold;}
    .bot-msg {color: #2e7d32;}
    .sidebar .stButton>button {background: #1976d2; color: white;}
    .sidebar .stButton>button:hover {background: #115293;}
    
 /**
 * Professional Chatbot UI - CSS Styling
 */

 :root {
    /* Color variables */
    --primary-color: #4285f4;
    --primary-dark: #3367d6;
    --secondary-color: #34a853;
    --accent-color: #ea4335;
    --light-bg: #f8f9fa;
    --dark-bg: #202124;
    --light-text: #202124;
    --dark-text: #e8eaed;
    --light-border: #dadce0;
    --chat-user-bg: #e3f2fd;
    --chat-bot-bg: #f5f5f5;
    --chat-dark-user-bg: #174ea6;
    --chat-dark-bot-bg: #303134;
    
    /* Spacing */
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;
    
    /* Sizing */
    --border-radius-sm: 8px;
    --border-radius-md: 12px;
    --border-radius-lg: 20px;
    
    /* Typography */
    --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    --font-size-sm: 0.875rem;
    --font-size-md: 1rem;
    --font-size-lg: 1.125rem;
    --font-weight-normal: 400;
    --font-weight-medium: 500;
    --font-weight-bold: 600;
    
    /* Animation */
    --transition-fast: 0.15s ease;
    --transition-normal: 0.3s ease;
}

/* Base styles */
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: var(--font-family);
    font-size: var(--font-size-md);
    line-height: 1.5;
    color: var(--light-text);
    background-color: var(--light-bg);
    transition: background-color var(--transition-normal), color var(--transition-normal);
}

/* Dark mode */
body.dark-mode {
    color: var(--dark-text);
    background-color: var(--dark-bg);
}

/* Chat container */
.chat-container {
    display: flex;
    flex-direction: column;
    max-width: 1200px;
    height: 100vh;
    margin: 0 auto;
    padding: var(--spacing-md);
}

/* Header */
.chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-md) 0;
    margin-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--light-border);
}

.chat-header h1 {
    font-size: 1.5rem;
    font-weight: var(--font-weight-bold);
    color: var(--primary-color);
    margin: 0;
}

.header-actions {
    display: flex;
    gap: var(--spacing-sm);
}

/* Main chat area */
.chat-main {
    display: flex;
    flex: 1;
    overflow: hidden;
    border-radius: var(--border-radius-md);
    background-color: white;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

body.dark-mode .chat-main {
    background-color: #1e1e1e;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}

/* Messages container */
.messages-container {
    flex: 1;
    padding: var(--spacing-md);
    overflow-y: auto;
    scroll-behavior: smooth;
}

/* Message styling */
.message {
    margin-bottom: var(--spacing-md);
    max-width: 80%;
    animation: fadeIn 0.3s ease;
}

.user-message {
    margin-left: auto;
    background-color: var(--chat-user-bg);
    border-radius: var(--border-radius-md) 0 var(--border-radius-md) var(--border-radius-md);
    color: var(--light-text);
}

.bot-message {
    margin-right: auto;
    background-color: var(--chat-bot-bg);
    border-radius: 0 var(--border-radius-md) var(--border-radius-md) var(--border-radius-md);
    color: var(--light-text);
}

body.dark-mode .user-message {
    background-color: var(--chat-dark-user-bg);
    color: var(--dark-text);
}

body.dark-mode .bot-message {
    background-color: var(--chat-dark-bot-bg);
    color: var(--dark-text);
}

.message-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    padding: var(--spacing-xs) var(--spacing-md);
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

body.dark-mode .message-header {
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.message-time {
    font-size: 0.75rem;
    color: rgba(0, 0, 0, 0.5);
    margin-left: var(--spacing-sm);
}

body.dark-mode .message-time {
    color: rgba(255, 255, 255, 0.5);
}

.message-content {
    padding: var(--spacing-sm) var(--spacing-md);
    word-break: break-word;
}

.message-content p {
    margin-bottom: var(--spacing-sm);
}

.message-content p:last-child {
    margin-bottom: 0;
}

.message-content pre {
    background-color: rgba(0, 0, 0, 0.05);
    border-radius: var(--border-radius-sm);
    padding: var(--spacing-sm);
    overflow-x: auto;
    margin: var(--spacing-sm) 0;
}

body.dark-mode .message-content pre {
    background-color: rgba(255, 255, 255, 0.05);
}

.message-content code {
    font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
    font-size: var(--font-size-sm);
    background-color: rgba(0, 0, 0, 0.05);
    padding: 2px 4px;
    border-radius: 3px;
}

body.dark-mode .message-content code {
    background-color: rgba(255, 255, 255, 0.1);
}

/* Typing indicator */
.typing-indicator {
    display: flex;
    align-items: center;
    padding: var(--spacing-md);
    max-width: 100px;
}

.dots-container {
    display: flex;
    align-items: center;
}

.dot {
    height: 8px;
    width: 8px;
    border-radius: 50%;
    background-color: rgba(0, 0, 0, 0.5);
    margin: 0 2px;
    animation: bounce 1.5s infinite ease-in-out;
}

body.dark-mode .dot {
    background-color: rgba(255, 255, 255, 0.5);
}

.dot:nth-child(1) {
    animation-delay: 0s;
}

.dot:nth-child(2) {
    animation-delay: 0.2s;
}

.dot:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-5px); }
}

/* Chat input area */
.chat-input-container {
    display: flex;
    align-items: center;
    padding: var(--spacing-md);
    border-top: 1px solid var(--light-border);
    background-color: white;
}

body.dark-mode .chat-input-container {
    background-color: #1e1e1e;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.input-wrapper {
    display: flex;
    flex: 1;
    position: relative;
}

.chat-input {
    flex: 1;
    border: 1px solid var(--light-border);
    border-radius: var(--border-radius-lg);
    padding: var(--spacing-sm) var(--spacing-lg);
    padding-right: 50px;
    font-family: inherit;
    font-size: var(--font-size-md);
    min-height: 50px;
    max-height: 150px;
    resize: none;
    overflow-y: auto;
    transition: border-color var(--transition-fast);
}

body.dark-mode .chat-input {
    background-color: #303134;
    border-color: rgba(255, 255, 255, 0.1);
    color: var(--dark-text);
}

.chat-input:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.2);
}

/* Buttons */
.chat-button {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: none;
    background-color: transparent;
    color: var(--primary-color);
    cursor: pointer;
    transition: background-color var(--transition-fast);
}

.chat-button:hover {
    background-color: rgba(66, 133, 244, 0.1);
}

body.dark-mode .chat-button:hover {
    background-color: rgba(66, 133, 244, 0.2);
}

.send-button {
    margin-left: var(--spacing-sm);
    background-color: var(--primary-color);
    color: white;
}

    </style>
    """, unsafe_allow_html=True)




    if not st.session_state.current_user:
        auth_interface()
        return

    st.sidebar.markdown(f"👤 **User:** {st.session_state.current_user}")
    if st.sidebar.button("🚪 Sign Out"):
        st.session_state.current_user = None
        st.session_state.greeted = False
        st.rerun()

    st.sidebar.markdown("### 📚 Chat Options")
    if st.sidebar.button("➕ New Chat"):
        start_new_chat()
        st.session_state.greeted = False

    if st.sidebar.button("🧹 Clear History"):
        st.session_state.conversations = {}
        start_new_chat()
        st.session_state.greeted = False

    if "conversations" not in st.session_state:
        st.session_state.conversations = {}
    if "current_chat_id" not in st.session_state:
        start_new_chat()

    sidebar_conversations()
    chat_interface()

# ------------------- Chat Core -------------------

def start_new_chat():
    chat_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.current_chat_id = chat_id
    st.session_state.conversations[chat_id] = {
        "title": "New Chat",
        "messages": [],
        "created": chat_id
    }
    st.session_state.greeted = False

def sidebar_conversations():
    for cid, convo in list(st.session_state.conversations.items()):
        with st.sidebar.expander(convo["title"], expanded=False):
            if st.button("🗂 Open", key=f"open_{cid}"):
                st.session_state.current_chat_id = cid

            new_title = st.text_input("Rename", convo["title"], key=f"rename_{cid}")
            st.session_state.conversations[cid]["title"] = new_title

            if st.button("🗑 Delete", key=f"delete_{cid}"):
                del st.session_state.conversations[cid]
                if cid == st.session_state.current_chat_id:
                    start_new_chat()
                st.rerun()

            export_data = export_chat(convo)
            st.download_button("📁 Export Chat", export_data, f"{new_title}.txt", mime="text/plain", key=f"export_{cid}")

def chat_interface():
    st.title("🦙💬 Llama 2 Chatbot")
    st.markdown(f"### 👋 Hello, {st.session_state.current_user}!")

    current_id = st.session_state.current_chat_id
    chat = st.session_state.conversations[current_id]

    for msg in chat["messages"]:
        if msg["role"] == "user":
            st.markdown(f"<div class='message user-msg'>🧑 You: {msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='message bot-msg'>🤖 Bot: {msg['content']}</div>", unsafe_allow_html=True)

    user_input = st.chat_input("Type your message here...")
    if user_input:
        chat["messages"].append({"role": "user", "content": user_input})

        with st.spinner("Bot is thinking..."):
            time.sleep(1)
            # Only greet once
            if "hello" in user_input.lower() and not st.session_state.greeted:
                response = f"Hi {st.session_state.current_user}, how can I help you today?"
                st.session_state.greeted = True
            else:
                response = f"You said: {user_input}"

        chat["messages"].append({"role": "bot", "content": response})

def export_chat(convo):
    return "\n".join([f"{'You' if m['role'] == 'user' else 'Bot'}: {m['content']}" for m in convo["messages"]])

# ------------------- Run -------------------

if __name__ == "__main__":
    main()
