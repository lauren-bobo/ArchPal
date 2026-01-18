import streamlit as st
import io
import csv
import dropbox
from datetime import datetime

# --- Constants & Config ---

def get_secrets():
    """Get secrets from Streamlit session"""
    return st.secrets

def get_dropbox_client():
    """Get or create cached Dropbox client"""
    if "dropbox_client" not in st.session_state or st.session_state["dropbox_client"] is None:
        secrets = get_secrets()
        if "dropbox_access_token" in secrets:
            dropbox_token = secrets["dropbox_access_token"]
            st.session_state["dropbox_client"] = dropbox.Dropbox(dropbox_token)
    return st.session_state.get("dropbox_client")

def build_dropbox_path(folder_key, filename):
    """Build a properly formatted Dropbox path from folder key and filename"""
    secrets = get_secrets()
    folder_path = secrets.get(folder_key, '')
    if folder_path and not folder_path.startswith('/'):
        folder_path = '/' + folder_path
    if folder_path and not folder_path.endswith('/'):
        folder_path = folder_path + '/'
    return f"{folder_path}{filename}"

def upload_to_dropbox(csv_data, filepath):
    """Upload CSV data to Dropbox at the specified filepath"""
    dbx = get_dropbox_client()
    if not dbx:
        raise ValueError("Dropbox client not initialized. Check secrets.")
        
    csv_bytes = csv_data.encode('utf-8')
    dbx.files_upload(csv_bytes, filepath, mode=dropbox.files.WriteMode.overwrite)

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

# --- Export Workflow ---

def handle_export(student_info, message_log):
    """Orchestrate the export process"""
    
    unique_id = student_info["unique_id"]
    first_name = student_info["first_name"]
    last_name = student_info["last_name"]
    college_year = student_info["college_year"]
    major = student_info["major"]
    session_number = student_info["session_number"]
    
    try:
        # Upload anonymized conversation data
        csv_anonymized = create_csv_data(
            message_log,
            unique_id,
            college_year,
            major,
            first_name,
            anonymize=True
        )
        filename_anonymized = f"{unique_id}_Session{session_number}.csv"
        path_anonymized = build_dropbox_path('dropbox_folder_path1', filename_anonymized)
        upload_to_dropbox(csv_anonymized, path_anonymized)
        
        # Upload identifier CSV
        csv_identifier = create_identifier_csv(first_name, last_name, unique_id)
        filename_identifier = f"{unique_id}_identifier.csv"
        path_identifier = build_dropbox_path('dropbox_folder_path2', filename_identifier)
        upload_to_dropbox(csv_identifier, path_identifier)
        
        return True
        
    except Exception as e:
        print(f"Export Error: {e}")
        return False
