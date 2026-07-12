# Language-Specific Credentials Update

## Changes Made

The transcription system was updated to support language-specific credentials, allowing separate service accounts for different languages (Cantonese, Mandarin, English).

### 1. Environment Variables

Add these to your `~/.zshrc`:

```bash
export GOOGLE_APPLICATION_CREDENTIALS_CANTONESE="/Users/stanleytan/Documents/46-python/transcribe_audio/cantonese/service_account_key.json"
export GOOGLE_APPLICATION_CREDENTIALS_MANDARIN="/Users/stanleytan/Documents/46-python/transcribe_audio/mandarin/service_account_key.json"
export GOOGLE_APPLICATION_CREDENTIALS_ENGLISH="/Users/stanleytan/Documents/46-python/transcribe_audio/english/service_account_key.json"
```

### 2. Script Modifications

Updated both `transcribe_audio_cantonese.py` and `record_and_transcribe_cantonese.py` to check for language-specific credentials before falling back to the default:

```python
# Try to use language-specific credentials first
cantonese_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_CANTONESE")
if cantonese_credentials:
    print(f"Using Cantonese-specific credentials from: {cantonese_credentials}")
    credentials = service_account.Credentials.from_service_account_file(cantonese_credentials)
    client = speech.SpeechClient(credentials=credentials)
else:
    # Fall back to default credentials
    print("No language-specific credentials found, using default credentials")
    credentials, project = google.auth.default()
    client = speech.SpeechClient(credentials=credentials)
```

### 3. Benefits

- Organize transcription services by language
- Use different Google Cloud projects for different languages
- Separate billing and quota usage
- Maintain independent service configurations
- Simplify development across multiple language projects

### 4. Usage

After setting the environment variables, restart your terminal or run `source ~/.zshrc`. The scripts will automatically use the appropriate credentials file for each language.

### 5. File Organization

Recommended directory structure:
```
transcribe_audio/
  ├── cantonese/
  │   ├── service_account_key.json    # Cantonese-specific credentials
  │   ├── transcribe_audio_cantonese.py
  │   └── record_and_transcribe_cantonese.py
  ├── mandarin/
  │   ├── service_account_key.json    # Mandarin-specific credentials
  │   ├── transcribe_audio_mandarin.py
  │   └── record_and_transcribe_mandarin.py
  └── english/
      ├── service_account_key.json    # English-specific credentials
      ├── transcribe_audio_english.py
      └── record_and_transcribe_english.py
```