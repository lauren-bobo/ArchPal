# ArchPal AI Companion Demo v1

A Streamlit application that provides a chat interface with Anthropic Claude via LangChain, designed for research demos with student interaction tracking and privacy-preserving data export.

## Features

- **Secure Authentication**: Integrated with AWS Cognito for secure login (only @uga.edu emails allowed).
- **Startup Form**: Collects student information context for the AI coach.
- **Chat Interface**: Powered by Anthropic Claude via LangChain with customizable system prompts.
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
   - Fill in your AWS Cognito, Anthropic API, and Dropbox credentials.
   - See `COGNITO_SETUP.md` for authentication details.
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

## Privacy & Data Handling

- **Anonymization**: Student names are automatically anonymized in conversation exports.
- **Secure Storage**: Identifying information is stored separately from conversation data in Dropbox.
- **Consent**: Export requires explicit user consent and privacy acknowledgment.

## Directory Structure

- `app.py`: Main Streamlit application.
- `utils/`: Helper modules for authentication (`cognito_auth.py`) and data export (`data_export.py`).
- `.streamlit/`: Configuration and secrets.
- `figs/`: Assets and images.
