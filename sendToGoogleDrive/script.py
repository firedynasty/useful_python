import imaplib
import email
from email.header import decode_header
import datetime
import re
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the scopes for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    """
    Authenticate and get the Gmail API service.
    Requires a credentials.json file from Google Cloud Console.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If credentials don't exist or are invalid, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    # Return the Gmail API service
    return build('gmail', 'v1', credentials=creds)

def get_label_id(service, label_name):
    """
    Get the ID of a label. If it doesn't exist, create it.
    """
    try:
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        for label in labels:
            if label['name'] == label_name:
                return label['id']
        
        # If label doesn't exist, create it
        label = service.users().labels().create(
            userId='me',
            body={'name': label_name}
        ).execute()
        
        return label['id']
    
    except Exception as e:
        print(f"Error getting/creating label: {e}")
        return None

def process_emails(service, email_filters):
    """
    Process emails received today and apply labels based on filters.
    
    Args:
        service: Gmail API service instance
        email_filters: Dictionary mapping domain patterns to label names
    """
    # Get today's date in the format YYYY/MM/DD
    today = datetime.datetime.now().strftime('%Y/%m/%d')
    
    # Search for emails from today
    query = f'after:{today}'
    
    try:
        # Retrieve messages matching the query
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print(f"No new messages found for {today}.")
            return
        
        print(f"Found {len(messages)} messages from today.")
        
        # Process each message
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            
            # Get the sender's email
            headers = msg['payload']['headers']
            sender = next((header['value'] for header in headers if header['name'] == 'From'), '')
            
            # Extract the domain from the sender's email
            domain_match = re.search(r'@([^>]+)', sender)
            if domain_match:
                sender_domain = domain_match.group(1).lower()
                
                # Check which filter matches this domain
                for domain_pattern, label_name in email_filters.items():
                    if domain_pattern in sender_domain:
                        # Get or create the label
                        label_id = get_label_id(service, label_name)
                        
                        if label_id:
                            # Apply the label to the message
                            service.users().messages().modify(
                                userId='me',
                                id=message['id'],
                                body={'addLabelIds': [label_id]}
                            ).execute()
                            
                            print(f"Applied label '{label_name}' to email from {sender}")
                            break
    
    except Exception as e:
        print(f"Error processing emails: {e}")

def main():
    # Define email filters: {domain_pattern: label_name}
    email_filters = {
        'github.com': 'GitHub',
        'linkedin.com': 'LinkedIn',
        # Add more filters as needed
        'newsletter': 'Newsletters',  # This will match any domain containing 'newsletter'
        'amazon': 'Shopping',
    }
    
    # Get the Gmail service
    service = get_gmail_service()
    
    # Process today's emails
    process_emails(service, email_filters)

if __name__ == "__main__":
    main()
