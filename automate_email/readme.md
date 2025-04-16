# Gmail Email Sorter

This Python script automatically sorts your Gmail emails into labels based on the sender's domain. It processes emails received on the current day and applies appropriate labels to help organize your inbox.

## How It Works

The script:
1. Connects to your Gmail account using OAuth2 authentication
2. Retrieves all emails received today
3. Examines the sender's domain for each email
4. Applies a predefined label to the email based on matching domain patterns
5. Creates new labels if they don't already exist

## Setup Instructions

### 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project" or select an existing project
3. Give your project a name (e.g., "Gmail Sorter")
4. Click "Create"

### 2. Enable the Gmail API

1. In your Google Cloud Project, navigate to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on the Gmail API result
4. Click "Enable"

### 3. Configure OAuth Consent Screen

1. Navigate to "APIs & Services" → "OAuth consent screen"
2. Select "External" as the User Type
3. Fill in the required application information:
   - App name (e.g., "Gmail Sorter")
   - User support email (your email)
   - Developer contact information (your email again)
4. Click "Save and Continue"
5. On the "Scopes" page, you can either:
   - Skip adding scopes here (the script will request them at runtime), or
   - Click "Add or Remove Scopes" and add `https://www.googleapis.com/auth/gmail.modify`
6. Click "Save and Continue"
7. Under "Test users", click "Add Users"
8. Add your own email address
9. Click "Save and Continue"
10. Review your app configuration and click "Back to Dashboard"

### 4. Create OAuth Client ID

1. Navigate to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Select "Desktop application" as the application type
4. Give it a name (e.g., "Gmail Sorter Client")
5. Click "Create"
6. Download the credentials file (it will download as a JSON file)
7. Rename the downloaded file to `credentials.json`

### 5. Set Up the Python Script

1. Make sure Python is installed on your computer
2. Install the required libraries:
   ```
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```
3. Create a new file named `gmail_sorter.py`
4. Copy the script code below into this file
5. Place the `credentials.json` file in the same directory as your script

### 6. Configure Email Filters

Edit the `email_filters` dictionary in the `main()` function to match your needs. The format is:
```python
email_filters = {
    'domain_keyword': 'Label_Name',
    # Add more filters as needed
}
```

Examples:
```python
email_filters = {
    'github.com': 'GitHub',
    'linkedin.com': 'LinkedIn',
    'google.com': 'Google',
    'newsletter': 'Newsletters',
    'billing': 'Bills',
    'amazon': 'Shopping',
}
```

### 7. Run the Script

1. Open a terminal or command prompt
2. Navigate to the directory containing your script
3. Run the script:
   ```
   python gmail_sorter.py
   ```
4. A browser window will open asking you to authorize the application
5. Sign in with your Google account and grant the requested permissions
6. The script will process emails received today and apply labels

### 8. (Optional) Set Up Automatic Daily Execution

#### Windows:
1. Open Task Scheduler
2. Create a Basic Task
3. Give it a name and description
4. Set it to run Daily
5. Set the start time
6. Choose "Start a program"
7. Browse to your Python executable and add the full path to your script as an argument

#### macOS/Linux:
1. Open Terminal
2. Edit your crontab with: `crontab -e`
3. Add a line like: `0 18 * * * /usr/bin/python3 /path/to/gmail_sorter.py`
   (This runs the script daily at 6 PM)

## Full Script Code

```python
.. see script_3.py


```

## Common Issues and Troubleshooting

1. **Authentication Error**: Make sure your `credentials.json` file is in the same directory as the script.

2. **"Label name exists or conflicts"**: This is usually not a critical error. It means the label already exists in your Gmail account but with slightly different formatting or case. The script will still find and use the existing label.

3. **Access Denied**: If you see "Access blocked" or "not completed the Google verification process" errors, make sure you've added your email as a test user in the OAuth consent screen.

4. **Scope Error**: If you get an error about scopes, make sure you're accepting all requested permissions when the authorization screen appears.

## Customizing the Script

- **Change the time period**: Modify the `query` variable in `process_emails()` to search for emails from different time periods
- **Add more sophisticated filters**: Enhance the filtering logic to look at subject lines, email content, or other criteria
- **Add notification features**: Modify the script to send you a summary of actions taken

## Security Notes

- The script uses OAuth2, so it never stores your Gmail password
- The `token.json` file contains access tokens - keep it secure and don't share it
- The script only requests the minimum permissions needed to read and modify labels

## License

This project is provided as-is without any warranty. Use at your own risk.



Script_4.py vs. Script_3.py does it from the beginning to the week until current day, vs. just the day of. 



script_3.py compared to script_2.py because what if the labels had been applied? then run it again will skip that label.



Here's a comparison of the differences between the original script and the updated version:

### 1. Handling Label Conflicts (First Update)

**Original:**

```python
# If label doesn't exist, create it
label = service.users().labels().create(
    userId='me',
    body={'name': label_name}
).execute()

return label['id']
```

**Updated:**

```python
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
```

**Changes:**

- Added error handling with try/except for label creation
- Added case-insensitive matching to find existing labels with different capitalization
- Added a message when successfully creating a new label

### 2. Added Missing Import (Second Update)

**Original:**

```python
from googleapiclient.discovery import build
```

**Updated:**

```python
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
```

**Changes:**

- Added the import for HttpError which is needed for error handling

### 3. Skip Already-Labeled Emails (Third Update)

**Original:**

```python
# Get the sender's email
headers = msg['payload']['headers']
sender = next((header['value'] for header in headers if header['name'] == 'From'), '')

# [processing code]

if label_id:
    # Apply the label to the message
    service.users().messages().modify(
        userId='me',
        id=message['id'],
        body={'addLabelIds': [label_id]}
    ).execute()
    
    print(f"Applied label '{label_name}' to email from {sender}")
```

**Updated:**

```python
# Get the existing labels for this message
existing_label_ids = msg.get('labelIds', [])

# Get the sender's email
headers = msg['payload']['headers']
sender = next((header['value'] for header in headers if header['name'] == 'From'), '')

# [processing code]

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
```

**Changes:**

- Added retrieval of existing label IDs for each message
- Added a conditional check to skip applying labels that are already present
- Added a message when skipping already-labeled emails

These changes make the script more robust by:

1. Handling label conflicts more gracefully
2. Avoiding unnecessary API calls by not re-applying existing labels
3. Providing better feedback about what the script is doing
