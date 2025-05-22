import re
import time
import streamlit as st
from datetime import datetime

# ------------------- Session State -------------------

if "users" not in st.session_state:
    st.session_state.users = {}

if "current_user" not in st.session_state:
    st.session_state.current_user = None

if "greeted" not in st.session_state:
    st.session_state.greeted = False

if "users_data" not in st.session_state:
    st.session_state.users_data = {}  # Holds conversations per user

# ------------------- Utilities -------------------

def get_user_chats():
    user = st.session_state.current_user
    if user not in st.session_state.users_data:
        st.session_state.users_data[user] = {
            "conversations": {},
            "current_chat_id": None
        }
    return st.session_state.users_data[user]

def generate_title(message: str):
    keywords = re.findall(r"\b[a-zA-Z]{4,}\b", message.lower())
    blacklist = {"this", "that", "have", "from", "with", "what", "about", "which"}
    title_words = [w.capitalize() for w in keywords if w not in blacklist]
    return " ".join(title_words[:3]) or "New Chat"

def export_chat(convo):
    return "\n".join([f"{'You' if m['role'] == 'user' else 'Bot'}: {m['content']}" for m in convo["messages"]])

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

# ------------------- Chat Logic -------------------

def start_new_chat(first_message=None):
    chat_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_data = get_user_chats()
    title = generate_title(first_message) if first_message else "New Chat"
    user_data["current_chat_id"] = chat_id
    user_data["conversations"][chat_id] = {
        "title": title,
        "messages": [],
        "created": chat_id
    }
    st.session_state.greeted = False

def sidebar_conversations():
    user_data = get_user_chats()
    for cid, convo in list(user_data["conversations"].items()):
        with st.sidebar.expander(convo["title"], expanded=False):
            if st.button("🗂 Open", key=f"open_{cid}"):
                user_data["current_chat_id"] = cid

            new_title = st.text_input("Rename", convo["title"], key=f"rename_{cid}")
            user_data["conversations"][cid]["title"] = new_title

            if st.button("🗑 Delete", key=f"delete_{cid}"):
                del user_data["conversations"][cid]
                if cid == user_data["current_chat_id"]:
                    start_new_chat()
                st.rerun()

            export_data = export_chat(convo)
            st.download_button("📁 Export Chat", export_data, f"{new_title}.txt", mime="text/plain", key=f"export_{cid}")

# ---------------------------Chat Interface-----------------------------------

def chat_interface():
    user_data = get_user_chats()

    st.title("🦙💬 Llama 2 Chatbot")
    st.markdown(f"### 👋 Hello, {st.session_state.current_user}!")

    current_id = user_data["current_chat_id"]
    chat = user_data["conversations"].get(current_id)

    if not chat:
        return

    # ---------------- CSS: Pin Chat Input + Hide File Box ----------------
    st.markdown("""
    <style>
    .block-container { padding-bottom: 120px !important; }
    .stChatInputContainer {
        position: fixed;
        bottom: 20px;
        left: 280px;
        right: 20px;
        background: rgba(30,30,38,0.95);
        border-radius: 20px;
        padding: 10px 16px;
        z-index: 1001;
    }
    .stFileUploader {
        position: fixed;
        bottom: 80px;
        left: 300px;
        z-index: 1002;
    }
    </style>
    """, unsafe_allow_html=True)

    # ---------------- Show chat history ----------------
    for msg in chat["messages"]:
        with st.chat_message("user" if msg["role"] == "user" else "assistant", avatar="🧑" if msg["role"] == "user" else "🤖"):
            st.write(msg["content"])

    # ---------------- Input Bar & Upload ----------------
    uploaded_file = st.file_uploader("📎", label_visibility="collapsed", key="upload_input")
    user_input = st.chat_input("Ask anything...")

    # ---------------- File & Input State Guards ----------------
    if "last_uploaded_file" not in st.session_state:
        st.session_state.last_uploaded_file = None

    if "last_input" not in st.session_state:
        st.session_state.last_input = ""

    new_file_uploaded = uploaded_file is not None and (
        st.session_state.last_uploaded_file is None or uploaded_file.name != st.session_state.last_uploaded_file.name
    )

    new_text_input = user_input and user_input != st.session_state.last_input

    # ---------------- Process ----------------
    if new_file_uploaded or new_text_input:
        if not chat["messages"]:
            chat["title"] = generate_title(user_input or uploaded_file.name)

        if new_text_input:
            chat["messages"].append({"role": "user", "content": user_input})
            st.session_state.last_input = user_input

        if new_file_uploaded:
            file_msg = f"[📎 Uploaded: {uploaded_file.name} ({uploaded_file.size / 1024:.2f} KB)]"
            chat["messages"].append({"role": "user", "content": file_msg})
            st.session_state.last_uploaded_file = uploaded_file

        # Generate bot reply
        if new_file_uploaded:
            response = f"📄 Got your file `{uploaded_file.name}`. What would you like me to do with it?"
        elif "hello" in (user_input or "").lower() and not st.session_state.greeted:
            response = f"Hi {st.session_state.current_user}, how can I help you today?"
            st.session_state.greeted = True
        else:
            response = f"You said: {user_input}"

        chat["messages"].append({"role": "bot", "content": response})
        st.rerun()

# ------------------- Main App -------------------

def main():
    st.set_page_config("🦙 Chatbot", "🦙", layout="wide")
    
    # Custom CSS to modify layout
    st.markdown("""
    <style>
    .main .block-container {
        padding-bottom: 120px;
    }
    </style>
    """, unsafe_allow_html=True)

    if not st.session_state.current_user:
        auth_interface()
        return

    # Sidebar
    st.sidebar.markdown(f"👤 **User:** {st.session_state.current_user}")
    if st.sidebar.button("🚪 Sign Out"):
        st.session_state.current_user = None
        st.session_state.greeted = False
        st.rerun()

    if st.sidebar.button("➕ New Chat"):
        start_new_chat()
        st.session_state.greeted = False

    if st.sidebar.button("🧹 Clear History"):
        user_data = get_user_chats()
        user_data["conversations"] = {}
        start_new_chat()
        st.session_state.greeted = False

    # Ensure user has a chat session
    user_data = get_user_chats()
    if not user_data["conversations"]:
        start_new_chat()
    elif not user_data["current_chat_id"]:
        user_data["current_chat_id"] = list(user_data["conversations"].keys())[0]

    sidebar_conversations()
    chat_interface()

if __name__ == "__main__":
    main()
