"""
S3 Storage Utility Module for ArchPal

This module handles all S3 operations for storing and retrieving:
- User information
- Conversation history
- Individual conversation data

Storage Structure:
s3://bucket-name/
├── users/
│   ├── {cognito_user_id}/
│   │   ├── info.json
│   │   ├── conversations.json
│   │   └── conversations/
│   │       ├── {conversation_id}.json
│   │       └── {conversation_id}.json

AWS Configuration Required:
- s3_bucket_name: Name of your S3 bucket (set in secrets.toml)
- s3_region: AWS region where bucket is located (set in secrets.toml)
- aws_access_key_id: AWS access key (set in secrets.toml)
- aws_secret_access_key: AWS secret key (set in secrets.toml)
"""

import streamlit as st
import boto3
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from botocore.exceptions import ClientError, NoCredentialsError


def get_s3_config():
    """Get S3 configuration from secrets"""
    try:
        secrets = st.secrets
        return {
            "bucket_name": secrets.get("s3_bucket_name"),
            "region": secrets.get("s3_region", "us-east-1"),
            "access_key_id": secrets.get("aws_access_key_id"),
            "secret_access_key": secrets.get("aws_secret_access_key")
        }
    except Exception as e:
        st.error(f"Error loading S3 configuration: {str(e)}")
        return None


def get_s3_client():
    """Get or create cached S3 client"""
    if "s3_client" not in st.session_state or st.session_state["s3_client"] is None:
        config = get_s3_config()
        if not config or not config["bucket_name"]:
            return None
        
        try:
            # Create S3 client with credentials from secrets
            # If access keys are not provided, boto3 will use IAM role (for EC2/ECS/Lambda)
            s3_client = boto3.client(
                's3',
                region_name=config["region"],
                aws_access_key_id=config.get("access_key_id") or None,
                aws_secret_access_key=config.get("secret_access_key") or None
            )
            st.session_state["s3_client"] = s3_client
            return s3_client
        except NoCredentialsError:
            st.error("AWS credentials not found. Please configure in secrets.toml")
            return None
        except Exception as e:
            st.error(f"Error creating S3 client: {str(e)}")
            return None
    
    return st.session_state.get("s3_client")


def build_s3_path(*parts):
    """Build S3 object path from parts"""
    # Filter out None values and join with /
    filtered_parts = [str(p) for p in parts if p is not None]
    return "/".join(filtered_parts)


# ============================================
# User Info Operations
# ============================================

def get_user_info(cognito_user_id: str) -> Optional[Dict]:
    """
    Retrieve user info from S3
    
    Args:
        cognito_user_id: Cognito user ID (sub claim)
    
    Returns:
        User info dict or None if not found
    """
    s3_client = get_s3_client()
    if not s3_client:
        return None
    
    config = get_s3_config()
    if not config:
        return None
    
    key = build_s3_path("users", cognito_user_id, "info.json")
    
    try:
        response = s3_client.get_object(Bucket=config["bucket_name"], Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'NoSuchKey':
            # User info doesn't exist yet - this is normal for new users
            return None
        else:
            st.error(f"Error retrieving user info from S3: {str(e)}")
            return None
    except Exception as e:
        st.error(f"Unexpected error retrieving user info: {str(e)}")
        return None


def save_user_info(cognito_user_id: str, user_info: Dict) -> bool:
    """
    Save user info to S3
    
    Args:
        cognito_user_id: Cognito user ID (sub claim)
        user_info: User info dictionary
    
    Returns:
        True if successful, False otherwise
    """
    s3_client = get_s3_client()
    if not s3_client:
        return False
    
    config = get_s3_config()
    if not config:
        return False
    
    # Add/update timestamps
    now = datetime.utcnow().isoformat() + "Z"
    if "created_at" not in user_info:
        user_info["created_at"] = now
    user_info["updated_at"] = now
    user_info["cognito_user_id"] = cognito_user_id
    
    key = build_s3_path("users", cognito_user_id, "info.json")
    
    try:
        json_data = json.dumps(user_info, indent=2)
        s3_client.put_object(
            Bucket=config["bucket_name"],
            Key=key,
            Body=json_data.encode('utf-8'),
            ContentType='application/json'
        )
        return True
    except Exception as e:
        st.error(f"Error saving user info to S3: {str(e)}")
        return False


# ============================================
# Conversation History Operations
# ============================================

def get_conversation_history(cognito_user_id: str, limit: int = 5) -> List[Dict]:
    """
    Retrieve conversation history for a user
    
    Args:
        cognito_user_id: Cognito user ID (sub claim)
        limit: Maximum number of conversations to return (default: 5)
    
    Returns:
        List of conversation metadata dicts, sorted by last_updated (newest first)
    """
    s3_client = get_s3_client()
    if not s3_client:
        return []
    
    config = get_s3_config()
    if not config:
        return []
    
    key = build_s3_path("users", cognito_user_id, "conversations.json")
    
    try:
        response = s3_client.get_object(Bucket=config["bucket_name"], Key=key)
        content = response['Body'].read().decode('utf-8')
        conversations = json.loads(content)
        
        # Sort by last_updated (newest first) and limit
        sorted_conversations = sorted(
            conversations,
            key=lambda x: x.get("last_updated", ""),
            reverse=True
        )
        return sorted_conversations[:limit]
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'NoSuchKey':
            # No conversations yet - this is normal for new users
            return []
        else:
            st.error(f"Error retrieving conversation history: {str(e)}")
            return []
    except Exception as e:
        st.error(f"Unexpected error retrieving conversation history: {str(e)}")
        return []


def add_conversation_to_history(cognito_user_id: str, conversation_id: str, title: Optional[str] = None) -> bool:
    """
    Add a new conversation to the history
    
    Args:
        cognito_user_id: Cognito user ID (sub claim)
        conversation_id: Unique conversation ID
        title: Optional conversation title
    
    Returns:
        True if successful, False otherwise
    """
    s3_client = get_s3_client()
    if not s3_client:
        return False
    
    config = get_s3_config()
    if not config:
        return False
    
    key = build_s3_path("users", cognito_user_id, "conversations.json")
    
    try:
        # Try to get existing conversations
        try:
            response = s3_client.get_object(Bucket=config["bucket_name"], Key=key)
            content = response['Body'].read().decode('utf-8')
            conversations = json.loads(content)
        except ClientError as e:
            if e.response.get('Error', {}).get('Code', '') == 'NoSuchKey':
                conversations = []
            else:
                raise
        
        # Check if conversation already exists
        existing_ids = [c.get("conversation_id") for c in conversations]
        if conversation_id in existing_ids:
            # Conversation already exists, update it
            for conv in conversations:
                if conv.get("conversation_id") == conversation_id:
                    conv["last_updated"] = datetime.utcnow().isoformat() + "Z"
                    break
        else:
            # Add new conversation
            now = datetime.utcnow().isoformat() + "Z"
            conversations.append({
                "conversation_id": conversation_id,
                "created_at": now,
                "last_updated": now,
                "message_count": 0,
                "title": title or f"Conversation {len(conversations) + 1}"
            })
        
        # Save back to S3
        json_data = json.dumps(conversations, indent=2)
        s3_client.put_object(
            Bucket=config["bucket_name"],
            Key=key,
            Body=json_data.encode('utf-8'),
            ContentType='application/json'
        )
        return True
    except Exception as e:
        st.error(f"Error updating conversation history: {str(e)}")
        return False


def update_conversation_metadata(cognito_user_id: str, conversation_id: str, message_count: int) -> bool:
    """
    Update conversation metadata (message count, last updated)
    
    Args:
        cognito_user_id: Cognito user ID (sub claim)
        conversation_id: Conversation ID to update
        message_count: New message count
    
    Returns:
        True if successful, False otherwise
    """
    s3_client = get_s3_client()
    if not s3_client:
        return False
    
    config = get_s3_config()
    if not config:
        return False
    
    key = build_s3_path("users", cognito_user_id, "conversations.json")
    
    try:
        # Get existing conversations
        try:
            response = s3_client.get_object(Bucket=config["bucket_name"], Key=key)
            content = response['Body'].read().decode('utf-8')
            conversations = json.loads(content)
        except ClientError as e:
            if e.response.get('Error', {}).get('Code', '') == 'NoSuchKey':
                return False
            else:
                raise
        
        # Update conversation metadata
        updated = False
        for conv in conversations:
            if conv.get("conversation_id") == conversation_id:
                conv["message_count"] = message_count
                conv["last_updated"] = datetime.utcnow().isoformat() + "Z"
                updated = True
                break
        
        if not updated:
            return False
        
        # Save back to S3
        json_data = json.dumps(conversations, indent=2)
        s3_client.put_object(
            Bucket=config["bucket_name"],
            Key=key,
            Body=json_data.encode('utf-8'),
            ContentType='application/json'
        )
        return True
    except Exception as e:
        st.error(f"Error updating conversation metadata: {str(e)}")
        return False


# ============================================
# Conversation Data Operations
# ============================================

def get_conversation(cognito_user_id: str, conversation_id: str) -> Optional[Dict]:
    """
    Retrieve a specific conversation
    
    Args:
        cognito_user_id: Cognito user ID (sub claim)
        conversation_id: Conversation ID
    
    Returns:
        Conversation dict or None if not found
    """
    s3_client = get_s3_client()
    if not s3_client:
        return None
    
    config = get_s3_config()
    if not config:
        return None
    
    key = build_s3_path("users", cognito_user_id, "conversations", f"{conversation_id}.json")
    
    try:
        response = s3_client.get_object(Bucket=config["bucket_name"], Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        if error_code == 'NoSuchKey':
            return None
        else:
            st.error(f"Error retrieving conversation: {str(e)}")
            return None
    except Exception as e:
        st.error(f"Unexpected error retrieving conversation: {str(e)}")
        return None


def save_conversation(cognito_user_id: str, conversation_id: str, conversation_data: Dict) -> bool:
    """
    Save a conversation to S3
    
    Args:
        cognito_user_id: Cognito user ID (sub claim)
        conversation_id: Conversation ID
        conversation_data: Full conversation data dict
    
    Returns:
        True if successful, False otherwise
    """
    s3_client = get_s3_client()
    if not s3_client:
        return False
    
    config = get_s3_config()
    if not config:
        return False
    
    # Ensure conversation has required fields
    conversation_data["conversation_id"] = conversation_id
    conversation_data["user_id"] = cognito_user_id
    if "created_at" not in conversation_data:
        conversation_data["created_at"] = datetime.utcnow().isoformat() + "Z"
    conversation_data["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    key = build_s3_path("users", cognito_user_id, "conversations", f"{conversation_id}.json")
    
    try:
        json_data = json.dumps(conversation_data, indent=2)
        s3_client.put_object(
            Bucket=config["bucket_name"],
            Key=key,
            Body=json_data.encode('utf-8'),
            ContentType='application/json'
        )
        return True
    except Exception as e:
        st.error(f"Error saving conversation to S3: {str(e)}")
        return False


def append_message_to_conversation(
    cognito_user_id: str,
    conversation_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict] = None
) -> bool:
    """
    Append a message to an existing conversation
    
    Args:
        cognito_user_id: Cognito user ID (sub claim)
        conversation_id: Conversation ID
        role: Message role ('user' or 'assistant')
        content: Message content
        metadata: Optional metadata dict
    
    Returns:
        True if successful, False otherwise
    """
    # Get existing conversation
    conversation = get_conversation(cognito_user_id, conversation_id)
    
    if conversation is None:
        # Create new conversation
        conversation = {
            "conversation_id": conversation_id,
            "user_id": cognito_user_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "messages": [],
            "metadata": {}
        }
    
    # Ensure messages list exists
    if "messages" not in conversation:
        conversation["messages"] = []
    
    # Create new message
    message_id = str(uuid.uuid4())
    message = {
        "message_id": message_id,
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "metadata": metadata or {}
    }
    message["metadata"]["message_index"] = len(conversation["messages"])
    
    # Append message
    conversation["messages"].append(message)
    
    # Update last_updated
    conversation["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    # Save conversation
    success = save_conversation(cognito_user_id, conversation_id, conversation)
    
    # Update conversation history metadata
    if success:
        update_conversation_metadata(cognito_user_id, conversation_id, len(conversation["messages"]))
    
    return success
