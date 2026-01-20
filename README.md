# ArchPal

**ArchPal** is an AI-powered writing coach designed to help students plan, brainstorm, and refine their writing while maintaining academic integrity.

## Project Structure

- `demo/demo-v1/` - The main Streamlit application containing the AI writing coach interface.
- `demo/demo-v1/utils/` - Utility modules for authentication and data export.

## Quick Start

1.  Navigate to the application directory:
    ```bash
    cd demo/demo-v1
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure secrets (see [COGNITO_SETUP.md](demo/demo-v1/COGNITO_SETUP.md)):
    ```bash
    cp .streamlit/secrets.toml.example .streamlit/secrets.toml
    # Edit secrets.toml with your AWS Cognito and Anthropic credentials
    ```

4.  Run the application:
    ```bash
    streamlit run app.py
    ```

## Documentation

- [App Features & Setup](demo/demo-v1/README.md)
- [Cognito Authentication Setup](demo/demo-v1/COGNITO_SETUP.md)
- [Data Export Setup](demo/demo-v1/EXPORT_SETUP.md)

## License

See [LICENSE](LICENSE) file for details.