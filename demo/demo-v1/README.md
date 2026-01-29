# ArchPal AI Companion Demo v1

A Streamlit application that provides a chat interface with Anthropic Claude via LangChain, designed for research demos with student interaction tracking and privacy-preserving data export.

## Features

- **Secure Authentication**: Integrated with AWS Cognito for secure login (only @uga.edu emails allowed).
- **Persistent Storage**: User profiles and conversation history stored in AWS S3 for seamless session continuity.
- **Conversation Management**: Load previous conversations from history or start new ones at any time.
- **Startup Form**: Collects student information context for the AI coach (auto-populated for returning users).
- **Chat Interface**: Powered by Anthropic Claude via AWS Bedrock with customizable system prompts.
- **Message Logging**: Tracks all messages with timestamps for the duration of the session.
- **Admin Controls**: Admin panel for customizing system prompts and role settings.
- **Dual CSV Export**: Exports anonymized conversation data and identifier files separately to Dropbox.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure secrets (required):**
   - Copy the example secrets file:
     ```bash
     cp .streamlit/secrets.toml.example .streamlit/secrets.toml
     ```
   - Fill in your AWS credentials (Cognito, Bedrock, S3) and Dropbox access token.
   - See `COGNITO_SETUP.md` for authentication setup.
   - See `AWS_S3_SETUP.md` for S3 storage configuration.
   - See `EXPORT_SETUP.md` for Dropbox export details.

3. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## Authentication

Authentication is handled via AWS Cognito.
- Users must log in using an `@uga.edu` email address.
- Session state is managed via OAuth tokens.
- Logout functionality is available in the sidebar.

## Data Storage & Privacy

### Conversation Storage
- **AWS S3**: User profiles and conversation history are stored in S3 with a structured organization:
  - `users/{cognito_user_id}/info.json` - User profile information
  - `users/{cognito_user_id}/conversations.json` - Conversation metadata index
  - `users/{cognito_user_id}/conversations/{conversation_id}.json` - Full conversation data
- **Seamless Experience**: Returning users automatically see their previous conversations in the sidebar
- **On-Demand Loading**: Conversation history loads metadata only; full conversations load when selected

### Privacy & Export
- **Anonymization**: Student names are automatically anonymized in conversation exports
- **Secure Storage**: Identifying information is stored separately from conversation data in Dropbox
- **Consent**: Export requires explicit user consent and privacy acknowledgment
- **Dual Export**: Separate files for identifiers and anonymized conversations

## Directory Structure

- `app.py`: Main Streamlit application
- `utils/`: Helper modules
  - `cognito_auth.py`: AWS Cognito authentication
  - `s3_storage.py`: S3 storage operations for user data and conversations
  - `data_export.py`: Dropbox export with anonymization
- `.streamlit/`: Configuration and secrets
- `figs/`: Assets and images

## How It Works

1. **First-Time Users**:
   - Log in with AWS Cognito (@uga.edu email)
   - Fill out student information form
   - Profile saved to S3 for future sessions
   - Start chatting with ArchPal

2. **Returning Users**:
   - Log in with AWS Cognito
   - Profile automatically loaded from S3
   - Previous conversations appear in sidebar
   - Continue existing conversations or start new ones

3. **Conversation Management**:
   - Each message pair (user + AI) is saved to S3 in real-time
   - Conversations are indexed for quick retrieval
   - Click any conversation in sidebar to resume
   - Use "New Conversation" button to start fresh
