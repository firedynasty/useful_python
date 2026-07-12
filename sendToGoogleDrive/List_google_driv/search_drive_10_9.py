import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

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

def get_file_path(service, file_id):
    """Get the full path of a file by traversing parent folders."""
    path_parts = []
    current_id = file_id

    while current_id != 'root':
        try:
            file = service.files().get(fileId=current_id, fields='name, parents').execute()
            path_parts.insert(0, file['name'])

            parents = file.get('parents', [])
            if not parents:
                break
            current_id = parents[0]
        except Exception:
            break

    return '/' + '/'.join(path_parts) if path_parts else '/My Drive'

def get_folder_contents(service, folder_id):
    """Get all files and folders in a Drive folder."""
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        fields='files(id, name, mimeType, size)',
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

def print_tree(service, folder_id, prefix="", is_last=True):
    """Print folder contents in tree format."""
    items = get_folder_contents(service, folder_id)

    if not items:
        print(f"{prefix}    (empty)")
        return

    # Separate folders and files
    folders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
    files = [item for item in items if item['mimeType'] != 'application/vnd.google-apps.folder']

    total_items = len(folders) + len(files)
    current_item = 0

    # Print files first
    for file in files:
        current_item += 1
        is_last_item = current_item == total_items
        connector = "└── " if is_last_item else "├── "

        size_str = format_size(int(file.get('size', 0))) if 'size' in file else ""
        size_display = f" ({size_str})" if size_str else ""

        print(f"{prefix}{connector}{file['name']}{size_display}")

    # Then print folders
    for folder in folders:
        current_item += 1
        is_last_item = current_item == total_items
        connector = "└── " if is_last_item else "├── "

        print(f"{prefix}{connector}{folder['name']}/")

        # Print folder contents with indentation
        extension = "    " if is_last_item else "│   "
        new_prefix = prefix + extension
        print_tree(service, folder['id'], new_prefix, is_last_item)

def search_drive(service, search_term, search_type='all'):
    """Search for files or folders in Google Drive.

    If search_term contains '/', it will be treated as a path search.
    The last part is used for the name search, and results are filtered
    to only show items whose full path contains the search term.
    """
    # Check if this is a path-based search
    if '/' in search_term:
        # Extract the last part of the path for the name search
        path_parts = search_term.strip('/').split('/')
        name_to_search = path_parts[-1]
    else:
        name_to_search = search_term

    # Build query based on search type
    if search_type == 'folder':
        query = f"name contains '{name_to_search}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    elif search_type == 'file':
        query = f"name contains '{name_to_search}' and mimeType!='application/vnd.google-apps.folder' and trashed=false"
    else:
        query = f"name contains '{name_to_search}' and trashed=false"

    try:
        results = service.files().list(
            q=query,
            fields='files(id, name, mimeType, size, parents)',
            orderBy='folder,name'
        ).execute()
        items = results.get('files', [])

        # If path-based search, filter results by full path
        if '/' in search_term:
            filtered_items = []
            for item in items:
                full_path = get_file_path(service, item['id'])
                # Check if the search term appears in the full path
                if search_term.lower() in full_path.lower():
                    filtered_items.append(item)
            return filtered_items

        return items
    except Exception as e:
        print(f"Error searching: {e}")
        return []

def main():
    """Main function to run the script."""
    import argparse

    parser = argparse.ArgumentParser(description='Search Google Drive and list folder contents')
    parser.add_argument('search_term', help='Folder or file name to search for')
    parser.add_argument('-t', '--type', choices=['all', 'folder', 'file'], default='all',
                       help='Type of items to search for (default: all)')
    parser.add_argument('-l', '--list', action='store_true',
                       help='List contents of found folders')

    args = parser.parse_args()

    service = get_drive_service()

    print(f"Searching for '{args.search_term}'...\n")
    results = search_drive(service, args.search_term, args.type)

    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} result(s):\n")

    # Store URLs for later clipboard copy
    urls = []

    for i, item in enumerate(results, 1):
        is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
        item_type = "📁 Folder" if is_folder else "📄 File"

        # Get full path
        path = get_file_path(service, item['id'])

        # Get size if it's a file
        size_str = ""
        if not is_folder and 'size' in item:
            size_str = f" ({format_size(int(item['size']))})"

        # Generate URL
        url = f"https://drive.google.com/drive/folders/{item['id']}" if is_folder else f"https://drive.google.com/file/d/{item['id']}/view"
        urls.append(url)

        print(f"{i}. {item_type}: {item['name']}{size_str}")
        print(f"   Path: {path}")
        print(f"   URL: {url}")

        # Only list contents if explicitly requested with -l flag, or if simple name search (no path)
        if args.list and is_folder:
            print(f"   Contents:")
            print_tree(service, item['id'], "   ")
        elif '/' not in args.search_term and is_folder:
            # Auto-list for simple searches only
            print(f"   Contents:")
            print_tree(service, item['id'], "   ")

        print()

    # Ask user if they want to copy URL to clipboard
    if PYPERCLIP_AVAILABLE and urls:
        if len(urls) == 1:
            response = input("Copy URL to clipboard? (y/n): ").lower().strip()
            if response == 'y' or response == 'yes':
                pyperclip.copy(urls[0])
                print("✓ URL copied to clipboard!")
        else:
            response = input(f"Copy URL to clipboard? Enter number (1-{len(urls)}) or 'n' to skip: ").strip()
            if response.isdigit():
                idx = int(response) - 1
                if 0 <= idx < len(urls):
                    pyperclip.copy(urls[idx])
                    print(f"✓ URL {response} copied to clipboard!")
                else:
                    print("Invalid number.")
    elif not PYPERCLIP_AVAILABLE:
        print("\nNote: Install pyperclip to enable clipboard copying: pip install pyperclip")

if __name__ == "__main__":
    main()
