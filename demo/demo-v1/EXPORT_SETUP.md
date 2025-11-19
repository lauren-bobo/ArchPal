# Secrets Configuration Guide

## Overview

The ArchPal application uses Streamlit secrets to securely store sensitive configuration without committing credentials to the GitHub repository. Two types of secrets are configured:

1. **Anthropic API Key** (required) - Used for the chatbot functionality
2. **Dropbox API Credentials** (required) - Used for automatic CSV export to Dropbox

## Quick Start

**For Local Development:**
1. Create `.streamlit/secrets.toml` in your project root
2. Add your secrets (see Dropbox setup below)
3. Copy from `.streamlit/secrets.toml.example` if needed

**For Streamlit Cloud:**
1. Set up Dropbox API (see detailed instructions below)
2. Go to your app → Settings → Secrets
3. Paste your secrets in TOML format
4. Save and redeploy

## Dropbox API Setup

### Step 1: Create Dropbox App

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Click "Create app"
3. Choose "Scoped access" (recommended for new apps)
4. Select "App folder" (files will be stored in a dedicated folder) or "Full Dropbox" (access to entire Dropbox)
5. Name your app (e.g., "ArchPal Exporter")
6. Click "Create app"

### Step 2: Configure App Permissions

1. In your app settings, go to the "Permissions" tab
2. Enable the following permissions:
   - `files.content.write` - for uploading files
   - `files.metadata.write` - for file metadata operations
3. Click "Submit" to save permissions

### Step 3: Generate Access Token

1. Go to the "Settings" tab in your app
2. Under "OAuth 2", click "Generate access token"
3. Copy the generated token (keep it secure!)

**Important:** This generates a long-lived access token. In production, consider using refresh tokens for better security.

### Step 4: Set Up Dropbox Folder (Optional)

If you want to upload files to a specific folder instead of the app folder:

1. Create a folder in your Dropbox (e.g., "ArchPal Exports")
2. Note the folder path (e.g., "/ArchPal Exports" - must start with `/`)

### Step 5: Configure Secrets

#### For Local Development:

1. **Create the secrets file:**
   - In your project root directory (same level as `app.py`), create a folder named `.streamlit`
   - Inside `.streamlit`, create a file named `secrets.toml`

2. **Add your secrets:**
   ```toml
   # Anthropic API Key
   anthropic_api_key = "sk-ant-your-api-key-here"

   # Dropbox Access Token
   dropbox_access_token = "your-dropbox-access-token-here"

   # Dropbox Folder Path (optional - if not provided, files go to app folder)
   dropbox_folder_path = "/ArchPal Exports"
   ```

#### For Streamlit Cloud:

1. **Deploy your app** to Streamlit Community Cloud (connect your GitHub repository)

2. **Add secrets via the web interface:**
   - Go to your app on [share.streamlit.io](https://share.streamlit.io)
   - Click the **"⋮"** (three dots) menu in the top right
   - Select **"Settings"**
   - Click on **"Secrets"** in the left sidebar
   - Paste your secrets in TOML format (same format as above)
   - Click **"Save"**

3. **Redeploy your app** (secrets are applied automatically on next deployment)

**Important:** Secrets added via the Streamlit Cloud interface are encrypted and stored securely. They are never exposed in your repository or logs.

## CSV Format

The exported CSV includes the following columns:

- `Unique Identifier`: UUID assigned to the student session
- `userMessage`: The student's message
- `userMessageTime`: When the student message was sent (YYYY-MM-DD HH:MM:SS)
- `AIMessage`: ArchPal's response
- `AIMessageTime`: When ArchPal's response was sent (YYYY-MM-DD HH:MM:SS)

## File Naming

Files are automatically named with the format:
```
{last_name}_{first_name}_Session{session_number}.csv
```

Example: `Doe_John_Session001.csv`

## Testing

To test the export feature:

1. Fill out the startup form with student information
2. Have a conversation with ArchPal
3. Click the "Export Chat" button
4. Verify:
   - CSV downloads correctly
   - File appears in your Dropbox folder (if configured)
   - Success message shows (files are uploaded silently)

## Troubleshooting

### Error: "Missing Dropbox configuration in secrets"
- Make sure `dropbox_access_token` is configured in your secrets
- Verify the token is valid and not expired

### Error: "Could not upload to Dropbox"
- Check that your access token is valid
- Verify the Dropbox API app has the correct permissions (`files.content.write`)
- Check that the folder path exists (if using `dropbox_folder_path`)

### Files not appearing in folder
- Verify the folder path is correct (must start with `/`)
- Make sure the folder exists in your Dropbox
- Check that your app has access to the specified folder

### Access token issues
- Access tokens can expire - generate a new one from your Dropbox app console
- Make sure you're using the correct token for the correct app
- For production apps, consider implementing OAuth 2.0 with refresh tokens
