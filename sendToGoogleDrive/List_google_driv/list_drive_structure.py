import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """Authenticate and get the Google Drive API service with read-only access."""
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

def get_folder_contents(service, folder_id):
    """Get all files and folders in a Drive folder."""
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields='files(id, name, mimeType, size, modifiedTime)',
        orderBy='folder,name'
    ).execute()
    return results.get('files', [])

def format_size(size_bytes):
    """Convert bytes to human-readable format."""
    if size_bytes is None:
        return ""

    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}PB"

def print_tree(service, folder_id, prefix="", folder_name="My Drive", is_last=True):
    """Recursively print the folder structure in tree format."""
    # Print current folder
    connector = "└── " if is_last else "├── "
    if prefix == "":
        print(folder_name)
    else:
        print(f"{prefix}{connector}{folder_name}/")

    # Get contents of current folder
    items = get_folder_contents(service, folder_id)

    if not items:
        return

    # Separate folders and files
    folders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
    files = [item for item in items if item['mimeType'] != 'application/vnd.google-apps.folder']

    # Update prefix for children
    extension = "    " if is_last else "│   "
    new_prefix = prefix + extension

    # Print files first
    total_items = len(folders) + len(files)
    current_item = 0

    for file in files:
        current_item += 1
        is_last_item = current_item == total_items
        connector = "└── " if is_last_item else "├── "

        size_str = format_size(int(file.get('size', 0))) if 'size' in file else ""
        size_display = f" ({size_str})" if size_str else ""

        print(f"{new_prefix}{connector}{file['name']}{size_display}")

    # Then print folders recursively
    for i, folder in enumerate(folders):
        current_item += 1
        is_last_item = current_item == total_items
        print_tree(service, folder['id'], new_prefix, folder['name'], is_last_item)

def list_drive_structure(folder_path=None):
    """List Google Drive folder structure starting from a specific path or root."""
    service = get_drive_service()

    if folder_path and folder_path != '/':
        # Find the folder by path
        path_parts = [part for part in folder_path.split('/') if part]
        current_id = 'root'

        for folder_name in path_parts:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and '{current_id}' in parents and trashed=false"
            results = service.files().list(q=query, fields='files(id, name)').execute()
            items = results.get('files', [])

            if not items:
                print(f"Error: Folder '{folder_name}' not found in path '{folder_path}'")
                return

            current_id = items[0]['id']

        folder_name = path_parts[-1]
    else:
        current_id = 'root'
        folder_name = "My Drive"

    print_tree(service, current_id, "", folder_name)

def main():
    """Main function to run the script."""
    import argparse

    parser = argparse.ArgumentParser(description='List Google Drive folder structure')
    parser.add_argument('path', nargs='?', help='Google Drive folder path to list (default: root)', default='/')

    args = parser.parse_args()

    print(f"Listing Google Drive structure for: {args.path if args.path != '/' else 'My Drive'}\n")
    list_drive_structure(args.path)

if __name__ == "__main__":
    main()
