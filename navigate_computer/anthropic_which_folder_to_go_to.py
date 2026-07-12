import os
import requests
import json
import pyperclip
from dotenv import load_dotenv

class FolderFinder:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key from environment variables
        self.api_key = os.getenv("CLAUDE_API_KEY")
        if not self.api_key:
            raise ValueError("CLAUDE_API_KEY not found in environment variables. Please add it to .env file.")
        
        self.model = 'claude-3-7-sonnet-20250219'
        self.api_url = 'https://api.anthropic.com/v1/messages'
        
        # Template variable with folder mappings
        self.folder_template = """
folder where I save about Palestine, history:
/Users/stanleytan/Documents/21-notes/08-news/topics
folder where I have saved about learning a language Chinese:
/Users/stanleytan/Documents/21-notes/04-learning/vocabulary/chinese
folder where I am learning about data:
/Users/stanleytan/Documents/11-data
folder where I am learning about statistics:
/Users/stanleytan/onedrive/Documents/classes/statistics
"""

    def get_folder_path(self, query):
        system_prompt = "You are a helpful assistant that helps the user find the appropriate folder path based on their query."
        
        user_prompt = f"""I want to find the appropriate folder path based on my interest or task.

My query: {query}

Here are my folder mappings:
{self.folder_template}

Please return ONLY the most relevant folder path without any explanation or additional text. 
Just the path itself, nothing else. If there is no relevant folder, simply reply 'No matching folder found.'"""

        try:
            # Set up the request headers
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            
            # Set up the request payload
            payload = {
                "model": self.model,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 100
            }
            
            # Make the API request
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                return f"Error: API request failed with status code {response.status_code}. {response.text}"
            
            # Extract the response content
            result = response.json()
            folder_path = result['content'][0]['text'].strip()
            
            return folder_path
            
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    finder = FolderFinder()
    
    print("===== Folder Finder =====")
    print("What do you want to do or learn about?")
    query = input("> ")
    
    print("\nFinding the appropriate folder path...")
    folder_path = finder.get_folder_path(query)
    
    print("\nResult:")
    if not folder_path.startswith("Error") and folder_path != "No matching folder found.":
        print(f"✅ Found matching folder: {folder_path}")
        # Copy the folder path to clipboard
        pyperclip.copy(folder_path)
        print("📋 Path copied to clipboard!")
    else:
        print(f"❌ {folder_path}")
        
if __name__ == "__main__":
    main()
