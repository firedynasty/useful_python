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
from googleapiclient.errors import HttpError

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
        try:
            label = service.users().labels().create(
                userId='me',
                body={'name': label_name}
            ).execute()
            print(f"Created new label: {label_name}")
            return label['id']
        except HttpError as error:
            # If error is because label already exists, try to find it with case insensitive search
            if "Label name exists or conflicts" in str(error):
                for label in labels:
                    if label['name'].lower() == label_name.lower():
                        return label['id']
            raise  # Re-raise if it's a different error
    
    except Exception as e:
        print(f"Error getting/creating label: {e}")
        return None

def get_date_range():
    """
    Calculate the date range from Sunday of the current week to today.
    Returns a list of dates in YYYY/MM/DD format for Gmail queries.
    """
    # Get today's date
    today = datetime.datetime.now()
    
    # Calculate the day of the week (0-6, Monday is 0)
    current_weekday = today.weekday()
    
    # Convert to 0 = Sunday, 1 = Monday, etc.
    days_since_sunday = (current_weekday + 1) % 7
    
    # Calculate Sunday's date
    sunday = today - datetime.timedelta(days=days_since_sunday)
    
    # Create a list of dates from Sunday to today
    date_range = []
    current_date = sunday
    
    while current_date <= today:
        date_range.append(current_date.strftime('%Y/%m/%d'))
        current_date += datetime.timedelta(days=1)
    
    return date_range

def process_day_emails(service, email_filters, date):
    """
    Process emails received on a specific day and apply labels based on filters.
    
    Args:
        service: Gmail API service instance
        email_filters: Dictionary mapping domain patterns to label names
        date: Date in YYYY/MM/DD format
    """
    # Create query for emails on this specific day
    # Gmail search uses after: and before: as inclusive and exclusive respectively
    # To get emails from exactly one day, we need the day and the day after
    date_obj = datetime.datetime.strptime(date, '%Y/%m/%d')
    next_day_obj = date_obj + datetime.timedelta(days=1)
    next_day = next_day_obj.strftime('%Y/%m/%d')
    
    query = f'after:{date} before:{next_day}'
    
    try:
        # Retrieve messages matching the query
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        
        if not messages:
            print(f"No messages found for {date}.")
            return 0
        
        print(f"Found {len(messages)} messages for {date}.")
        
        labeled_count = 0
        
        # Process each message
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            
            # Get the existing labels for this message
            existing_label_ids = msg.get('labelIds', [])
            
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
                            # Skip if label is already applied
                            if label_id in existing_label_ids:
                                print(f"Label '{label_name}' already applied to email from {sender} - skipping")
                            else:
                                # Apply the label to the message
                                service.users().messages().modify(
                                    userId='me',
                                    id=message['id'],
                                    body={'addLabelIds': [label_id]}
                                ).execute()
                                
                                print(f"Applied label '{label_name}' to email from {sender}")
                                labeled_count += 1
                            break
        
        return labeled_count
    
    except Exception as e:
        print(f"Error processing emails for {date}: {e}")
        return 0

def process_emails_by_day(service, email_filters):
    """
    Process emails day by day from Sunday of this week until today.
    
    Args:
        service: Gmail API service instance
        email_filters: Dictionary mapping domain patterns to label names
    """
    # Get the date range from Sunday to today
    date_range = get_date_range()
    
    total_labeled = 0
    
    print(f"Processing emails from {date_range[0]} to {date_range[-1]}...")
    
    # Process each day separately
    for date in date_range:
        print(f"\n--- Processing {date} ---")
        day_labeled = process_day_emails(service, email_filters, date)
        total_labeled += day_labeled
    
    print(f"\nCompleted processing. Applied labels to {total_labeled} emails across the week.")

def main():
    # Define email filters: {domain_pattern: label_name}
    email_filters = {
        'github.com': 'GitHub',
        'linkedin.com': 'LinkedIn',
        'google.com': 'Google',
        'ss.email.nextdoor.com': 'Nextdoor',
        'mail.coinbase.com' : 'Newsletters',
        'substack.com' : 'Newsletters',
        'seekingalpha.com' : 'SeekingAlpha',
        'interactive.wsj.com' : 'Newsletters',
        't.outbound.surveymonkey.com' : 'Surveys',
        # Add more filters as needed
        'newsletter': 'Newsletters',  # This will match any domain containing 'newsletter'
        'billing': 'Bills',
        'amazon': 'Shopping',
    }
    
    # Get the Gmail service
    service = get_gmail_service()
    
    # Process this week's emails day by day
    process_emails_by_day(service, email_filters)

if __name__ == "__main__":
    main()
