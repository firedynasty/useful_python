import os
import io
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

# Read-only scope
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """Authenticate and get the Google Drive API service."""
    creds = None
    token_file = 'drive_token.json'

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed: {e}")
                print("Need to re-authenticate...")
                creds = None

        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def extract_file_id(url):
    """Extract file ID from Google Drive URL."""
    # Pattern for Google Docs URLs: /document/d/{FILE_ID}/
    docs_match = re.search(r'/document/d/([a-zA-Z0-9_-]+)', url)
    if docs_match:
        return docs_match.group(1)

    # Pattern for Google Sheets URLs: /spreadsheets/d/{FILE_ID}/
    sheets_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9_-]+)', url)
    if sheets_match:
        return sheets_match.group(1)

    # Pattern for Google Slides URLs: /presentation/d/{FILE_ID}/
    slides_match = re.search(r'/presentation/d/([a-zA-Z0-9_-]+)', url)
    if slides_match:
        return slides_match.group(1)

    # Pattern for file URLs: /file/d/{FILE_ID}/
    file_match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
    if file_match:
        return file_match.group(1)

    # Pattern for folder URLs: /folders/{FOLDER_ID}
    folder_match = re.search(r'/folders/([a-zA-Z0-9_-]+)', url)
    if folder_match:
        return folder_match.group(1)

    # Pattern for open URLs: /open\?id={FILE_ID}
    open_match = re.search(r'/open\?id=([a-zA-Z0-9_-]+)', url)
    if open_match:
        return open_match.group(1)

    return None

def download_full_file(service, file_id):
    """Download complete file contents and return as text."""
    try:
        # Get file metadata to determine mime type
        file_metadata = service.files().get(fileId=file_id, fields='name, mimeType').execute()
        mime_type = file_metadata.get('mimeType', '')
        file_name = file_metadata.get('name', 'Unknown')

        print(f"Downloading: {file_name}")
        print(f"Type: {mime_type}")

        # Handle Google Docs formats
        if mime_type.startswith('application/vnd.google-apps'):
            export_map = {
                'application/vnd.google-apps.document': 'text/plain',
                'application/vnd.google-apps.spreadsheet': 'text/csv',
            }

            if mime_type in export_map:
                request = service.files().export_media(fileId=file_id, mimeType=export_map[mime_type])
                content = request.execute()
                text = content.decode('utf-8', errors='ignore')
                return text if text.strip() else "[Empty file]"
            else:
                return f"[Unsupported Google format: {mime_type}]"

        # Handle regular files - download complete file
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download progress: {int(status.progress() * 100)}%")

        content = fh.getvalue()

        # Try to decode as text
        try:
            text = content.decode('utf-8')
            return text if text.strip() else "[Empty file]"
        except UnicodeDecodeError:
            return "[Binary file - cannot convert to text]"

    except Exception as e:
        return f"[Error reading file: {str(e)}]"

def main():
    """Main function to get URL and copy file contents to clipboard."""
    import argparse

    parser = argparse.ArgumentParser(description='Download Google Drive file contents to clipboard')
    parser.add_argument('url', nargs='?', help='Google Drive URL (optional if using stdin)')

    args = parser.parse_args()

    # Get URL from argument or prompt user
    if args.url:
        url = args.url
    else:
        url = input("Paste Google Drive URL: ").strip()

    if not url:
        print("No URL provided.")
        return

    # Extract file ID from URL
    file_id = extract_file_id(url)
    if not file_id:
        print("Could not extract file ID from URL.")
        print("Supported URL formats:")
        print("  - https://docs.google.com/document/d/{FILE_ID}/...")
        print("  - https://docs.google.com/spreadsheets/d/{FILE_ID}/...")
        print("  - https://drive.google.com/file/d/{FILE_ID}/view")
        print("  - https://drive.google.com/folders/{FOLDER_ID}")
        print("  - https://drive.google.com/open?id={FILE_ID}")
        return

    print(f"\nFile ID: {file_id}")

    # Convert to standard Drive URL
    drive_url = f"https://drive.google.com/file/d/{file_id}/view"
    print(f"Drive URL: {drive_url}")

    # Get Drive service
    service = get_drive_service()

    # Download file contents
    print("\nDownloading file...")
    content = download_full_file(service, file_id)

    # Copy to clipboard if available
    if PYPERCLIP_AVAILABLE:
        if not content.startswith('['):  # Check if it's not an error message
            pyperclip.copy(content)
            print("\n✓ File contents copied to clipboard!")
        else:
            print(f"\n✗ Could not copy file: {content}")
    else:
        print("\nNote: Install pyperclip to enable clipboard copying: pip install pyperclip")
        print("\nFile contents:")
        print("=" * 60)
        print(content[:1000])  # Show first 1000 chars
        if len(content) > 1000:
            print(f"\n... ({len(content) - 1000} more characters)")

if __name__ == "__main__":
    main()
