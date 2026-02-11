# AWS Cognito Authentication Setup

This guide explains how to configure AWS Cognito authentication for the ArchPal Streamlit application.

## Prerequisites

- AWS Account with Cognito User Pool configured
- Streamlit application running (locally or deployed)

## Configuration Steps

### 1. Configure User Pool Client

In your AWS Cognito Console:

1.  Go to your User Pool (`rzpit2` / `us-east-1_pMMn1UjGk`)
2.  Navigate to **App integration** -> **App clients**
3.  Select or create a user pool client
4.  Configure **Hosted UI**:
    *   **Allowed callback URLs**: 
        *   `http://localhost:8501/` (for local development)
        *   `https://<your-app>.streamlit.app/` (for production)
    *   **Allowed sign-out URLs**:
        *   Same as callback URLs
    *   **OAuth 2.0 grant types**: Authorization code grant
    *   **OpenID Connect scopes**: `email`, `openid`, `profile`

### 2. Configure Streamlit Secrets

Create or update `.streamlit/secrets.toml` in the `demo/demo-v1/` directory:

```toml
[cognito]
user_pool_id = "us-east-1_pMMn1UjGk"
client_id = "<your-client-id>"
domain = "rzpit2.auth.us-east-1.amazoncognito.com"
region = "us-east-1"
redirect_uri = "http://localhost:8501"  # Update for production

# Other existing secrets...
anthropic_api_key = "..."
dropbox_access_token = "..."
# ...
```

### 3. Run the Application

```bash
streamlit run app.py
```

## How It Works

1.  App checks for existing session token
2.  If valid, user is authenticated
3.  If invalid/missing, user is shown "Login with Cognito" button
4.  User authenticates via AWS Cognito Hosted UI
    *   Validates `@uga.edu` email (via Lambda trigger)
5.  Cognito redirects back to Streamlit with auth code
6.  App exchanges code for tokens and establishes session
