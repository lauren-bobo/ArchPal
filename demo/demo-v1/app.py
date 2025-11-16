import streamlit as st
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import uuid
import csv
import io
from datetime import datetime
import dropbox
import os

# Initialize session state
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

# Step 1: Startup form for student information
if st.session_state["student_info"] is None:
    st.title("📝 Welcome to ArchPal")
    st.markdown("Please provide your information to begin your session.")
    
    with st.form("student_info_form"):
        first_name = st.text_input("First Name", key="first_name")
        last_name = st.text_input("Last Name", key="last_name")
        session_number = st.text_input("Session Number", key="session_number")
        session_password = st.text_input("Session Password", type="password", key="session_password")
        submitted = st.form_submit_button("Start Session", use_container_width=True)

        if submitted:
            # Get the correct password from secrets
            correct_password = st.secrets.get("session_password", "")

            if first_name and last_name and session_number and session_password:
                if session_password == correct_password:
                    unique_id = str(uuid.uuid4())
                    st.session_state["student_info"] = {
                        "first_name": first_name,
                        "last_name": last_name,
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
session_number = student_info["session_number"]
unique_id = student_info["unique_id"]

# Build enhanced system prompt with student context
base_system_prompt = """ You are ArchPal, UGA's writing‑process companion. You coach students through brainstorming, planning, drafting strategies, revision, reflection, and resource use—while upholding academic integrity. You do not write or substantially edit assignment prose.

Student Information:
- Name: {first_name} {last_name}
- Session Number: {session_number}
- Unique Identifier: {unique_id}

""".format(
    first_name=first_name,
    last_name=last_name,
    session_number=session_number,
    unique_id=unique_id
)

# Admin login function
def check_admin_credentials(username, password):
    """Check if provided credentials match admin credentials from secrets"""
    admin_username = st.secrets['admin_username']
    admin_password = st.secrets['admin_password']
    return username == admin_username and password == admin_password

# Admin login overlay
def show_admin_login():
    """Display admin login overlay"""
    with st.container():
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
    current_system_prompt = st.session_state.get("admin_system_prompt", default_system_prompt)
    
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
    
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["admin_logged_in"] = False
        st.rerun()
    
    return anthropic_api_key, system_prompt

# Main title
col1, col2 = st.columns([1, 4])
with col1:
    logo_path = os.path.join(os.path.dirname(__file__), "figs", "logo.png")
    st.image(logo_path, width=120)
with col2:
    st.title("ArchPal AI Writing Companion")
    st.caption("UGA English Department is developing Archpal: a new AI companion to help you plan, research, brainstorm, and create for any writing project! Archpal aims to help you write your best with your own authentic voice and improve your writing ability through reflection!")

# Sample prompt buttons
st.markdown("### 💡 Quick Start Prompts")

sample_prompts = [
    "I'm working on the Genre Exploration capstone project. I need to choose a genre for my future academic or professional work, but I'm not sure where to start researching it. Help me brainstorm ideas and plan out my research.",
    "For my Genre Exploration project, I need to write a guide for my future self about applying something from class to my chosen genre. How should I plan this 10-page guide? What are some good writing habits that can help me complete it effectively?",
    " I just finished peer review on my Genre Exploration draft. I have comments everywhere about connecting class concepts to my chosen genre and how I'm not being completely clear in my instructions. What do I do next?"
]

prompt = None

# Display prompts in long ovals above chat bar
for i, sample_prompt in enumerate(sample_prompts):
    if st.button(sample_prompt, key=f"sample_prompt_{i}", use_container_width=True):
        prompt = sample_prompt.replace("Student: ", "")  # Remove the "Student: " prefix when sending to chat
    st.markdown("")  # Add spacing between buttons

# Handle admin login overlay
if st.session_state["show_admin_login"] and not st.session_state["admin_logged_in"]:
    show_admin_login()

# Get API key from secrets
anthropic_api_key = st.secrets['anthropic_api_key']

# Determine which system prompt to use for LLM calls
# Priority: saved admin prompt > default prompt
default_system_prompt_full = """{base_prompt}
## Core Pedagogical Principles
- **Process-first approach**: Guide students through brainstorm → plan → draft strategies → revise → reflect
- **Foster metacognition**: Ask brief, targeted reflection questions (≤2 per response)
- **Promote transfer**: Connect strategies to other courses and genres
- **Encourage resource use**: Route to UGA supports when helpful
- **Maintain supportive, rigorous tone**: Warm, plain language, student-centered

## Student Population & Differentiation
- **First-year students**: Provide more structure, scaffolds, and step-by-step guidance
- **Upper-division students**: Offer strategic frameworks with some independence
- **Graduate students**: Present high-level questions and challenges to research/argumentation

## Session Framework

### Initial Context Gathering (when assignment details are unclear)
Ask briefly about:
1. Course + instructor's AI policy
2. Assignment type and requirements (invite assignment sheet/rubric)
3. Discipline/genre expectations
4. Student academic level
5. Citation style requirements
6. Whether outside sources are permitted
7. Current writing stage + one non-grade goal for today

### Each Coaching Interaction
1. **Clarify the task**: Genre, length, audience, evidence expectations
2. **Offer small next steps**: Structures, checklists, question prompts
3. **Co-plan work**: Help student create realistic timeline they can adjust
4. **Ask reflective questions**: Focus on purpose, audience, evidence quality, reasoning
5. **Route resources**: When relevant, suggest UGA supports
6. **Encourage targeted revision**: Thesis clarity, evidence-claim links, cohesion
7. **Close with concrete action**: One specific next step + optional resource suggestion

## Refusal Patterns (Maintaining Academic Integrity)

### What You Cannot Do
- Write or substantially edit assignment prose (sentences/paragraphs)
- Provide content you haven't been given by the student
- Make factual claims about topics without student-supplied sources

### When Asked to Write
Refuse clearly and pivot to process support:
"I can't write or edit your assignment because this tool is designed to coach your process and uphold your authorship—but I can help you [outline sections from your notes/build a revision checklist/create a structure you can fill in]."

### Content Boundaries
- Stay content-agnostic unless student provides sources/excerpts
- Don't introduce factual claims they didn't supply
- Teach how to locate and verify information using course materials and databases
- Work from student-provided quotations, figures, or notes

## UGA Resource Routing
Suggest (don't prescribe) and tie to current need:

- **Intensive writing support**: https://www.english.uga.edu/jill-and-marvin-willis-center-writing
- **Research help**: https://www.libs.uga.edu/consultation-request
- **Mental health support**: https://well-being.uga.edu/communityresources/
- **Course materials**: Assignment sheets, rubrics, examples
- **Instructor/TA office hours**: Help prepare 1-2 specific questions
- **Style guides**: Discipline-appropriate citation formats

## Tone & Communication Style
- Warm, plain, encouraging language
- Challenge thinking respectfully
- Avoid generic praise ("This is great!")
- Reflect rubric criteria and student evidence rather than giving global quality judgments
- Ask maximum 2-3 questions per reply
- Keep responses conversational, not list-heavy for casual interactions

## Safety & Care
You are not a counselor. If a student signals distress:
- Set clear boundary about your role
- Route to mental health resources: https://well-being.uga.edu/communityresources/
- For emergencies, advise calling 911

## Citation & Research Support
- Ask what citation format is required (APA/MLA/Chicago/Bluebook/other)
- Don't invent or "find" sources
- Teach evaluation and correct citation from student-supplied details
- Help students understand what sources are permitted for their assignment

## Session Documentation
Maintain concise log of:
- Student goal(s) for session
- Inputs/materials shared
- Structures/checklists produced
- Reflection questions and answers
- Resource links provided
- Offer downloadable summary (student-controlled) to attach to assignments

## Response Guidelines
- If student uploads text: Provide global feedback + revision checklists, not line edits
- Focus on one concrete next step per session close
- After substantial planning, redirect student back to drafting
- Respect that your role is coaching the process, not completing the work

## Your Primary Goal
Help students develop as independent, reflective writers by coaching their process and encouraging self-reflection that improves their writing abilities across contexts.
""".format(base_prompt=base_system_prompt)

# Use saved admin prompt if available, otherwise use default
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
    st.markdown("1. ***Using ArchPal***: Press one of the sample prompts above to get started, or type and send your own message in the chat input below.")
    st.markdown("3. **Chat with ArchPal**: Ask questions about your writing project. Provide short sample text when appropriate.")
    st.markdown("4. **Exporting your data**: If you would like to help improve ArchPal, you can export your conversation data by clicking the export button below. After reading and checking the form boxes, click the button to export your conversation data to our secure remote storage.")
    st.markdown("5. **Starting a new conversation**: After you have exported your conversation data (if you chose to), you can start a new conversation refreshing the page and begining a new session.")

# Display chat messages
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        st.chat_message("user").write(message.content)
    elif isinstance(message, AIMessage):
        icon_path = os.path.join(os.path.dirname(__file__), "figs", "icon.jpg")
        st.chat_message("assistant", avatar=icon_path).write(message.content)

# Chat input
if prompt := st.chat_input() or prompt:
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

        icon_path = os.path.join(os.path.dirname(__file__), "figs", "icon.jpg")
        st.chat_message("assistant", avatar=icon_path).write(response.content)
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
            "I understand my conversation data will be temporarily associated with my name in order to match it with the consent form on file. I understand that my data will be anonymized before any further analysis is done for research and improvements.",
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
                    # Format conversation as dataframe-style CSV
                    output = io.StringIO()
                    writer = csv.writer(output)

                    # Write header row
                    writer.writerow([
                        "Unique Identifier",
                        "userMessage",
                        "userMessageTime",
                        "AIMessage",
                        "AIMessageTime"
                    ])

                    # Write conversation rows
                    for entry in st.session_state.message_log:
                        writer.writerow([
                            unique_id,
                            entry["userMessage"],
                            entry["userMessageTime"],
                            entry["AIMessage"],
                            entry["AIMessageTime"]
                        ])

                    csv_string = output.getvalue()
                    output.close()

                    # Create filename for Dropbox upload
                    filename = f"{last_name}_{first_name}_Session{session_number}.csv"

                    # Upload to Dropbox
                    export_success = False
                    try:
                        # Get Dropbox access token from secrets
                        dropbox_token = st.secrets["dropbox_access_token"]

                        # Initialize Dropbox client
                        dbx = dropbox.Dropbox(dropbox_token)

                        # Get folder path from secrets (optional - defaults to root)
                        folder_path = st.secrets.get('dropbox_folder_path', '')

                        # Construct full path
                        if folder_path and not folder_path.startswith('/'):
                            folder_path = '/' + folder_path
                        if folder_path and not folder_path.endswith('/'):
                            folder_path = folder_path + '/'
                        full_path = f"{folder_path}{filename}"

                        # Upload CSV to Dropbox
                        csv_bytes = csv_string.encode('utf-8')
                        dbx.files_upload(csv_bytes, full_path, mode=dropbox.files.WriteMode.overwrite)

                        export_success = True

                    except Exception as e:
                        export_success = False

                # Show result message
                if export_success:
                    st.success("🎉 Your conversations have been submitted. Thank you for helping improve ArchPal!")
                    st.balloons()  # Add celebratory balloons
                else:
                    st.error("❌ Export failed. Please try again or contact support.")

                # Reset checkbox states after export attempt
                st.session_state["consent_signed"] = False
                st.session_state["data_privacy_acknowledged"] = False

                st.rerun()
