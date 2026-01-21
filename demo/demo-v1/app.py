import streamlit as st
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import boto3
import uuid
import os
import time
from datetime import datetime

# Local imports
from utils import cognito_auth, data_export

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
        "default_system_prompt": None
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
        session_number = st.text_input("Session Number", key="session_number")
        # Session Password removed - handled by Cognito
        
        submitted = st.form_submit_button("Start Session", use_container_width=True)

        if submitted:
            # Trim trailing spaces from all inputs
            first_name = first_name.strip() if first_name else first_name
            last_name = last_name.strip() if last_name else last_name
            major = major.strip() if major else major
            session_number = session_number.strip() if session_number else session_number

            if first_name and last_name and college_year and major and session_number:
                unique_id = str(uuid.uuid4())
                st.session_state["student_info"] = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "college_year": college_year,
                    "major": major,
                    "session_number": session_number,
                    "unique_id": unique_id,
                    "email": auth_email
                }
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
session_number = student_info["session_number"]
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
    st.text(f"Session: {session_number}")

    st.divider()

    st.markdown("### 📋 Demo Instructions")
    st.markdown("1. ***Using ArchPal***: Type and send your message in the chat input below to get started.")
    st.markdown("2. **Chat with ArchPal**: Ask questions about your writing project. Provide short sample text when appropriate.")
    st.markdown("3. **Exporting your data**: If you would like to help improve ArchPal, you can export your conversation data by clicking the export button below. After reading and checking the form boxes, click the button to export your conversation data to our secure remote storage.")
    st.markdown("4. **Starting a new conversation**: After you have exported your conversation data (if you chose to), you can start a new conversation refreshing the page and begining a new session, adding +1 to the session number.")

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

        st.chat_message("assistant", avatar=ICON_PATH).write(response.content)
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.stop()

# Step 3: Export button
st.divider()
col_export1, col_export2 = st.columns([3, 1])

with col_export1:
    st.markdown("### 📊 Export Conversation")

with col_export2:
    export_clicked = st.button("📥 Export Chat", use_container_width=True, type="primary")

if export_clicked:
    if not st.session_state.message_log:
        st.warning("No conversation to export yet.")
    else:
        # Show consent modal instead of immediately exporting
        st.session_state["show_export_consent"] = True
        st.rerun()

# Export Consent Modal
if st.session_state["show_export_consent"]:
    with st.container():
        st.markdown("---")
        st.markdown("### 📋 Export Consent & Privacy Agreement")
        st.markdown("Before exporting your conversation data, please review and confirm the following:")

        # Checkbox 1: Consent form authorization
        consent_signed = st.checkbox(
            "I have signed and authorized the consent form",
            key="consent_checkbox_modal",
            value=st.session_state.get("consent_signed", False)
        )

        # Checkbox 2: Data privacy acknowledgment
        privacy_acknowledged = st.checkbox(
            "We want you to trust that we care about your privacy and anonimity while helping archpal improve. I understand my conversation data will be stored in two separate secure locations: one with my raw conversation data (including my name) for matching with the consent form, and one with anonymized data (names replaced with [NAME]) for research and improvements. I understand that only the anonomized data will be viewed or used for research purposes.",
            key="privacy_checkbox_modal",
            value=st.session_state.get("data_privacy_acknowledged", False)
        )

        st.markdown("---")

        # Export button only enabled when both checkboxes are checked
        export_enabled = consent_signed and privacy_acknowledged
        export_button_text = "✅ Proceed with Export" if export_enabled else "✅ Proceed with Export (Check boxes above to enable)"

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("❌ Cancel", use_container_width=True, type="secondary"):
                st.session_state["show_export_consent"] = False
                st.session_state["consent_signed"] = False
                st.session_state["data_privacy_acknowledged"] = False
                st.rerun()

        with col2:
            if st.button(export_button_text, use_container_width=True, type="primary", disabled=not export_enabled):
                # Update session state with checkbox values
                st.session_state["consent_signed"] = consent_signed
                st.session_state["data_privacy_acknowledged"] = privacy_acknowledged

                # Close modal and show loading
                st.session_state["show_export_consent"] = False

                # Show loading spinner during export
                with st.spinner("📤 Exporting your conversation data..."):
                    
                    # Use the new utility function for export
                    export_success = data_export.handle_export(
                        st.session_state["student_info"],
                        st.session_state["message_log"]
                    )

                # Show result message
                if export_success:
                    st.success("🎉 Your conversations have been submitted. Thank you for helping improve ArchPal!")
                    st.balloons()  # Add celebratory balloons
                    # Keep success message visible for 3 seconds
                    time.sleep(3)
                else:
                    st.error("❌ Export failed. Please try again or contact support.")

                # Reset checkbox states after export attempt
                st.session_state["consent_signed"] = False
                st.session_state["data_privacy_acknowledged"] = False

                st.rerun()
