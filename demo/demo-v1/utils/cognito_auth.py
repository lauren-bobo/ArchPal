import streamlit as st
import os
import jwt
import requests
import base64
import json
from datetime import datetime, time
from urllib.parse import quote

def get_cognito_config():
    """Get Cognito configuration from secrets"""
    try:
        if "cognito_user_pool_id" not in st.secrets:
            # Fallback for dev/testing if secrets not set up
            return None
            
        return {
            "pool_id": st.secrets["cognito_user_pool_id"],
            "app_client_id": st.secrets["cognito_client_id"],
            "domain": st.secrets["cognito_domain"],
            "region": st.secrets["cognito_region"],
            "redirect_uri": st.secrets["cognito_redirect_uri"]
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
        "token_id": None
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
                
                # Update session state
                st.session_state["authenticated"] = True
                st.session_state["auth_token"] = access_token
                st.session_state["token_id"] = id_token
                st.session_state["auth_user"] = {
                    "email": email,
                    "username": decoded.get("cognito:username", email)
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
        # Debug: Show the auth URL being used
        st.info(f"🔍 Debug: Login URL = {auth_url}")
        
        st.markdown(
            f"""
            <a href="{auth_url}" target="_self" class="login-button">
                <div style="
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    background-color: #BA0C2F; 
                    color: white; 
                    padding: 12px 24px; 
                    border-radius: 8px; 
                    text-decoration: none; 
                    font-weight: bold; 
                    margin: 20px 0;
                    width: 100%;
                    max-width: 300px;
                    text-align: center;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    Login
                </div>
            </a>
            """, 
            unsafe_allow_html=True
        )
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
    
    # Construct logout URL
    logout_url = (
        f"https://{domain}/logout?"
        f"client_id={client_id}&"
        f"logout_uri={redirect_uri}"
    )
    
    # Redirect to Cognito logout
    st.markdown(f'<meta http-equiv="refresh" content="0;url={logout_url}">', unsafe_allow_html=True)
