import os
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Same read-only scope works for previews
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

def search_drive(service, search_term, search_type='all'):
    """Search for files or folders in Google Drive."""
    if search_type == 'folder':
        query = f"name contains '{search_term}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    elif search_type == 'file':
        query = f"name contains '{search_term}' and mimeType!='application/vnd.google-apps.folder' and trashed=false"
    else:
        query = f"name contains '{search_term}' and trashed=false"

    try:
        results = service.files().list(
            q=query,
            fields='files(id, name, mimeType, size)',
            orderBy='folder,name'
        ).execute()
        return results.get('files', [])
    except Exception as e:
        print(f"Error searching: {e}")
        return []

def get_folder_contents(service, folder_id, recursive=True):
    """Get all files in a folder, optionally recursive."""
    files_list = []

    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields='files(id, name, mimeType, size)',
        orderBy='name'
    ).execute()

    items = results.get('files', [])

    for item in items:
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            if recursive:
                files_list.extend(get_folder_contents(service, item['id'], recursive=True))
        else:
            files_list.append(item)

    return files_list

def download_file_chunk(service, file_id, mime_type):
    """Download first chunk of a file and return as text."""
    try:
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
                return "[Unsupported Google format for preview]"

        # Handle regular files - download only first chunk for preview
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        # Download only first chunk (typically ~256KB)
        status, done = downloader.next_chunk()

        content = fh.getvalue()

        # Try to decode as text
        try:
            text = content.decode('utf-8')
            return text if text.strip() else "[Empty file]"
        except UnicodeDecodeError:
            return "[Binary file - no text preview available]"

    except Exception as e:
        return f"[Error reading file: {str(e)[:100]}]"

def get_file_preview(text, max_chars=500):
    """Extract a preview from the downloaded text."""
    preview = text[:max_chars].replace('\n', ' ').strip()
    # Clean up multiple spaces
    preview = ' '.join(preview.split())
    return preview if preview else "[Empty file]"

def preview_files(service, files_list, recursive=True):
    """Preview files one by one with pagination."""
    if not files_list:
        print("No files to preview.")
        return

    # Filter supported file types
    supported_extensions = {'.txt', '.md', '.csv', '.rtf', '.pdf'}
    google_doc_types = {
        'application/vnd.google-apps.document',
        'application/vnd.google-apps.spreadsheet'
    }

    previewable_files = []
    for file in files_list:
        mime_type = file.get('mimeType', '')
        file_name = file.get('name', '')
        file_ext = os.path.splitext(file_name)[1].lower()

        if file_ext in supported_extensions or mime_type in google_doc_types:
            previewable_files.append(file)

    if not previewable_files:
        print("No previewable files found (txt, md, csv, rtf, pdf, Google Docs).")
        return

    print(f"\nFound {len(previewable_files)} previewable file(s)")
    print("=" * 60)

    for idx, file in enumerate(previewable_files, 1):
        print(f"\n{file['name']}")
        print("***_______")

        # Download the chunk once
        full_text = download_file_chunk(service, file['id'], file['mimeType'])

        # Show compact preview (500 chars, newlines collapsed)
        preview = get_file_preview(full_text, max_chars=500)
        print(preview)
        print()

        print()

    # Interactive loop to keep the script running until 'q' is pressed
    print("=" * 60)
    print("\nPreview complete.")
    while True:
        response = input("\nPress 'q' to quit: ").strip().lower()
        if response in ['q', 'quit', 'exit']:
            break
    print("\nExiting...")

def main():
    """Main function to search and preview files."""
    import argparse

    parser = argparse.ArgumentParser(description='Search and preview files from Google Drive')
    parser.add_argument('search_term', help='Folder or file name to search for')
    parser.add_argument('-t', '--type', choices=['all', 'folder', 'file'], default='all',
                       help='Search type (default: all)')
    parser.add_argument('-r', '--recursive', action='store_true', default=False,
                       help='Search recursively through subdirectories')

    args = parser.parse_args()

    service = get_drive_service()

    print(f"Searching for '{args.search_term}'...\n")
    results = search_drive(service, args.search_term, args.type)

    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} result(s):\n")

    # Display results with URLs
    for i, item in enumerate(results, 1):
        is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
        item_type = "📁" if is_folder else "📄"

        url = f"https://drive.google.com/drive/folders/{item['id']}" if is_folder else f"https://drive.google.com/file/d/{item['id']}/view"

        print(f"{i}. {item_type} {item['name']}")
        print(f"   URL: {url}\n")

    # Ask user what to preview
    response = input(f"Preview which item? (1-{len(results)}, 'all', or 'n' to cancel): ").strip().lower()

    if response == 'n':
        print("Cancelled.")
        return

    # Collect files to preview
    files_to_preview = []

    if response == 'all':
        for item in results:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                print(f"\nGetting files from folder '{item['name']}'...")
                files_to_preview.extend(get_folder_contents(service, item['id'], recursive=args.recursive))
            else:
                files_to_preview.append(item)
    elif response.isdigit():
        idx = int(response) - 1
        if 0 <= idx < len(results):
            item = results[idx]

            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # Ask for recursive search
                if not args.recursive:
                    choice = input("Search recursively through subdirectories? (r/m)\n"
                                 "r = recursive (all subdirectories)\n"
                                 "m = max depth 1 (current folder only)\n"
                                 "Enter choice (r/m): ").strip().lower()
                    recursive = choice in ['r', 'recursive']
                else:
                    recursive = True

                print(f"\nGetting files from folder '{item['name']}'...")
                files_to_preview.extend(get_folder_contents(service, item['id'], recursive=recursive))
            else:
                files_to_preview.append(item)
        else:
            print("Invalid number.")
            return
    else:
        print("Invalid input.")
        return

    # Preview the files
    preview_files(service, files_to_preview)

if __name__ == "__main__":
    main()
