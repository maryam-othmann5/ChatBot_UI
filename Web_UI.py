import os
import re
import sys
import pymysql
import hashlib
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from PyPDF2 import PdfReader

# ------------------------
# Load environment variables
# ------------------------
load_dotenv()

# Ensure src is in sys.path for import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from _1_Inference.rag_pipeline import run_agent, rag_pipeline

# ------------------- DB Helpers -------------------

def get_app_db_connection():
    """
    Get a connection to the application's own database (ml_proj_db).
    """
    return pymysql.connect(
        host="localhost",
        user="mluser",
        password="mlpass",
        database="ml_proj_db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

def get_user_db_connection():
    """
    Get a connection to the user's query database (the one they want to query with SQL).
    Returns a pymysql connection object or None if not connected.
    """
    if not st.session_state.user_db_connection_details:
        st.error("Please connect to a database first")
        return None
    try:
        return pymysql.connect(
            host=st.session_state.user_db_connection_details["host"],
            port=int(st.session_state.user_db_connection_details["port"]),
            user=st.session_state.user_db_connection_details["username"],
            password=st.session_state.user_db_connection_details["password"],
            database=st.session_state.user_db_connection_details["database"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

def test_user_db_connection(host, port, username, password, database):
    """
    Test connection to the user's query database.
    Returns (True, message) if successful, (False, error message) otherwise.
    """
    try:
        conn = pymysql.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            database=database,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        # Test if we can get the schema
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
        conn.close()
        return True, f"Connection successful! Found {len(tables)} tables."
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def hash_password(password):
    """
    Hash a password using SHA-256 for secure storage.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, email, password):
    """
    Create a new user in the application's own database.
    Returns True if successful, False otherwise.
    """
    try:
        conn = get_app_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, hash_password(password))
            )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error creating user: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def check_user(email, password):
    """
    Check user credentials against the application's own database.
    Returns user info if credentials are valid, None otherwise.
    """
    try:
        conn = get_app_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, name FROM users WHERE email=%s AND password_hash=%s",
                (email, hash_password(password))
            )
            result = cursor.fetchone()
            return result
    except Exception as e:
        st.error(f"Error checking credentials: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

# ------------------- DB Operations -------------------

def log_security_event(user_id, event_type, event_desc, ip_address=None):
    """
    Log a security event to the application's own database.
    """
    conn = get_app_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO security_logs (user_id, event_type, event_dec, ip_address) VALUES (%s, %s, %s, %s)",
                (user_id, event_type, event_desc, ip_address)
            )
        conn.commit()
    finally:
        conn.close()

def insert_input(user_id, input_type, input_txt=None, file_path=None):
    """
    Insert a new input record into the application's own database.
    """
    conn = get_app_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO inputs (user_id, input_type, input_txt, file_path) VALUES (%s, %s, %s, %s)",
                (user_id, input_type, input_txt, file_path)
            )
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()

def insert_document(input_id, content=None, page_number=None):
    """
    Insert a new document record into the application's own database.
    """
    conn = get_app_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO documents (input_id, content, page_number) VALUES (%s, %s, %s)",
                (input_id, content, page_number)
            )
            conn.commit()
    finally:
        conn.close()

def insert_prediction(input_id, generated_sql):
    """
    Insert a new prediction record into the application's own database.
    """
    conn = get_app_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO predictions (input_id, generated_sql) VALUES (%s, %s)",
                (input_id, generated_sql)
            )
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()

def insert_execution_result(prediction_id, result_json, execution_time, success, error_message=None):
    """
    Insert a new execution result record into the application's own database.
    """
    conn = get_app_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO execution_result (prediction_id, result_json, execution_time, success, error_message) VALUES (%s, %s, %s, %s, %s)",
                (prediction_id, result_json, execution_time, success, error_message)
            )
            conn.commit()
    finally:
        conn.close()

def insert_feedback(prediction_id, rating, comment=None):
    """
    Insert a new feedback record into the application's own database.
    """
    conn = get_app_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO feedback (prediction_id, rating, comment) VALUES (%s, %s, %s)",
                (prediction_id, rating, comment)
            )
            conn.commit()
    finally:
        conn.close()

# ------------------- Session State Initialization -------------------
# These variables help keep track of the user's session and app state.
def initialize_session_state():
    """Initialize all session state variables in one place."""
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "greeted" not in st.session_state:
        st.session_state.greeted = False
    if "users_data" not in st.session_state:
        st.session_state.users_data = {}  # Holds conversations per user
    if "user_db_connected" not in st.session_state:
        st.session_state.user_db_connected = False
    if "user_db_connection_details" not in st.session_state:
        st.session_state.user_db_connection_details = None

# ------------------- Database Connection UI -------------------
def user_database_connection_interface():
    """
    Sidebar UI for connecting to a user's own MySQL database.
    Lets the user enter host, port, username, password, and database name.
    On success, sets up the connection for the agent.
    """
    st.sidebar.markdown("### 🔌 Connect to Your Database")
    st.sidebar.markdown("""
    Connect to the database you want to query. This can be:
    - A local database on your machine
    - A remote database on another server
    - Any MySQL database you have access to
    """)
    
    with st.sidebar.form("user_db_connection_form"):
        host = st.text_input("Host", value="localhost", help="Enter 'localhost' for local database or IP/domain for remote")
        port = st.text_input("Port", value="3306", help="Default MySQL port is 3306")
        username = st.text_input("Username", help="Database user with query permissions")
        password = st.text_input("Password", type="password", help="Database user password")
        database = st.text_input("Database Name", help="Name of the database to connect to")
        
        submitted = st.form_submit_button("Connect to Database")
        
        if submitted:
            if not all([host, port, username, password, database]):
                st.error("Please fill in all fields")
            else:
                success, message = test_user_db_connection(host, port, username, password, database)
                if success:
                    st.session_state.user_db_connection_details = {
                        "host": host,
                        "port": port,
                        "username": username,
                        "password": password,
                        "database": database
                    }
                    st.session_state.user_db_connected = True
                    st.success(message)
                    # Update MYSQL_URL environment variable for the RAG pipeline
                    os.environ["MYSQL_URL"] = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
                    # Reload RAG pipeline with new connection
                    rag_pipeline.initialize()
                    st.rerun()
                else:
                    st.error(message)

# ------------------- Utilities -------------------
def get_user_chats():
    """
    Retrieve or initialize the current user's chat data from session state.
    Returns a dict with conversations and current chat id.
    """
    user = st.session_state.current_user
    if user not in st.session_state.users_data:
        st.session_state.users_data[user] = {
            "conversations": {},
            "current_chat_id": None
        }
    return st.session_state.users_data[user]

def generate_title(message: str):
    """
    Generate a simple chat title from the user's first message.
    """
    keywords = re.findall(r"\b[a-zA-Z]{4,}\b", message.lower())
    blacklist = {"this", "that", "have", "from", "with", "what", "about", "which"}
    title_words = [w.capitalize() for w in keywords if w not in blacklist]
    return " ".join(title_words[:3]) or "New Chat"

def export_chat(convo):
    """
    Export a conversation as a plain text transcript.
    """
    return "\n".join([f"{'You' if m['role'] == 'user' else 'Bot'}: {m['content']}" for m in convo["messages"]])

# ------------------- Auth UI -------------------
def auth_interface():
    """
    Main authentication UI for sign in and account creation.
    Handles user login, session creation, and account registration.
    """
    st.title("🦙 Welcome to Llama 2 Chatbot")

    tabs = st.tabs(["🔐 Sign In", "🆕 Create Account"])

    with tabs[0]:
        with st.form("sign_in"):
            email = st.text_input("Email", key="sign_email")
            password = st.text_input("Password", type="password", key="sign_pass")
            if st.form_submit_button("Sign In"):
                user = check_user(email, password)
                if user:
                    # Create session
                    import secrets
                    session_token = secrets.token_hex(32)
                    
                    # Get IP address (safely)
                    ip_address = None
                    user_agent = None
                    
                    try:
                        conn = get_app_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute(
                                "INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, expires_at) VALUES (%s, %s, %s, %s, DATE_ADD(NOW(), INTERVAL 24 HOUR))",
                                (user["id"], session_token, ip_address, user_agent)
                            )
                        conn.commit()
                        
                        # Log successful login
                        log_security_event(user["id"], "login_success", "User logged in successfully", ip_address)
                        
                    except Exception as e:
                        st.error(f"Error creating session: {str(e)}")
                    finally:
                        if conn:
                            conn.close()
                    
                    st.session_state.current_user = user["name"]
                    st.success(f"Signed in as {user['name']}")
                    st.rerun()
                else:
                    # Log failed login attempt
                    try:
                        conn = get_app_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
                            user = cursor.fetchone()
                            if user:
                                log_security_event(user["id"], "login_failed", "Failed login attempt", None)
                    except Exception as e:
                        st.error(f"Error logging failed attempt: {str(e)}")
                    finally:
                        if conn:
                            conn.close()
                    st.error("Invalid credentials")

    with tabs[1]:
        with st.form("create_account"):
            username = st.text_input("Name", key="new_user")
            email = st.text_input("Email", key="new_email")
            password = st.text_input("Password", type="password", key="new_pass")
            if st.form_submit_button("Create Account"):
                if not username or not email or not password:
                    st.warning("All fields are required.")
                else:
                    # Check if email already exists
                    try:
                        conn = get_app_db_connection()
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
                            exists = cursor.fetchone()
                            if exists:
                                st.warning("Email already exists.")
                            else:
                                if create_user(username, email, password):
                                    # Get new user ID
                                    cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
                                    user_id = cursor.fetchone()["id"]
                                    
                                    # Create session
                                    import secrets
                                    session_token = secrets.token_hex(32)
                                    cursor.execute(
                                        "INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, expires_at) VALUES (%s, %s, %s, %s, DATE_ADD(NOW(), INTERVAL 24 HOUR))",
                                        (user_id, None, None, "DATE_ADD(NOW(), INTERVAL 24 HOUR)")
                                    )
                                    conn.commit()
                                    
                                    # Log account creation
                                    log_security_event(user_id, "account_created", "New account created", None)
                                    
                                    st.session_state.current_user = username
                                    st.success("Account created and signed in.")
                                    st.rerun()
                    except Exception as e:
                        st.error(f"Error creating account: {str(e)}")
                    finally:
                        if conn:
                            conn.close()

# ------------------- Chat Logic -------------------
def start_new_chat(first_message=None):
    """
    Start a new chat session for the user, optionally with a first message.
    Initializes a new conversation in session state.
    """
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
    """
    Render the sidebar with all previous conversations for the current user.
    Allows opening, renaming, deleting, and exporting chats.
    """
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

def chat_interface():
    """
    Main chat interface for the AI chatbot.
    Displays chat history, handles user input, and shows bot responses.
    Also handles feedback and source document display.
    """
    user_data = get_user_chats()
    st.title("🦙💬 Llama 2 Chatbot")
    st.markdown(f"### 👋 Hello, {st.session_state.current_user}!")

    current_id = user_data["current_chat_id"]
    chat = user_data["conversations"].get(current_id)

    if not chat:
        return

    # Build chat history for RAG pipeline
    chat_history = [
        (msg["role"], msg["content"]) for msg in chat["messages"]
    ]

    for msg in chat["messages"]:
        if msg["role"] == "user":
            st.markdown(f"<div class='message user-msg'>🧑 You: {msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='message bot-msg'>🤖 Bot: {msg['content']}</div>", unsafe_allow_html=True)
            # Optionally show sources if present
            if msg.get("sources"):
                with st.expander("Show source documents"):
                    for i, doc in enumerate(msg["sources"]):
                        st.markdown(f"**Source {i+1}:**\n{doc.page_content[:500]}{'...' if len(doc.page_content) > 500 else ''}")
            
            # Add feedback option for bot responses
            if msg.get("prediction_id"):
                with st.expander("Rate this response"):
                    rating = st.slider("Rating", 1, 5, 3, key=f"rating_{msg['prediction_id']}")
                    comment = st.text_area("Comment (optional)", key=f"comment_{msg['prediction_id']}")
                    if st.button("Submit Feedback", key=f"feedback_{msg['prediction_id']}"):
                        insert_feedback(msg["prediction_id"], rating, comment)
                        st.success("Thank you for your feedback!")

    user_input = st.chat_input("Type your message here...")
    if user_input:
        if not chat["messages"]:
            chat["title"] = generate_title(user_input)

        # Get user ID from session (use app DB, not user DB)
        conn = get_app_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE name=%s", (st.session_state.current_user,))
            user_id = cursor.fetchone()["id"]
        conn.close()

        # Store user input in database
        input_id = insert_input(user_id, "text", input_txt=user_input)

        chat["messages"].append({"role": "user", "content": user_input})

        # Call the RAG pipeline
        with st.spinner("Bot is thinking..."):
            result, sources = run_agent(user_input, chat_history)
            
            # Store prediction in database
            prediction_id = insert_prediction(input_id, result)
            
            # Store execution result
            import json
            from datetime import datetime
            execution_time = datetime.now().time()
            insert_execution_result(
                prediction_id=prediction_id,
                result_json=json.dumps({"result": result}),
                execution_time=execution_time,
                success=True
            )

        chat["messages"].append({
            "role": "bot", 
            "content": result, 
            "sources": sources if sources else None,
            "prediction_id": prediction_id
        })
        st.rerun()

# ------------------- Document Processing -------------------
def process_uploaded_document(uploaded_file, user_id):
    """
    Process an uploaded document file, store it and extract content.
    """
    # Store file in filesystem
    docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/_1_Inference/docs'))
    os.makedirs(docs_dir, exist_ok=True)
    file_path = os.path.join(docs_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Store file metadata in database
    input_id = insert_input(user_id, "file", file_path=file_path)
    
    # Store document content in database
    try:
        # Read file content based on type
        if uploaded_file.type == "application/pdf":
            reader = PdfReader(uploaded_file)
            for page_num in range(len(reader.pages)):
                content = reader.pages[page_num].extract_text()
                insert_document(input_id, content=content, page_number=page_num + 1)
        elif uploaded_file.type in ["image/jpeg", "image/png"]:
            # For images, store the file path
            insert_document(input_id, content=f"Image file: {file_path}")
        else:
            # For other files, store the file path
            insert_document(input_id, content=f"Document file: {file_path}")
    except Exception as e:
        st.sidebar.error(f"Error processing file: {str(e)}")
        # Still store the file path even if content extraction fails
        insert_document(input_id, content=f"File: {file_path}")

    st.sidebar.success(f"Uploaded {uploaded_file.name}. Reloading RAG documents...")
    rag_pipeline.reload_documents(docs_dir)
    st.sidebar.success("RAG document store updated!")

# ------------------- Main App -------------------
def main():
    """
    Main entry point for the Streamlit app.
    Handles authentication, database connection, document upload, and chat interface.
    """
    st.set_page_config("🦙 Chatbot", "🦙", layout="wide")
    
    # Initialize session state
    initialize_session_state()

    if not st.session_state.current_user:
        auth_interface()
        return

    # Sidebar
    st.sidebar.markdown(f"👤 **User:** {st.session_state.current_user}")
    if st.sidebar.button("🚪 Sign Out"):
        st.session_state.current_user = None
        st.session_state.greeted = False
        st.session_state.user_db_connected = False
        st.session_state.user_db_connection_details = None
        st.rerun()

    # User Database Connection
    if not st.session_state.user_db_connected:
        user_database_connection_interface()
        return

    # Document upload
    st.sidebar.markdown("### 📄 Upload Document for RAG")
    uploaded_file = st.sidebar.file_uploader("Upload a document (PDF, DOCX, PNG, JPG)", type=["pdf", "docx", "doc", "png", "jpg", "jpeg"])
    if uploaded_file is not None:
        # Get user ID from session (use app DB, not user DB)
        conn = get_app_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE name=%s", (st.session_state.current_user,))
            user_id = cursor.fetchone()["id"]
        conn.close()
        
        process_uploaded_document(uploaded_file, user_id)

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