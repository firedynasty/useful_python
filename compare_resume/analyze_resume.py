import string
import re
from collections import Counter

# Function to read the resume file
def read_resume(file_path):
    with open(file_path, 'r') as file:
        return file.read()

# Function to extract all words
def extract_words(text):
    # Split by whitespace and convert to lowercase
    words = [word.lower() for word in re.split(r'\s+', text) if word]
    
    # Remove punctuation from each word
    clean_words = []
    for word in words:
        # Remove trailing punctuation
        word = word.strip(string.punctuation)
        if word:  # Skip empty strings
            clean_words.append(word)
    
    return clean_words

# Function to get unique words (no punctuation)
def get_unique_words(words):
    # Create a set of unique words
    unique_words = set(words)
    
    # Remove any remaining punctuation
    punctuation_set = set(string.punctuation)
    
    # Remove words that are just punctuation
    clean_unique_words = {word for word in unique_words if not all(char in punctuation_set for char in word)}
    
    return clean_unique_words

# Define required and desired skills
def check_skills(unique_words):
    # These would typically be defined based on a job description
    required_skills = {
        'python', 'data', 'analytics', 'visualization', 'excel', 'statistics'
    }
    
    desired_skills = {
        'machine learning', 'javascript', 'html', 'css', 'd3', 'api', 
        'sql', 'mongodb', 'tableau', 'hadoop', 'aws', 'git'
    }
    
    # For multi-word skills, we'll need to check the original text
    # but for single words, we can check the unique words set
    matched_required = required_skills.intersection(unique_words)
    matched_desired = desired_skills.intersection(unique_words)
    
    return matched_required, matched_desired

# Function to count word frequencies (for bonus)
def count_word_frequencies(words):
    # Common English stop words
    stop_words = {
        'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 
        'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 
        'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 
        'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 
        'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 
        'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 
        'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 
        'with', 'about', 'against', 'between', 'into', 'through', 'during', 
        'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 
        'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 
        'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 
        'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 
        'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 
        'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 
        'should', 'now'
    }
    
    # Filter out stop words
    filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
    
    # Count frequencies
    word_counts = Counter(filtered_words)
    
    # Return top 10 most common words
    return word_counts.most_common(10)

def main():
    # In a real scenario, you'd use a file path
    # For this example, we'll use a string variable to hold the resume text
    resume_text = """# Frank N. Stein

## Education

* Data Analytics and Visualization Boot Camp Graduate

## Experience

* Creating pivot tables and VBA scripts in Excel.
* Modeling and forecasting data using basic statistics
* Writing python scripts to analyze data sets from files and APIs.
* Social Media Mining using Python
* Working with MySQL and MongoDB databases
* Developing Front-End Web Visualizations using HTML, CSS, Bootstrap, D3, and Leaflet.js
* Using the Tableau Business Intelligence Software
* Performing Big Data Analytics with Hadoop
* Working with Machine Learning algorithms

## Skills

* Microsoft Excel, Python, JavaScript, HTML/CSS, API Interactions, Social Media Mining, SQL, Hadoop, Tableau, Advanced Statistics, Machine Learning, R, Git/Github

## Interests

* Contributing to open-source software
* Data analytics with Python and Pandas
* Designing Data Visualization Web Apps with HTML, CSS, JavaScript, and D3
* Working with Big Data in the cloud using AWS"""
    
    # In a real scenario, you'd use:
    # resume_text = read_resume('resume.txt')
    
    print("Resume Analysis\n" + "="*50)
    
    # Get all words
    all_words = extract_words(resume_text)
    print(f"Total word count: {len(all_words)}")
    
    # Get unique words
    unique_words = get_unique_words(all_words)
    print(f"Unique word count: {len(unique_words)}")
    print("\nSample of unique words:", list(unique_words)[:10])
    
    # Check skills
    matched_required, matched_desired = check_skills(unique_words)
    
    print("\nRequired Skills Found:")
    for skill in matched_required:
        print(f"- {skill}")
    
    print("\nDesired Skills Found:")
    for skill in matched_desired:
        print(f"- {skill}")
    
    # Bonus: Word frequencies
    print("\nTop 10 Word Frequencies (excluding common stop words):")
    for word, count in count_word_frequencies(all_words):
        print(f"- {word}: {count}")

if __name__ == "__main__":
    main()
