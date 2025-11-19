# ArchPal AI Companion Demo v1

A Streamlit application that provides a chat interface with Anthropic Claude via LangChain, designed for research demos with student interaction tracking.

## Features

- **Startup Form**: Collects student information (first name, last name, session number) and assigns unique identifiers
- **Chat Interface**: Powered by Anthropic Claude via LangChain
- **Message Logging**: Tracks all messages with timestamps for the duration of the session
- **Export Functionality**: Exports conversations as CSV play scripts with timestamps
- **Dropbox Export**: Automatic CSV export to Dropbox (configured via secrets)
- **Customizable System Prompt**: Includes student context in system prompt

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure secrets (required for Dropbox export):
   - Set up Dropbox API (see `EXPORT_SETUP.md` for detailed instructions)
   - Create `.streamlit/secrets.toml` in your project root
   - Add your Anthropic API key and Dropbox access token
   - Copy from `.streamlit/secrets.toml.example` if needed

3. Run the application:
```bash
streamlit run app.py
```

4. Fill out the startup form with student information

5. If API key is not in secrets, enter it in the sidebar

6. Start chatting with ArchPal!

## Research Features

### Student Information Collection
- On first launch, students fill out a form with:
  - First Name
  - Last Name
  - Session Number
- System automatically generates a unique identifier (UUID)
- This information is included in the system prompt and export

### Message Tracking
- All messages are logged with timestamps
- Messages are stored for the duration of the Streamlit session
- Both student and ArchPal messages are tracked

### Export Format
- Conversations are exported as CSV files
- Format: Play script style with timestamps
- Columns: First Name, Last Name, Unique Identifier, Session Number, Timestamp, Speaker (Student/ArchPal), Message
- Automatically uploaded to Dropbox (configured via secrets)
- CSV download button also available for manual download

## Configuration

The app uses Streamlit secrets for secure configuration:

- **Anthropic API Key** (required): Configure via secrets to avoid manual entry
- **Dropbox API Credentials** (required): Configure for automatic CSV export to Dropbox

See `EXPORT_SETUP.md` for detailed Dropbox API setup instructions for both local development and Streamlit Cloud deployment.
