from openai import OpenAI
import pyperclip
import os

class FolderFinder:
    def __init__(self):
        self.client = OpenAI(
            api_key='ollama',
            base_url='http://localhost:11434/v1/'
        )
        self.model = 'deepseek-r1:1.5b'
        
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
        # First try keyword matching directly - it's more reliable
        keyword_result = self.keyword_match(query)
        if keyword_result != "No matching folder found.":
            return keyword_result
            
        # If keyword matching fails, try the LLM approach
        prompt = f"""I want to find the appropriate folder path based on my interest or task.

My query: {query}

Here are my folder mappings:
{self.folder_template}

Based on my query about "{query}", return ONLY the single most relevant folder path from the exact options listed above.
Return the complete path exactly as written in the mapping, including all slashes and formatting.
Do not add any explanation or additional text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that helps the user find the appropriate folder path based on their query.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            
            # Extract the response content and clean it up
            raw_response = response.choices[0].message.content.strip()
            
            # If empty response or very short, return keyword result
            if len(raw_response) < 5:
                return keyword_result
                
            # If the response contains a thinking process or other text,
            # try to extract just the path by looking for the last line
            lines = raw_response.split('\n')
            folder_path = lines[-1].strip()
            
            # Check if the folder path looks valid (contains '/' or '\')
            if '/' not in folder_path and '\\' not in folder_path:
                return keyword_result
            
            return folder_path
            
        except Exception as e:
            # In case of any errors, fall back to keyword matching
            return keyword_result
            
    def keyword_match(self, query):
        """Match query with folder descriptions using keywords"""
        query = query.lower()
        
        # Define keywords for each folder path
        paths = {
            "/Users/stanleytan/onedrive/Documents/classes/statistics": ["statistics", "stat", "stats", "statistic", "probability", "math"],
            "/Users/stanleytan/Documents/11-data": ["data", "database", "dataset", "analytics", "analysis"],
            "/Users/stanleytan/Documents/21-notes/04-learning/vocabulary/chinese": ["chinese", "mandarin", "language", "vocabulary", "learning language"],
            "/Users/stanleytan/Documents/21-notes/08-news/topics": ["palestine", "history", "news", "current events", "topics"]
        }
        
        # Check for direct matches in the query
        for path, keywords in paths.items():
            for keyword in keywords:
                if keyword in query:
                    return path
        
        # If no direct match, try to find the most relevant path
        best_match = None
        best_score = 0
        
        for path, keywords in paths.items():
            for keyword in keywords:
                # Check for partial matches
                for word in query.split():
                    if word in keyword or keyword in word:
                        score = len(keyword) / (len(word) + 0.1)  # Avoid division by zero
                        if score > best_score:
                            best_score = score
                            best_match = path
        
        if best_match and best_score > 0.3:  # Threshold for a reasonable match
            return best_match
        
        # Default fallback
        return "No matching folder found."

def main():
    finder = FolderFinder()
    
    print("===== Folder Finder =====")
    print("What do you want to do or learn about?")
    query = input("> ")
    
    print("\nFinding the appropriate folder path...")
    folder_path = finder.get_folder_path(query)
    
    print("\nResult:")
    if folder_path != "No matching folder found.":
        print(f"✅ Found matching folder: {folder_path}")
        # Copy the folder path to clipboard
        pyperclip.copy(folder_path)
        print("📋 Path copied to clipboard!")
    else:
        print("❌ No matching folder found.")
        
if __name__ == "__main__":
    main()