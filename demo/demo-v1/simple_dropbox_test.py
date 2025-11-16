#!/usr/bin/env python3
"""
Simple Dropbox upload test - creates dummy CSV and uploads to specified folder.
Run with: python simple_dropbox_test.py
"""

import csv
import io
import os
from datetime import datetime

# Import Dropbox modules (these should be available in the Streamlit environment)
try:
    import dropbox
    DROPBOX_MODULES_AVAILABLE = True
except ImportError as e:
    print("ERROR: Dropbox API modules not available. Please install with:")
    print("   pip install dropbox")
    DROPBOX_MODULES_AVAILABLE = False

# Read secrets from Streamlit secrets file
def load_secrets():
    """Load secrets from the Streamlit secrets.toml file"""
    secrets_path = os.path.join(os.path.dirname(__file__), '.streamlit', 'secrets.toml')

    if not os.path.exists(secrets_path):
        raise FileNotFoundError(f"Secrets file not found at: {secrets_path}")

    import tomllib
    with open(secrets_path, 'rb') as f:
        return tomllib.load(f)

def create_dummy_csv():
    """Create a dummy CSV with sample data"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["Timestamp", "Test Data 1", "Test Data 2", "Test Data 3"])

    # Write sample rows
    now = datetime.now().isoformat()
    writer.writerow([now, "Sample Row 1 Col 1", "Sample Row 1 Col 2", "Sample Row 1 Col 3"])
    writer.writerow([now, "Sample Row 2 Col 1", "Sample Row 2 Col 2", "Sample Row 2 Col 3"])
    writer.writerow([now, "Sample Row 3 Col 1", "Sample Row 3 Col 2", "Sample Row 3 Col 3"])

    csv_content = output.getvalue()
    output.close()

    return csv_content

def test_folder_access(dbx, folder_path):
    """Test if Dropbox app can access the folder"""
    try:
        # Test folder access by listing its contents
        result = dbx.files_list_folder(folder_path)
        print(f"SUCCESS: Folder accessible: {folder_path}")
        print(f"Folder contains {len(result.entries)} items")
        return True
    except Exception as e:
        print(f"ERROR: Cannot access folder: {str(e)}")
        return False

def upload_to_dropbox(csv_content, filename, folder_path, dbx):
    """Upload CSV content to Dropbox"""

    # Construct full path
    if folder_path and not folder_path.startswith('/'):
        folder_path = '/' + folder_path
    if folder_path and not folder_path.endswith('/'):
        folder_path = folder_path + '/'
    full_path = f"{folder_path}{filename}"

    # Upload file
    csv_bytes = csv_content.encode('utf-8')
    result = dbx.files_upload(csv_bytes, full_path, mode=dropbox.files.WriteMode.overwrite)

    return result

def main():
    print("Starting Dropbox upload test...")
    print("=" * 50)

    if not DROPBOX_MODULES_AVAILABLE:
        print("ERROR: Cannot proceed without Dropbox API modules.")
        return False

    try:
        # Step 1: Load secrets
        print("Step 1: Loading secrets...")
        secrets = load_secrets()
        print("SUCCESS: Secrets loaded successfully")

        # Step 2: Get Dropbox credentials and folder
        print("Step 2: Setting up Dropbox credentials...")
        dropbox_token = secrets["dropbox_access_token"]
        folder_path = secrets.get("dropbox_folder_path", "")

        print(f"Target folder path: {folder_path or 'Root folder'}")

        dbx = dropbox.Dropbox(dropbox_token)
        print("SUCCESS: Dropbox client initialized")

        # Step 2.5: Test folder access
        print("Step 2.5: Testing folder access...")
        if folder_path:
            # Ensure folder path starts with /
            if not folder_path.startswith('/'):
                folder_path = '/' + folder_path
            folder_accessible = test_folder_access(dbx, folder_path)
            if not folder_accessible:
                print("ERROR: Folder access test failed - check folder path and permissions")
                return False
        else:
            print("INFO: No folder path specified - will upload to root")

        # Step 3: Create dummy CSV
        print("Step 3: Creating dummy CSV...")
        csv_content = create_dummy_csv()
        print("SUCCESS: Dummy CSV created")
        print("CSV Content:")
        print("-" * 30)
        print(csv_content)
        print("-" * 30)

        # Step 4: Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_upload_{timestamp}.csv"
        print(f"Step 4: Generated filename: {filename}")

        # Step 5: Upload to Dropbox
        print("Step 5: Uploading to Dropbox...")
        uploaded_file = upload_to_dropbox(csv_content, filename, folder_path, dbx)

        # Success!
        print("SUCCESS! File uploaded successfully!")
        print("=" * 50)
        print(f"File Name: {uploaded_file.name}")
        print(f"File Path: {uploaded_file.path_display}")
        print(f"File Size: {uploaded_file.size} bytes")
        print("=" * 50)

        return True

    except Exception as e:
        print("ERROR! Upload failed!")
        print("=" * 50)
        print(f"Error: {str(e)}")
        print("=" * 50)

        # Additional troubleshooting
        print("\nTroubleshooting tips:")
        print("- Check that your Dropbox access token is valid")
        print("- Verify the folder path exists and your app has access")
        print("- Ensure the Dropbox API app has the correct permissions")
        print("- Check that the access token hasn't expired")

        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
