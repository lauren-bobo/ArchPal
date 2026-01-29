import streamlit as st
import io
import csv
from datetime import datetime
from fpdf import FPDF

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

# --- PDF Generation ---

def create_pdf_conversation(student_info, message_log):
    """
    Create a PDF-formatted conversation history
    
    Args:
        student_info: Dictionary with student information
        message_log: List of message dictionaries with userMessage, AIMessage, and timestamps
    
    Returns:
        PDF bytes ready for download
    """
    first_name = student_info.get("first_name", "")
    last_name = student_info.get("last_name", "")
    college_year = student_info.get("college_year", "")
    major = student_info.get("major", "")
    course_number = student_info.get("course_number", "")
    
    # Format current date/time for header
    current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    
    # Create PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(139, 0, 0)  # Dark red (UGA colors)
    pdf.cell(0, 15, "ArchPal Conversation History", ln=True, align="C")
    
    # Subtitle
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "UGA's AI Writing Coach", ln=True, align="C")
    
    # Divider line
    pdf.set_draw_color(139, 0, 0)
    pdf.line(20, pdf.get_y() + 2, 190, pdf.get_y() + 2)
    pdf.ln(10)
    
    # Student Information Section
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Student Information", ln=True)
    
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Name: {first_name} {last_name}", ln=True)
    pdf.cell(0, 7, f"College Year: {college_year}", ln=True)
    pdf.cell(0, 7, f"Major: {major}", ln=True)
    pdf.cell(0, 7, f"Course Number: {course_number}", ln=True)
    pdf.cell(0, 7, f"Export Date: {current_date}", ln=True)
    
    pdf.ln(5)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(8)
    
    # Conversation Section
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Conversation", ln=True)
    
    if not message_log:
        pdf.set_font("Helvetica", "I", 11)
        pdf.cell(0, 10, "No messages in this conversation.", ln=True)
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
            
            # Exchange header
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 10, f"Exchange {idx}", ln=True)
            
            # User message
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(0, 100, 0)  # Dark green for user
            pdf.cell(0, 7, f"You ({formatted_user_time})", ln=True)
            
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(0, 0, 0)
            # Handle multi-line user message
            pdf.multi_cell(0, 6, user_message.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(3)
            
            # AI message
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(139, 0, 0)  # Dark red for ArchPal
            pdf.cell(0, 7, f"ArchPal ({formatted_ai_time})", ln=True)
            
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(0, 0, 0)
            # Handle multi-line AI message
            pdf.multi_cell(0, 6, ai_message.encode('latin-1', 'replace').decode('latin-1'))
            pdf.ln(5)
            
            # Divider between exchanges
            if idx < len(message_log):
                pdf.set_draw_color(200, 200, 200)
                pdf.line(30, pdf.get_y(), 180, pdf.get_y())
                pdf.ln(5)
    
    # Footer
    pdf.ln(10)
    pdf.set_draw_color(139, 0, 0)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "This conversation was exported from ArchPal, UGA's AI Writing Coach.", ln=True, align="C")
    pdf.cell(0, 6, f"Generated on {current_date}", ln=True, align="C")
    
    # Return PDF as bytes (convert from bytearray for Streamlit compatibility)
    return bytes(pdf.output())



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
    Generate PDF and markdown-formatted conversation history for download/print
    
    Note: Conversations are automatically saved to S3 during chat.
    This function generates downloadable PDF and printable markdown.
    
    Args:
        student_info: Dictionary with student information
        message_log: List of message dictionaries
    
    Returns:
        True if export generation successful, False otherwise
    """
    
    unique_id = student_info["unique_id"]
    course_number = student_info.get("course_number", "")
    
    try:
        # Use course number in filename if available, otherwise use unique_id
        filename_course = course_number.replace(" ", "_") if course_number else unique_id[:8]
        
        # Generate PDF conversation history
        pdf_content = create_pdf_conversation(student_info, message_log)
        st.session_state["export_pdf"] = pdf_content
        st.session_state["export_pdf_filename"] = f"ArchPal_Conversation_{filename_course}.pdf"
        
        # Generate markdown conversation history (for preview)
        markdown_content = create_markdown_conversation(student_info, message_log)
        st.session_state["export_markdown"] = markdown_content
        st.session_state["export_markdown_filename"] = f"ArchPal_Conversation_{filename_course}.md"
        
        return True
        
    except Exception as e:
        st.error(f"Export Error: {e}")
        return False
