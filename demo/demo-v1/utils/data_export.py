import streamlit as st
import io
import csv
from datetime import datetime

# --- Constants & Config ---

def get_secrets():
    """Get secrets from Streamlit session"""
    return st.secrets

# --- CSV Generation ---

def create_csv_data(message_log, unique_id, college_year, major, first_name, anonymize=False):
    """Create CSV data from message log, optionally anonymizing names"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Unique Identifier",
        "College Year",
        "Major",
        "userMessage",
        "userMessageTime",
        "AIMessage",
        "AIMessageTime"
    ])
    
    for entry in message_log:
        user_message = entry["userMessage"]
        ai_message = entry["AIMessage"]
        
        if anonymize:
            user_message = user_message.replace(first_name, "[NAME]")
            ai_message = ai_message.replace(first_name, "[NAME]")
        
        writer.writerow([
            unique_id,
            college_year,
            major,
            user_message,
            entry["userMessageTime"],
            ai_message,
            entry["AIMessageTime"]
        ])
    
    csv_string = output.getvalue()
    output.close()
    return csv_string

def create_identifier_csv(first_name, last_name, unique_id):
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

# --- Markdown Generation ---

def create_markdown_conversation(student_info, message_log):
    """
    Create a printable markdown-formatted conversation history
    
    Args:
        student_info: Dictionary with student information
        message_log: List of message dictionaries with userMessage, AIMessage, and timestamps
    
    Returns:
        Markdown string formatted for printing
    """
    first_name = student_info.get("first_name", "")
    last_name = student_info.get("last_name", "")
    college_year = student_info.get("college_year", "")
    major = student_info.get("major", "")
    course_number = student_info.get("course_number", "")
    
    # Format current date/time for header
    current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    # Build markdown content
    markdown_lines = []
    
    # Header
    markdown_lines.append("# ArchPal Conversation History")
    markdown_lines.append("")
    markdown_lines.append("---")
    markdown_lines.append("")
    
    # Student Information Section
    markdown_lines.append("## Student Information")
    markdown_lines.append("")
    markdown_lines.append(f"**Name:** {first_name} {last_name}")
    markdown_lines.append(f"**College Year:** {college_year}")
    markdown_lines.append(f"**Major:** {major}")
    markdown_lines.append(f"**Course Number:** {course_number}")
    markdown_lines.append(f"**Export Date:** {current_date}")
    markdown_lines.append("")
    markdown_lines.append("---")
    markdown_lines.append("")
    
    # Conversation Section
    markdown_lines.append("## Conversation")
    markdown_lines.append("")
    
    if not message_log:
        markdown_lines.append("*No messages in this conversation.*")
    else:
        for idx, entry in enumerate(message_log, 1):
            user_message = entry.get("userMessage", "")
            ai_message = entry.get("AIMessage", "")
            user_time = entry.get("userMessageTime", "")
            ai_time = entry.get("AIMessageTime", "")
            
            # Format timestamps
            try:
                if user_time:
                    user_dt = datetime.strptime(user_time, "%Y-%m-%d %H:%M:%S")
                    formatted_user_time = user_dt.strftime("%I:%M %p")
                else:
                    formatted_user_time = ""
            except:
                formatted_user_time = user_time
            
            try:
                if ai_time:
                    ai_dt = datetime.strptime(ai_time, "%Y-%m-%d %H:%M:%S")
                    formatted_ai_time = ai_dt.strftime("%I:%M %p")
                else:
                    formatted_ai_time = ""
            except:
                formatted_ai_time = ai_time
            
            # User message
            markdown_lines.append(f"### Exchange {idx}")
            markdown_lines.append("")
            markdown_lines.append(f"**You** ({formatted_user_time})")
            markdown_lines.append("")
            # Indent user message for better readability
            user_lines = user_message.split('\n')
            for line in user_lines:
                markdown_lines.append(f"> {line}")
            markdown_lines.append("")
            
            # AI message
            markdown_lines.append(f"**ArchPal** ({formatted_ai_time})")
            markdown_lines.append("")
            # Format AI message with proper line breaks
            ai_lines = ai_message.split('\n')
            for line in ai_lines:
                markdown_lines.append(line)
            markdown_lines.append("")
            markdown_lines.append("---")
            markdown_lines.append("")
    
    # Footer
    markdown_lines.append("")
    markdown_lines.append("---")
    markdown_lines.append("")
    markdown_lines.append("*This conversation was exported from ArchPal, UGA's AI Writing Coach.*")
    markdown_lines.append(f"*Generated on {current_date}*")
    
    return "\n".join(markdown_lines)


# --- Export Workflow ---

def handle_export(student_info, message_log):
    """
    Generate markdown-formatted conversation history for printing
    
    Note: Conversations are automatically saved to S3 during chat.
    This function generates a printable markdown document.
    
    Args:
        student_info: Dictionary with student information
        message_log: List of message dictionaries
    
    Returns:
        True if export generation successful, False otherwise
    """
    
    unique_id = student_info["unique_id"]
    course_number = student_info.get("course_number", "")
    
    try:
        # Generate markdown conversation history
        markdown_content = create_markdown_conversation(student_info, message_log)
        
        # Store markdown in session state for download/display
        # Use course number in filename if available, otherwise use unique_id
        filename_course = course_number.replace(" ", "_") if course_number else unique_id[:8]
        st.session_state["export_markdown"] = markdown_content
        st.session_state["export_markdown_filename"] = f"ArchPal_Conversation_{filename_course}.md"
        
        return True
        
    except Exception as e:
        st.error(f"Export Error: {e}")
        return False
