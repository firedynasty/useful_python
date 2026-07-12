import os
import hashlib
import mimetypes
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/drive']

def get_drive_service():
    """Authenticate and get the Google Drive API service."""
    creds = None
    token_file = 'drive_token.json'  # Use separate token file for Drive
    
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

def get_file_md5(file_path):
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def find_drive_folder(service, folder_name, parent_id='root'):
    """Find a folder in Google Drive by name."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and parents in '{parent_id}'"
    results = service.files().list(q=query).execute()
    items = results.get('files', [])
    return items[0]['id'] if items else None

def create_drive_folder(service, folder_name, parent_id='root'):
    """Create a folder in Google Drive."""
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

def get_drive_folder_contents(service, folder_id):
    """Get all files and folders in a Drive folder."""
    query = f"parents in '{folder_id}'"
    results = service.files().list(q=query, fields='files(id,name,mimeType,md5Checksum,modifiedTime)').execute()
    return results.get('files', [])

def upload_file_to_drive(service, file_path, folder_id, existing_file_id=None):
    """Upload or update a file to Google Drive."""
    file_name = os.path.basename(file_path)
    mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
    
    try:
        media = MediaFileUpload(file_path, mimetype=mime_type)
        
        if existing_file_id:
            # Update existing file
            file = service.files().update(
                fileId=existing_file_id,
                media_body=media,
                fields='id'
            ).execute()
            print(f"Updated: {file_name}")
        else:
            # Upload new file
            file_metadata = {
                'name': file_name,
                'parents': [folder_id]
            }
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            print(f"Uploaded: {file_name}")
        
        return file.get('id')
    except HttpError as error:
        print(f"Error uploading {file_name}: {error}")
        return None
    except Exception as error:
        print(f"Unexpected error uploading {file_name}: {error}")
        return None

def delete_drive_file(service, file_id, file_name):
    """Delete a file from Google Drive."""
    service.files().delete(fileId=file_id).execute()
    print(f"Deleted: {file_name}")

def sync_folder_to_drive_recursive(service, local_folder_path, drive_folder_id, base_path):
    """Recursively sync a local folder and its subfolders to Google Drive."""
    # Get current contents of Drive folder
    drive_files = get_drive_folder_contents(service, drive_folder_id)
    drive_files_dict = {f['name']: f for f in drive_files}
    
    # Track which files and folders we've processed
    processed_items = set()
    
    # Process local files and folders
    for item in local_folder_path.iterdir():
        if item.name.startswith('.'):
            continue  # Skip hidden files
        
        processed_items.add(item.name)
        
        if item.is_file():
            # Handle file
            if item.name in drive_files_dict:
                drive_file = drive_files_dict[item.name]
                
                # Compare file hashes if available
                local_md5 = get_file_md5(item)
                drive_md5 = drive_file.get('md5Checksum')
                
                if drive_md5 and local_md5 == drive_md5:
                    print(f"Skipping (unchanged): {item.relative_to(base_path)}")
                    continue
                
                # Update existing file
                upload_file_to_drive(service, item, drive_folder_id, drive_file['id'])
            else:
                # Upload new file
                upload_file_to_drive(service, item, drive_folder_id)
        
        elif item.is_dir():
            # Handle folder
            subfolder_id = None
            if item.name in drive_files_dict:
                drive_item = drive_files_dict[item.name]
                if drive_item['mimeType'] == 'application/vnd.google-apps.folder':
                    subfolder_id = drive_item['id']
                    print(f"Using existing folder: {item.relative_to(base_path)}")
            
            if not subfolder_id:
                subfolder_id = create_drive_folder(service, item.name, drive_folder_id)
                print(f"Created folder: {item.relative_to(base_path)}")
            
            # Recursively sync subfolder
            sync_folder_to_drive_recursive(service, item, subfolder_id, base_path)
    
    # Delete items that exist on Drive but not locally (rclone sync behavior)
    for drive_item_name, drive_item in drive_files_dict.items():
        if drive_item_name not in processed_items:
            delete_drive_file(service, drive_item['id'], drive_item_name)

def find_or_create_drive_folder_path(service, folder_path):
    """Find or create a nested folder path in Google Drive."""
    if not folder_path or folder_path == '/':
        return 'root'
    
    # Split the path into parts
    path_parts = [part for part in folder_path.split('/') if part]
    
    current_parent_id = 'root'
    
    # Navigate/create each folder in the path
    for folder_name in path_parts:
        folder_id = find_drive_folder(service, folder_name, current_parent_id)
        if not folder_id:
            folder_id = create_drive_folder(service, folder_name, current_parent_id)
            print(f"Created Drive folder: {'/'.join(path_parts[:path_parts.index(folder_name)+1])}")
        
        current_parent_id = folder_id
    
    return current_parent_id

def sync_folder_to_drive(local_folder_path, drive_folder_path=None):
    """Sync a local folder to Google Drive like rclone sync."""
    local_folder_path = Path(local_folder_path)
    if not local_folder_path.exists():
        print(f"Error: Local folder '{local_folder_path}' does not exist.")
        return
    
    if drive_folder_path is None:
        drive_folder_path = local_folder_path.name
    
    service = get_drive_service()
    
    # Find or create the destination folder path on Drive
    drive_folder_id = find_or_create_drive_folder_path(service, drive_folder_path)
    if drive_folder_id != 'root':
        print(f"Using Drive folder path: {drive_folder_path}")
    
    # Start recursive sync
    sync_folder_to_drive_recursive(service, local_folder_path, drive_folder_id, local_folder_path)

def main():
    """Main function to run the sync."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sync local folder to Google Drive (like rclone sync)')
    parser.add_argument('-i', '--input', required=True, help='Local folder path to sync from')
    parser.add_argument('-o', '--output', required=True, help='Google Drive folder path to sync to')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be synced without actually doing it')
    
    args = parser.parse_args()
    
    print(f"Syncing '{args.input}' to Google Drive folder '{args.output}'...")
    
    if args.dry_run:
        print("DRY RUN MODE - No actual changes will be made")
        # TODO: Implement dry run functionality
        return
    
    sync_folder_to_drive(args.input, args.output)
    print("Sync completed!")

if __name__ == "__main__":
    main()