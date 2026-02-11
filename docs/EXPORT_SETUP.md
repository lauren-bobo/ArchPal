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

### Step 4: Set Up Dropbox Folders

The application exports two types of files to separate folders:

1. **Anonymized Conversation Data** - Full conversation with names replaced by `[NAME]`
2. **Identifier Data** - Single row CSV with first name, last name, and unique identifier

Create two folders in your Dropbox:
- One for anonymized conversations (e.g., "/ArchPal User Sessions Anonymous Exports")
- One for identifier files (e.g., "/ArchPal User Sessions Identifiers")

Note the folder paths (must start with `/`)

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

   # Dropbox Folder Paths (required)
   # Folder 1: Anonymized conversation data (names replaced with [NAME])
   dropbox_folder_path1 = "/ArchPal User Sessions Anonymous Exports"
   
   # Folder 2: Identifier files (first_name, last_name, unique_id)
   dropbox_folder_path2 = "/ArchPal User Sessions Identifiers"
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

## CSV Export Format

The application exports **two separate CSV files** for each session:

### 1. Anonymized Conversation CSV (Folder 1)

This file contains the full conversation with student names replaced by `[NAME]` for privacy. It includes the following columns:

- `Unique Identifier`: UUID assigned to the student session
- `College Year`: Student's college year level
- `Major`: Student's major
- `userMessage`: The student's message (with names anonymized)
- `userMessageTime`: When the student message was sent (YYYY-MM-DD HH:MM:SS)
- `AIMessage`: ArchPal's response (with names anonymized)
- `AIMessageTime`: When ArchPal's response was sent (YYYY-MM-DD HH:MM:SS)

**File naming format:**
```
{unique_id}_Session{session_number}.csv
```

Example: `a1b2c3d4-e5f6-7890-abcd-ef1234567890_Session1.csv`

### 2. Identifier CSV (Folder 2)

This file contains a single row with identifying information for matching purposes. It includes the following columns:

- `first_name`: Student's first name
- `last_name`: Student's last name
- `unique_id`: UUID assigned to the student session (matches the conversation file)

**File naming format:**
```
{unique_id}_identifier.csv
```

Example: `a1b2c3d4-e5f6-7890-abcd-ef1234567890_identifier.csv`

**Note:** Both files share the same `unique_id`, allowing them to be matched while keeping conversation data anonymized.

## Testing

To test the export feature:

1. Fill out the startup form with student information
2. Have a conversation with ArchPal
3. Click the "Export Chat" button
4. Review and accept the consent form
5. Verify:
   - Success message appears
   - Two CSV files are uploaded to Dropbox:
     - Anonymized conversation file in `dropbox_folder_path1`
     - Identifier file in `dropbox_folder_path2`
   - Both files share the same `unique_id` for matching

## Troubleshooting

### Error: "Missing Dropbox configuration in secrets"
- Make sure `dropbox_access_token` is configured in your secrets
- Verify the token is valid and not expired

### Error: "Could not upload to Dropbox"
- Check that your access token is valid
- Verify the Dropbox API app has the correct permissions (`files.content.write`)
- Check that both folder paths exist (`dropbox_folder_path1` and `dropbox_folder_path2`)

### Files not appearing in folders
- Verify both folder paths are correct (must start with `/`)
- Make sure both folders exist in your Dropbox
- Check that your app has access to both specified folders
- Verify that both `dropbox_folder_path1` and `dropbox_folder_path2` are configured in secrets

### Access token issues
- Access tokens can expire - generate a new one from your Dropbox app console
- Make sure you're using the correct token for the correct app
- For production apps, consider implementing OAuth 2.0 with refresh tokens
