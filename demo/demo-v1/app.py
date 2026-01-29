import streamlit as st
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import boto3
import uuid
import os
import time
from datetime import datetime

# Local imports
from utils import cognito_auth, data_export, s3_storage

# Constants
ICON_PATH = os.path.join(os.path.dirname(__file__), "figs", "icon.jpg")
LOGO_PATH = os.path.join(os.path.dirname(__file__), "figs", "logo.png")

# Cache for secrets to avoid repeated access
_secrets_cache = None

def get_secrets():
    """Get cached secrets to avoid repeated access"""
    global _secrets_cache
    if _secrets_cache is None:
        _secrets_cache = st.secrets
    return _secrets_cache

def initialize_session_state():
    """Initialize all session state variables with default values"""
    defaults = {
        "student_info": None,
        "messages": [],
        "message_log": [],
        "show_export_consent": False,
        "consent_signed": False,
        "data_privacy_acknowledged": False,
        "chat_model": None,
        "chat_model_config": None,
        "default_system_prompt": None,
        "current_conversation_id": None,
        "conversation_history": [],
        "s3_user_info_loaded": False
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # Initialize Auth State
    cognito_auth.init_auth_state()

# Initialize session state
initialize_session_state()

# Step 0: Authentication
if not cognito_auth.login():
    st.stop()

# Step 0.5: Load user info from S3 if available
cognito_user_id = st.session_state.get("cognito_user_id")
if cognito_user_id and not st.session_state.get("s3_user_info_loaded"):
    # Try to load user info from S3
    user_info = s3_storage.get_user_info(cognito_user_id)
    if user_info:
        # User info exists in S3, populate session state
        st.session_state["student_info"] = {
            "first_name": user_info.get("first_name", ""),
            "last_name": user_info.get("last_name", ""),
            "college_year": user_info.get("college_year", ""),
            "major": user_info.get("major", ""),
            "course_number": user_info.get("course_number", ""),
            "unique_id": user_info.get("unique_identifier", str(uuid.uuid4())),
            "email": user_info.get("email", st.session_state.get("auth_user", {}).get("email", ""))
        }
        st.session_state["s3_user_info_loaded"] = True
        st.rerun()
    else:
        # Mark as checked so we don't keep trying
        st.session_state["s3_user_info_loaded"] = True

# Step 1: Startup form for student information
if st.session_state["student_info"] is None:
    st.title("📝 Hello there! I'm ArchPal, UGA's New AI Writing Coach!")
    st.markdown("Please enter some basic information to help me get to know you better and tailor my coaching to you.")
    
    with st.form("student_info_form"):
        # Pre-fill email from auth user if available
        auth_email = st.session_state.get("auth_user", {}).get("email", "")
        if auth_email:
            st.info(f"Logged in as: {auth_email}")
            
        first_name = st.text_input("First Name", key="first_name")
        last_name = st.text_input("Last Name", key="last_name")
        college_year = st.selectbox("College Year", ["First Year", "Second Year", "Upper-Division", "Masters Student", "PhD Student"], key="college_year")
        major = st.text_input("Major", key="major")
        course_number = st.text_input("Course Number", key="course_number")
        
        submitted = st.form_submit_button("Start Session", use_container_width=True)

        if submitted:
            # Trim trailing spaces from all inputs
            first_name = first_name.strip() if first_name else first_name
            last_name = last_name.strip() if last_name else last_name
            major = major.strip() if major else major
            course_number = course_number.strip() if course_number else course_number

            if first_name and last_name and college_year and major and course_number:
                unique_id = str(uuid.uuid4())
                student_info_dict = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "college_year": college_year,
                    "major": major,
                    "course_number": course_number,
                    "unique_id": unique_id,
                    "email": auth_email
                }
                st.session_state["student_info"] = student_info_dict
                
                # Save user info to S3
                if cognito_user_id:
                    user_info_for_s3 = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "college_year": college_year,
                        "major": major,
                        "course_number": course_number,
                        "unique_identifier": unique_id,
                        "email": auth_email
                    }
                    s3_storage.save_user_info(cognito_user_id, user_info_for_s3)
                
                st.rerun()
            else:
                st.error("Please fill in all fields.")
    st.stop()

# Get student info
student_info = st.session_state["student_info"]
first_name = student_info["first_name"]
last_name = student_info["last_name"]
college_year = student_info["college_year"]
major = student_info["major"]
course_number = student_info["course_number"]
unique_id = student_info["unique_id"]

# Build default system prompt with student context (only if not cached or student info changed)
def build_default_system_prompt(first_name, last_name, college_year, major):
    """Build default system prompt with student context"""
    secrets = get_secrets()
    system_prompt_from_secrets = secrets.get('SYSTEM_PROMPT', '')
    return f"""You are ArchPal, UGA's writing coach and friendly helpful companion. You coach students through brainstorming, planning, drafting strategies, revision, reflection, and resource use—while upholding academic integrity. You do not write or substantially edit assignment prose. Instead, you help students grow their own writing skills by serving as a companion to their own process and work.

{system_prompt_from_secrets}

Student Information:
- Name: {first_name} {last_name}
- College Year: {college_year}
- Major: {major}
"""

# Cache default system prompt in session state
if st.session_state["default_system_prompt"] is None:
    st.session_state["default_system_prompt"] = build_default_system_prompt(
        first_name, last_name, college_year, major
    )
default_system_prompt_full = st.session_state["default_system_prompt"]




# Main title
col1, col2 = st.columns([1, 4])
with col1:
    st.image(LOGO_PATH, width=120)
with col2:
    st.title("ArchPal: AI Writing Coach")
    st.caption("A small group of interdisciplinary UGA students and instructors are developing ArchPal: a new AI companion to help you plan, research, brainstorm, and create for any writing project! ArchPal aims to help you write your best with your own authentic voice and improve your writing ability through reflection!")


# Get secrets
secrets = get_secrets()

# Use default system prompt
system_prompt = default_system_prompt_full

# Sidebar for student info
with st.sidebar:
    # User info and Logout
    if st.session_state.get("authenticated"):
        auth_email = st.session_state.get("auth_user", {}).get("email", "User")
        st.write(f"Logged in as: **{auth_email}**")
        if st.button("LOGOUT", type="primary", use_container_width=True):
            cognito_auth.logout()

    st.divider()

    st.markdown("### Student Information")
    st.text(f"Name: {first_name} {last_name}")
    st.text(f"Course: {course_number}")

    st.divider()

    # Load conversation history from S3
    if cognito_user_id and not st.session_state.get("conversation_history"):
        st.session_state["conversation_history"] = s3_storage.get_conversation_history(cognito_user_id, limit=5)
    
    # Display conversation history
    st.markdown("### 💬 Conversation History")
    conversation_history = st.session_state.get("conversation_history", [])
    
    if conversation_history:
        for conv in conversation_history:
            conv_id = conv.get("conversation_id")
            conv_title = conv.get("title", "Untitled Conversation")
            conv_date = conv.get("last_updated", conv.get("created_at", ""))
            # Format date for display
            try:
                if conv_date:
                    date_obj = datetime.fromisoformat(conv_date.replace("Z", "+00:00"))
                    formatted_date = date_obj.strftime("%b %d, %Y %I:%M %p")
                else:
                    formatted_date = "Unknown date"
            except:
                formatted_date = conv_date[:10] if conv_date else "Unknown"
            
            # Create button for each conversation
            button_label = f"{conv_title}\n{formatted_date}"
            if st.button(button_label, key=f"conv_{conv_id}", use_container_width=True):
                # Load conversation
                conversation_data = s3_storage.get_conversation(cognito_user_id, conv_id)
                if conversation_data:
                    # Restore messages
                    st.session_state["messages"] = []
                    st.session_state["message_log"] = []
                    st.session_state["current_conversation_id"] = conv_id
                    
                    # Convert stored messages to LangChain format
                    for msg in conversation_data.get("messages", []):
                        role = msg.get("role")
                        content = msg.get("content", "")
                        if role == "user":
                            st.session_state["messages"].append(HumanMessage(content=content))
                            # Rebuild message_log for export compatibility
                            if len(st.session_state["messages"]) > 0:
                                # Find corresponding AI message
                                msg_idx = msg.get("metadata", {}).get("message_index", 0)
                                if msg_idx + 1 < len(conversation_data.get("messages", [])):
                                    ai_msg = conversation_data["messages"][msg_idx + 1]
                                    st.session_state["message_log"].append({
                                        "userMessage": content,
                                        "userMessageTime": msg.get("timestamp", ""),
                                        "AIMessage": ai_msg.get("content", ""),
                                        "AIMessageTime": ai_msg.get("timestamp", "")
                                    })
                        elif role == "assistant":
                            st.session_state["messages"].append(AIMessage(content=content))
                    
                    st.rerun()
    else:
        st.info("No previous conversations. Start chatting to create your first conversation!")
    
    # New Conversation button
    if st.button("➕ New Conversation", use_container_width=True, type="primary"):
        st.session_state["messages"] = []
        st.session_state["message_log"] = []
        st.session_state["current_conversation_id"] = None
        # Refresh conversation history from S3
        if cognito_user_id:
            st.session_state["conversation_history"] = s3_storage.get_conversation_history(cognito_user_id, limit=5)
        st.rerun()
    
    st.divider()
    
    st.markdown("### 📋 Instructions")
    st.markdown("1. **Chat with ArchPal**: Type and send your message to get started.")
    st.markdown("2. **Resume conversations**: Click on any conversation above to continue.")
    st.markdown("3. **Export data**: Use the export button below to download your conversation data.")

# Display chat messages
if "messages" in st.session_state:
    for message in st.session_state.messages:
        if isinstance(message, HumanMessage):
            st.chat_message("user").write(message.content)
        elif isinstance(message, AIMessage):
            st.chat_message("assistant", avatar=ICON_PATH).write(message.content)

# Chat input
if prompt := st.chat_input():
    # Verify AWS credentials are configured
    secrets = get_secrets()
    aws_key = secrets.get('aws_access_key_id', '')
    aws_secret = secrets.get('aws_secret_access_key', '')
    
    # Check if credentials exist and are not placeholder values
    if (not aws_key or not aws_secret or 
        'YOUR_AWS' in aws_key or 'YOUR_AWS' in aws_secret or
        aws_key.strip() == '' or aws_secret.strip() == ''):
        st.error("⚠️ AWS credentials not configured properly in secrets.toml")
        st.info("Please update `.streamlit/secrets.toml` with your actual AWS credentials and restart Streamlit.")
        st.code(f"Current aws_access_key_id: {aws_key[:10]}... (length: {len(aws_key)})", language="text")
        st.stop()

    # Add user message to session state with timestamp
    user_timestamp = datetime.now()
    user_message = HumanMessage(content=prompt)
    st.session_state.messages.append(user_message)

    st.chat_message("user").write(prompt)

    # Get or create cached Claude chat model via AWS Bedrock
    secrets = get_secrets()
    
    # Create Bedrock client with AWS credentials
    bedrock_client = boto3.client(
        service_name='bedrock-runtime',
        region_name=secrets.get('aws_region', 'us-east-1'),
        aws_access_key_id=secrets.get('aws_access_key_id'),
        aws_secret_access_key=secrets.get('aws_secret_access_key')
    )
    
    model_config = {
        "model_id": secrets.get("anthropic_model"),
        "region_name": secrets.get('aws_region', 'us-east-1'),
        "temperature": secrets.get("anthropic_temperature"),
        "max_tokens": secrets.get("anthropic_max_tokens")
    }
    
    # Check if model needs to be recreated (config changed or doesn't exist)
    cached_config = st.session_state["chat_model_config"]
    config_changed = (
        cached_config is None or
        cached_config.get("model_id") != model_config["model_id"] or
        cached_config.get("region_name") != model_config["region_name"] or
        cached_config.get("temperature") != model_config["temperature"] or
        cached_config.get("max_tokens") != model_config["max_tokens"]
    )
    
    if st.session_state["chat_model"] is None or config_changed:
        st.session_state["chat_model"] = ChatBedrock(
            client=bedrock_client,
            model_id=model_config["model_id"],
            model_kwargs={
                "temperature": model_config["temperature"],
                "max_tokens": model_config["max_tokens"]
            }
        )
        st.session_state["chat_model_config"] = model_config.copy()
    
    chat = st.session_state["chat_model"]

    # Prepare messages for LangChain (system prompt + conversation history)
    langchain_messages = [SystemMessage(content=system_prompt)]
    langchain_messages.extend(st.session_state.messages)

    # Get response from Claude
    try:
        with st.spinner("ArchPal is thinking..."):
            response = chat.invoke(langchain_messages)
        ai_message = AIMessage(content=response.content)
        st.session_state.messages.append(ai_message)

        # Step 2: Save conversation pair to log with timestamps
        ai_timestamp = datetime.now()
        st.session_state.message_log.append({
            "userMessage": prompt,
            "userMessageTime": user_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "AIMessage": response.content,
            "AIMessageTime": ai_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        })

        # Step 2.5: Save to S3
        if cognito_user_id:
            # Get or create conversation ID
            conversation_id = st.session_state.get("current_conversation_id")
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                st.session_state["current_conversation_id"] = conversation_id
                
                # Use current time for conversation title
                conv_title = datetime.now().strftime("%b %d, %Y %I:%M %p")
                
                # Add to conversation history
                s3_storage.add_conversation_to_history(cognito_user_id, conversation_id, title=conv_title)
                # Refresh conversation history
                st.session_state["conversation_history"] = s3_storage.get_conversation_history(cognito_user_id, limit=5)
            
            # Append user message
            s3_storage.append_message_to_conversation(
                cognito_user_id,
                conversation_id,
                "user",
                prompt,
                metadata={"course_number": course_number}
            )
            
            # Append AI message
            s3_storage.append_message_to_conversation(
                cognito_user_id,
                conversation_id,
                "assistant",
                response.content,
                metadata={
                    "model": secrets.get("anthropic_model", "unknown"),
                    "course_number": course_number
                }
            )
            
            # Refresh conversation history to update last_updated time in sidebar
            st.session_state["conversation_history"] = s3_storage.get_conversation_history(cognito_user_id, limit=5)
            
            # Update conversation metadata with student info
            conversation_data = s3_storage.get_conversation(cognito_user_id, conversation_id)
            if conversation_data and "metadata" not in conversation_data:
                conversation_data["metadata"] = {
                    "unique_identifier": unique_id,
                    "college_year": college_year,
                    "major": major,
                    "course_number": course_number
                }
                s3_storage.save_conversation(cognito_user_id, conversation_id, conversation_data)

        st.chat_message("assistant", avatar=ICON_PATH).write(response.content)
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.stop()

# Step 3: Export button
st.divider()
col_export1, col_export2 = st.columns([3, 1])

with col_export1:
    st.markdown("### 📄 Export Conversation")
    st.caption("Generate a printable markdown document of your conversation history")

with col_export2:
    export_clicked = st.button("📥 Export & Print", use_container_width=True, type="primary")

if export_clicked:
    if not st.session_state.message_log:
        st.warning("No conversation to export yet.")
    else:
        # Show loading spinner during export
        with st.spinner("📤 Generating your conversation history..."):
            # Use the utility function for export
            export_success = data_export.handle_export(
                st.session_state["student_info"],
                st.session_state["message_log"]
            )

        # Show result message and markdown preview
        if export_success:
            st.success("✅ Your conversation history has been generated!")
            
            # Display markdown preview
            markdown_content = st.session_state.get("export_markdown", "")
            markdown_filename = st.session_state.get("export_markdown_filename", "conversation.md")
            
            if markdown_content:
                st.markdown("---")
                st.markdown("### 📄 Your Conversation History")
                
                # Download button - this is the "automatic" part, as prominent as possible
                st.download_button(
                    label="⬇️ Download Markdown File",
                    data=markdown_content,
                    file_name=markdown_filename,
                    mime="text/markdown",
                    use_container_width=True,
                    type="primary"
                )
                
                st.markdown("---")
                
                # Display markdown preview (printable format)
                st.markdown("### Preview (Ready to Print)")
                st.markdown(
                    """
                    <style>
                    @media print {
                        .stApp { visibility: hidden; }
                        .stApp > div:first-child { visibility: visible; }
                        .stApp > div:first-child > div:first-child { position: absolute; left: 0; top: 0; width: 100%; }
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
                
                # Render markdown with print-friendly styling
                st.markdown(markdown_content)
                
                st.info("💡 **Tip:** Use your browser's print function (Ctrl+P / Cmd+P) to print this conversation. The download button above saves a markdown file you can open in any text editor.")
        else:
            st.error("❌ Export failed. Please try again or contact support.")
