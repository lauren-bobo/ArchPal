import streamlit as st
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import uuid
import csv
import io
from datetime import datetime
import dropbox
import os
import time

# Constants
ICON_PATH = os.path.join(os.path.dirname(__file__), "figs", "icon.jpg")
LOGO_PATH = os.path.join(os.path.dirname(__file__), "figs", "logo.png")

def initialize_session_state():
    """Initialize all session state variables with default values"""
    if "student_info" not in st.session_state:
        st.session_state["student_info"] = None
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "message_log" not in st.session_state:
        st.session_state["message_log"] = []
    if "admin_logged_in" not in st.session_state:
        st.session_state["admin_logged_in"] = False
    if "show_admin_login" not in st.session_state:
        st.session_state["show_admin_login"] = False
    if "admin_system_prompt" not in st.session_state:
        st.session_state["admin_system_prompt"] = None
    if "admin_role" not in st.session_state:
        st.session_state["admin_role"] = None
    if "show_export_consent" not in st.session_state:
        st.session_state["show_export_consent"] = False
    if "consent_signed" not in st.session_state:
        st.session_state["consent_signed"] = False
    if "data_privacy_acknowledged" not in st.session_state:
        st.session_state["data_privacy_acknowledged"] = False

# Initialize session state
initialize_session_state()

# Step 1: Startup form for student information
if st.session_state["student_info"] is None:
    st.title("📝 Hello there! I'm ArchPal, UGA's New AI Writing Coach!")
    st.markdown("Please enter some baisc information to help me get to know you better and tailor my coaching to you.")
    
    with st.form("student_info_form"):
        first_name = st.text_input("First Name", key="first_name")
        last_name = st.text_input("Last Name", key="last_name")
        college_year = st.selectbox("College Year", ["First Year", "Second Year", "Upper-Division", "Masters Student", "PhD Student"], key="college_year")
        major = st.text_input("Major", key="major")
        session_number = st.text_input("Session Number", key="session_number")
        session_password = st.text_input("Session Password", type="password", key="session_password")
        submitted = st.form_submit_button("Start Session", use_container_width=True)

        if submitted:
            # Get the correct password from secrets
            correct_password = st.secrets.get("session_password", "")

            # Trim trailing spaces from all inputs except password
            first_name = first_name.strip() if first_name else first_name
            last_name = last_name.strip() if last_name else last_name
            major = major.strip() if major else major
            session_number = session_number.strip() if session_number else session_number

            if first_name and last_name and college_year and major and session_number and session_password:
                if session_password == correct_password:
                    unique_id = str(uuid.uuid4())
                    st.session_state["student_info"] = {
                        "first_name": first_name,
                        "last_name": last_name,
                        "college_year": college_year,
                        "major": major,
                        "session_number": session_number,
                        "unique_id": unique_id
                    }
                    st.rerun()
                else:
                    st.error("❌ Incorrect session password. Please check with your session facilitator.")
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

# Build default system prompt with student context
system_prompt_from_secrets = st.secrets.get('SYSTEM_PROMPT', '')
default_system_prompt_full = f"""You are ArchPal, UGA's writing coach and friendly helpful companion. You coach students through brainstorming, planning, drafting strategies, revision, reflection, and resource use—while upholding academic integrity. You do not write or substantially edit assignment prose. Instead, you help students grow their own writing skills by serving as a companion to their own process and work.

{system_prompt_from_secrets}

Student Information:
- Name: {first_name} {last_name}
- College Year: {college_year}
- Major: {major}
"""

# Admin login function
def check_admin_credentials(username, password):
    """Check if provided credentials match admin credentials from secrets"""
    admin_username = st.secrets['admin_username']
    admin_password = st.secrets['admin_password']
    return username == admin_username and password == admin_password

# Admin login overlay
def show_admin_login():
    """Display admin login overlay"""
    st.markdown("---")
    st.markdown("### 🔐 Admin Login")
    st.markdown("Enter your credentials to access admin controls.")
    with st.form("admin_login_form"):
        username = st.text_input("Username", key="admin_username_input")
        password = st.text_input("Password", type="password", key="admin_password_input")
        col1, col2 = st.columns(2)
        with col1:
            login_submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
        with col2:
            cancel_submitted = st.form_submit_button("Cancel", use_container_width=True)

        if login_submitted:
            if check_admin_credentials(username, password):
                st.session_state["admin_logged_in"] = True
                st.session_state["show_admin_login"] = False
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
        if cancel_submitted:
            st.session_state["show_admin_login"] = False
            st.rerun()
    st.markdown("---")

# Admin controls section
def show_admin_controls():
    """Display admin-only controls"""
    st.markdown("### ⚙️ Admin Controls")
    
    # Get API key from secrets
    anthropic_api_key = st.secrets['anthropic_api_key']
    st.info("✅ API key configured via secrets")
    
    # Simple defaults - admin can customize as needed
    default_role = "You are ArchPal, UGA's writing-process companion."
    default_system_prompt = "Guide students through writing process: brainstorm → plan → draft → revise → reflect. Maintain academic integrity."
    
    # Use session state values if they exist, otherwise use defaults
    current_role = st.session_state.get("admin_role", default_role)
    current_system_prompt = st.session_state.get("admin_system_prompt", default_system_prompt_full)
    
    role = st.text_input("Role", key="role_input", value=current_role)
    system_prompt = st.text_area("System Prompt", value=current_system_prompt,
        height=100,
        key="system_prompt_input"
    )
    
    # Submit button to save changes and reinitialize LLM
    if st.button("💾 Save & Reinitialize LLM", use_container_width=True, type="primary"):
        # Save to session state
        st.session_state["admin_role"] = role
        st.session_state["admin_system_prompt"] = system_prompt
        
        # Clear conversation history to reinitialize LLM with new prompt
        st.session_state["messages"] = []
        st.session_state["message_log"] = []
        
        st.success("✅ Settings saved! Conversation history cleared. The LLM will use the new system prompt and role.")
        st.rerun()
    
    st.divider()

    # CSV download section
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 📊 Download Configuration")
        st.markdown("Download the current role and system prompt as a CSV file.")

    with col2:
        if st.button("📥 Download CSV", use_container_width=True, type="secondary"):
            # Create CSV with role and system prompt
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header row
            writer.writerow(["Role", "System Prompt"])

            # Write data row
            writer.writerow([current_role, current_system_prompt])

            csv_string = output.getvalue()
            output.close()

            # Create download link
            st.download_button(
                label="⬇️ Download CSV",
                data=csv_string,
                file_name="archpal_config.csv",
                mime="text/csv",
                key="download_config_csv"
            )

    st.divider()

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["admin_logged_in"] = False
        st.rerun()
    
    return anthropic_api_key, system_prompt

def create_csv_data(first_name, last_name, unique_id):
    """Create single row CSV data with first name, last name, and unique identifier"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "first_name",
        "last_name",
        "unique_id"
    ])
    
    writer.writerow([
        first_name,
        last_name,
        unique_id
    ])
    
    csv_string = output.getvalue()
    output.close()
    return csv_string

def build_dropbox_path(folder_key, filename):
    """Build a properly formatted Dropbox path from folder key and filename"""
    folder_path = st.secrets.get(folder_key, '')
    if folder_path and not folder_path.startswith('/'):
        folder_path = '/' + folder_path
    if folder_path and not folder_path.endswith('/'):
        folder_path = folder_path + '/'
    return f"{folder_path}{filename}"

def upload_to_dropbox(csv_data, filepath):
    """Upload CSV data to Dropbox at the specified filepath"""
    dropbox_token = st.secrets["dropbox_access_token"]
    dbx = dropbox.Dropbox(dropbox_token)
    csv_bytes = csv_data.encode('utf-8')
    dbx.files_upload(csv_bytes, filepath, mode=dropbox.files.WriteMode.overwrite)

# Main title
col1, col2 = st.columns([1, 4])
with col1:
    st.image(LOGO_PATH, width=120)
with col2:
    st.title("ArchPal: AI Writing Coach")
    st.caption("A small group of interdisciplinary UGA students and instructors are developing ArchPal: a new AI companion to help you plan, research, brainstorm, and create for any writing project! ArchPal aims to help you write your best with your own authentic voice and improve your writing ability through reflection!")

# Handle admin login overlay
if st.session_state["show_admin_login"] and not st.session_state["admin_logged_in"]:
    show_admin_login()

# Get API key from secrets
anthropic_api_key = st.secrets['anthropic_api_key']


# Use saved admin prompt if available, otherwise use default
# If admin has set a custom system prompt, it completely replaces the default
system_prompt = st.session_state.get("admin_system_prompt") or default_system_prompt_full

# Sidebar for admin controls (if logged in) or student info
with st.sidebar:
    # Admin login/logout button
    if st.session_state["admin_logged_in"]:
        if st.button("👤 Admin Panel", use_container_width=True, type="secondary"):
            st.session_state["show_admin_login"] = False
    else:
        if st.button("🔐 Admin Login", use_container_width=True, type="secondary"):
            st.session_state["show_admin_login"] = True

    st.divider()

    if st.session_state["admin_logged_in"]:
        anthropic_api_key_from_admin, _ = show_admin_controls()
        if anthropic_api_key_from_admin:
            anthropic_api_key = anthropic_api_key_from_admin
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
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        st.chat_message("user").write(message.content)
    elif isinstance(message, AIMessage):
        st.chat_message("assistant", avatar=ICON_PATH).write(message.content)

# Chat input
if prompt := st.chat_input():
    if not anthropic_api_key:
        st.info("Please add your Anthropic API key to continue.")
        st.stop()

    # Add user message to session state with timestamp
    user_timestamp = datetime.now()
    user_message = HumanMessage(content=prompt)
    st.session_state.messages.append(user_message)

    st.chat_message("user").write(prompt)

    # Create Claude chat model
    chat = ChatAnthropic(
        model=st.secrets.get("anthropic_model", "claude-3-5-sonnet-20241022"),
        anthropic_api_key=anthropic_api_key,
        temperature=st.secrets.get("anthropic_temperature", 0.7),
        max_tokens=st.secrets.get("anthropic_max_tokens", 1024)
    )

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
                    export_success = True
                    
                    try:
                        # Upload single row CSV with first name, last name, and unique identifier
                        csv_data = create_csv_data(first_name, last_name, unique_id)
                        filename = f"{last_name}_{first_name}_Session{session_number}.csv"
                        path = build_dropbox_path('dropbox_folder_path1', filename)
                        upload_to_dropbox(csv_data, path)
                        
                    except Exception as e:
                        export_success = False

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
