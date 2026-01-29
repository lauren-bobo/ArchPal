import streamlit as st
import os
import jwt
import requests
import base64
import json
import toml
from datetime import datetime, time
from urllib.parse import quote

# Cache for secrets loaded from parent directory
_parent_secrets = None

def _load_parent_secrets():
    """Load secrets from parent .streamlit directory if available"""
    global _parent_secrets
    if _parent_secrets is not None:
        return _parent_secrets
    
    # Try parent directories for .streamlit/secrets.toml
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):  # Check up to 5 levels up
        parent_dir = os.path.dirname(current_dir)
        secrets_path = os.path.join(parent_dir, ".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            try:
                _parent_secrets = toml.load(secrets_path)
                return _parent_secrets
            except Exception:
                pass
        current_dir = parent_dir
    
    _parent_secrets = {}
    return _parent_secrets

def _get_secret(key, default=None):
    """Get secret from st.secrets or parent directory secrets"""
    try:
        return st.secrets[key]
    except Exception:
        parent_secrets = _load_parent_secrets()
        return parent_secrets.get(key, default)

def get_cognito_config():
    """Get Cognito configuration from secrets"""
    try:
        pool_id = _get_secret("cognito_user_pool_id")
        if not pool_id:
            return None
            
        return {
            "pool_id": pool_id,
            "app_client_id": _get_secret("cognito_client_id"),
            "domain": _get_secret("cognito_domain"),
            "region": _get_secret("cognito_region"),
            "redirect_uri": _get_secret("cognito_redirect_uri")
        }
    except Exception as e:
        st.error(f"Error loading Cognito configuration: {str(e)}")
        return None

def get_jwks_url(region, pool_id):
    """Get JWKS URL for token verification"""
    return f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"

def init_auth_state():
    """Initialize authentication state in session"""
    defaults = {
        "authenticated": False,
        "auth_token": None,
        "auth_user": None,
        "token_id": None,
        "cognito_user_id": None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def login():
    """Handle Cognito Login Flow"""
    config = get_cognito_config()
    if not config:
        st.warning("Cognito configuration not found in .streamlit/secrets.toml")
        return False
        
    client_id = config["app_client_id"]
    domain = config["domain"]
    redirect_uri = config["redirect_uri"]
    
    # Construct Cognito Hosted UI URL
    # Using 'code' response type for Authorization Code Grant
    auth_url = (
        f"https://{domain}/login?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"scope=email+openid+profile&"
        f"redirect_uri={quote(redirect_uri, safe='')}"
    )
    
    # Check for auth code in query params (callback)
    query_params = st.query_params
    code = query_params.get("code")
    
    if code:
        # Exchange code for tokens
        try:
            token_url = f"https://{domain}/oauth2/token"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "grant_type": "authorization_code",
                "client_id": client_id,
                "code": code,
                "redirect_uri": redirect_uri
            }
            
            response = requests.post(token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                tokens = response.json()
                id_token = tokens.get("id_token")
                access_token = tokens.get("access_token")
                
                # Verify and decode ID token
                # In production, you would fetch JWKS and verify signature
                # For this demo, we'll optimistically decode unverified for user info
                # verifying audience and issuer
                
                # Simple decode to get payload
                decoded = jwt.decode(id_token, options={"verify_signature": False})
                
                email = decoded.get("email")
                
                # Check for UGA email
                if email and not email.lower().endswith("@uga.edu"):
                    st.error("Only @uga.edu email addresses are allowed.")
                    return False
                
                # Extract Cognito user ID (sub claim) - this is the permanent unique identifier
                # The 'sub' claim is a UUID that uniquely identifies the user in Cognito
                cognito_user_id = decoded.get("sub")
                
                # Update session state
                st.session_state["authenticated"] = True
                st.session_state["auth_token"] = access_token
                st.session_state["token_id"] = id_token
                st.session_state["cognito_user_id"] = cognito_user_id
                st.session_state["auth_user"] = {
                    "email": email,
                    "username": decoded.get("cognito:username", email),
                    "cognito_user_id": cognito_user_id
                }
                
                # Clear query params to hide code
                st.query_params.clear()
                st.rerun()
                return True
            else:
                st.error(f"❌ Failed to authenticate with Cognito")
                st.error(f"Status: {response.status_code}")
                try:
                    error_data = response.json()
                    st.error(f"Error: {error_data.get('error', 'Unknown')}")
                    st.error(f"Description: {error_data.get('error_description', 'No description')}")
                except:
                    st.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            st.error(f"❌ Authentication error: {str(e)}")
            st.info(f"Redirect URI configured: {redirect_uri}")
            st.info(f"Cognito domain: {domain}")
            return False
            
    # If not authenticated and no code, show login button
    if not st.session_state.get("authenticated", False):
        # Welcome text
        st.markdown("## Welcome")
        st.markdown("**ArchPal** is an AI companion designed at UGA to support you as a writer, learner, and thinker.")
        st.markdown("""
- A partner to talk through ideas before and as you write
- A tool to help you revise, reorganize, and reflect
- A low-stakes partner available anytime
- A way to practice explaining your thinking
- A resource to help you access other support at UGA and online
""")
        st.markdown("*You'll be redirected to a secure login screen.*")

        # Login button
        st.link_button(
            "🔑 Login with UGA Email",
            auth_url,
            type="primary",
            use_container_width=True
        )

        st.markdown("---")
        st.markdown("### Quick tips")
        st.markdown("""
- Share the assignment prompt and rubric with ArchPal.
- When getting started, ask for a plan to help you manage a writing project.
- Later on, ask for revision priorities and a checklist to guide your work.
""")
        
        return False
        
    return True

def logout():
    """Handle Logout"""
    config = get_cognito_config()
    if not config:
        return
        
    domain = config["domain"]
    client_id = config["app_client_id"]
    redirect_uri = config["redirect_uri"]
    
    # Clear session state
    keys_to_clear = ["authenticated", "auth_token", "auth_user", "token_id", "student_info", "messages", "message_log"]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
            
    # clear all query params
    st.query_params.clear()
    
    # Construct logout URL with proper URL encoding
    logout_url = (
        f"https://{domain}/logout?"
        f"client_id={client_id}&"
        f"logout_uri={quote(redirect_uri, safe='')}"
    )
    
    # Use JavaScript window.location for redirect (more reliable than meta refresh)
    st.markdown(
        f"""
        <script>
            window.location.href = "{logout_url}";
        </script>
        """,
        unsafe_allow_html=True
    )
    st.rerun()
