import re
import string
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd

def extract_skill_patterns_from_job_posting(job_posting_text):
    """
    Extracts technical skills and keywords from a job posting and 
    returns them as regex patterns ready to use.
    
    Args:
        job_posting_text (str): The full text of the job posting
        
    Returns:
        list: A list of regex patterns for skills mentioned in the job posting
    """
    # Common technical skills to look for in any data/tech job posting
    base_skills = [
        "sql", "python", "excel", "tableau", "data analytics", "visualization",
        "reporting", "spreadsheet", "crm", "salesforce", "dashboard", "analysis",
        "analytics", "statistics", "vba", "forecasting", "machine learning",
        "javascript", "html", "css", "api", "mongodb", "mysql", "hadoop", 
        "big data", "r", "git", "github", "d3", "aws", "cloud", "database",
        "data science", "data engineering", "etl", "bi", "business intelligence",
        "snowflake", "redshift", "power bi", "pandas", "numpy", "tensorflow",
        "pytorch", "java", "c++", "c#", "php", "ruby", "scala", "spark", 
        "airflow", "kubernetes", "docker", "linux", "unix", "shell", "bash",
        "rest", "soap", "json", "xml", "azure", "gcp", "google cloud", 
        "data modeling", "data warehouse", "data lake", "data mining",
        "regression", "classification", "nlp", "natural language processing", 
        "computer vision", "deep learning", "ai", "artificial intelligence",
        "nosql", "postgresql", "oracle", "ms office", "microsoft office",
        "word", "powerpoint", "access", "outlook", "looker", "dbt", "metabase",
        "hex", "alteryx", "sas", "spss", "matlab", "power query", "dax",
        "data visualization", "data analysis", "data quality", "data cleansing",
        "data governance", "data management", "agile", "scrum", "kanban",
        "jira", "confluence", "slack", "teams", "google workspace"
    ]
    
    # Extract skill-related sections from the job posting
    skill_sections = []
    
    # Look for sections typically containing skills
    section_headers = [
        "qualifications", "requirements", "skills", "required skills",
        "preferred skills", "must have", "nice to have", "desired skills",
        "what you'll need", "what we're looking for", "technical skills",
        "experience", "expertise", "about you", "what you bring"
    ]
    
    # Convert job posting to lowercase for easier matching
    job_text_lower = job_posting_text.lower()
    
    # Extract sections with skill information
    for header in section_headers:
        if header in job_text_lower:
            start_idx = job_text_lower.find(header)
            # Find the next section header if it exists
            next_section = float('inf')
            for h in section_headers:
                idx = job_text_lower.find(h, start_idx + len(header))
                if idx > start_idx and idx < next_section:
                    next_section = idx
            
            # If we found a next section, extract text up to that point
            if next_section < float('inf'):
                skill_sections.append(job_text_lower[start_idx:next_section])
            else:
                # Otherwise take a chunk of reasonable size (500 chars)
                skill_sections.append(job_text_lower[start_idx:start_idx + 500])
    
    # Combine skill sections into one text
    skill_text = " ".join(skill_sections)
    
    # Look for mentions of specific tools, technologies, and skills
    identified_skills = set()
    
    # Check for each base skill in the job posting
    for skill in base_skills:
        # Look for the skill as a whole word
        if re.search(r'\b' + re.escape(skill) + r'\b', job_text_lower):
            identified_skills.add(skill)
    
    # Look for additional skills using some common patterns
    # Skills often appear after phrases like "proficient in", "experience with", etc.
    skill_indicators = [
        r"proficient in ([\w\s,]+)", 
        r"experience (?:with|in) ([\w\s,]+)",
        r"knowledge of ([\w\s,]+)",
        r"familiar with ([\w\s,]+)",
        r"background in ([\w\s,]+)",
        r"skilled (?:in|with) ([\w\s,]+)"
    ]
    
    for pattern in skill_indicators:
        matches = re.findall(pattern, job_text_lower)
        for match in matches:
            # Split by commas and 'and' to get individual skills
            skills = re.split(r',|\sand\s', match)
            for skill in skills:
                # Clean up the skill
                clean_skill = skill.strip()
                if clean_skill and len(clean_skill) > 1:  # Avoid single characters
                    identified_skills.add(clean_skill)
    
    # Convert identified skills to regex patterns
    skill_patterns = []
    for skill in identified_skills:
        # Replace spaces with \s* to allow for variations
        pattern_skill = skill.replace(" ", r"\s*")
        # Add word boundaries and create raw string pattern
        skill_pattern = r'\b' + pattern_skill + r'\b'
        skill_patterns.append(skill_pattern)
    
    # Make sure ALL base skills are included as patterns, whether found in job posting or not
    for skill in base_skills:
        skill_pattern = r'\b' + skill.replace(" ", r"\s*") + r'\b'
        if skill_pattern not in skill_patterns:
            skill_patterns.append(skill_pattern)
    
    return skill_patterns

class JobMatchAnalyzer:
    def __init__(self, resume_text, job_posting_text):
        """Initialize with resume and job posting text"""
        self.resume_text = resume_text
        self.job_posting_text = job_posting_text
        self.stop_words = self._get_stop_words()
        # Automatically extract skill patterns from the job posting
        self.skill_patterns = extract_skill_patterns_from_job_posting(job_posting_text)
        
    def _get_stop_words(self):
        """Define common stop words to filter out"""
        return {
            'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
            'with', 'about', 'against', 'between', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
            'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then',
            'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
            'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's',
            't', 'can', 'will', 'just', 'don', 'should', 'now', 'of', 'for', 'by',
            'be', 'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'i', 'my',
            'me', 'we', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her',
            'it', 'its', 'they', 'them', 'their', 'who', 'whom'
        }
    
    def clean_text(self, text):
        """Clean text by removing punctuation and converting to lowercase"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        translator = str.maketrans('', '', string.punctuation)
        text = text.translate(translator)
        
        return text
    
    def extract_words(self, text):
        """Extract words from text, removing stop words"""
        clean_text = self.clean_text(text)
        words = [word for word in clean_text.split() if word not in self.stop_words and len(word) > 1]
        return words
    
    def extract_key_skills(self, text):
        """Extract key technical skills using regex patterns"""
        # Now using dynamically generated skill patterns
        skills = []
        clean_text = text.lower()
        
        for pattern in self.skill_patterns:
            matches = re.findall(pattern, clean_text)
            skills.extend(matches)
        
        return skills
    
    def calculate_match_score(self):
        """Calculate how well the resume matches the job posting"""
        # Extract key skills from both documents
        job_skills = Counter(self.extract_key_skills(self.job_posting_text))
        resume_skills = Counter(self.extract_key_skills(self.resume_text))
        
        # Find matching and missing skills
        all_job_skills = set(job_skills.keys())
        all_resume_skills = set(resume_skills.keys())
        
        matching_skills = all_job_skills.intersection(all_resume_skills)
        missing_skills = all_job_skills - all_resume_skills
        
        # Calculate match percentage
        if not all_job_skills:
            return 0, matching_skills, missing_skills, {}
        
        match_percentage = (len(matching_skills) / len(all_job_skills)) * 100
        
        # Create skill importance dictionary
        # Skills mentioned multiple times in job posting are weighted higher
        skill_importance = {skill: count for skill, count in job_skills.items()}
        
        return match_percentage, matching_skills, missing_skills, skill_importance
    
    def analyze_job_requirements(self):
        """Extract and analyze key requirements from the job posting"""
        # Extract sentences containing "required", "must have", "necessary", etc.
        requirement_patterns = [
            r'[^.!?]*\b(required|must have|necessary|essential|qualification)[^.!?]*[.!?]',
            r'[^.!?]*\b(looking for|seeking)[^.!?]*[.!?]',
            r'[^.!?]*\b(proficien|experienc|knowledge|understanding)[^.!?]*[.!?]'
        ]
        
        requirements = []
        for pattern in requirement_patterns:
            matches = re.findall(pattern, self.job_posting_text, re.IGNORECASE)
            requirements.extend(matches)
        
        return requirements
    
    def visualize_match(self):
        """Create visualizations for the match analysis"""
        match_score, matching_skills, missing_skills, skill_importance = self.calculate_match_score()
        
        # Prepare data for visualization
        categories = ['Matching Skills', 'Missing Skills']
        values = [len(matching_skills), len(missing_skills)]
        
        # Create a simple bar chart
        plt.figure(figsize=(10, 6))
        plt.bar(categories, values, color=['green', 'red'])
        plt.title(f'Resume Match Analysis - Overall Score: {match_score:.1f}%')
        plt.xlabel('Categories')
        plt.ylabel('Number of Skills')
        
        # Add text labels
        for i, v in enumerate(values):
            plt.text(i, v + 0.1, str(v), ha='center')
        
        # Save the visualization
        plt.tight_layout()
        plt.savefig('match_analysis.png')
        
        # Return the data for reporting
        return {
            'match_score': match_score,
            'matching_skills': matching_skills,
            'missing_skills': missing_skills,
            'skill_importance': skill_importance
        }
    
    def generate_report(self):
        """Generate a comprehensive report of the analysis"""
        match_score, matching_skills, missing_skills, skill_importance = self.calculate_match_score()
        requirements = self.analyze_job_requirements()
        
        report = {
            'match_score': match_score,
            'matching_skills': list(matching_skills),
            'missing_skills': list(missing_skills),
            'requirements': requirements[:5],  # Show top 5 requirements
            'recommendation': self._get_recommendation(match_score)
        }
        
        return report
    
    def _get_recommendation(self, match_score):
        """Generate a recommendation based on match score"""
        if match_score >= 80:
            return "Strong match! Highly recommended to apply."
        elif match_score >= 60:
            return "Good match. Consider applying with a cover letter highlighting your relevant skills."
        elif match_score >= 40:
            return "Moderate match. Apply but address missing skills in your cover letter."
        else:
            return "Low match. Consider developing missing skills before applying."
        
    def keyword_frequency_analysis(self):
        """Analyze keyword frequencies in both documents"""
        # Extract words
        job_words = self.extract_words(self.job_posting_text)
        resume_words = self.extract_words(self.resume_text)
        
        # Count frequencies
        job_word_freq = Counter(job_words)
        resume_word_freq = Counter(resume_words)
        
        # Get top keywords
        top_job_keywords = job_word_freq.most_common(15)
        top_resume_keywords = resume_word_freq.most_common(15)
        
        return {
            'top_job_keywords': top_job_keywords,
            'top_resume_keywords': top_resume_keywords
        }
    
    def get_skill_patterns(self):
        """Return the extracted skill patterns being used"""
        return self.skill_patterns


# Sample usage
if __name__ == "__main__":
    # In a real scenario, these would be loaded from files
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
    
    job_posting_text = """Clipboard Health

Sales Data Analyst
Clipboard Health • San Francisco, CA • via Greenhouse
Full-time
No Degree Mentioned
Paid time off
Apply on Greenhouse
Apply on Jobilize
Job highlights
Identified by Google from the original job post
Qualifications
We are seeking a highly skilled and motivated Sales Data Analyst to join our Sales Operations team
The ideal candidate will possess a strong background in data analytics, proficiency in spreadsheet formulas and manipulation, and a solid understanding of SQL
Proven experience as a Data Analyst or similar role in a sales-focused environment
Proficiency in spreadsheet software (e.g., Microsoft Excel, Google Sheets) and experience with complex formulas
Strong knowledge of SQL for data extraction and manipulation (there will be a live whiteboarding session should you advance to the interview process)
Experience with Salesforce or other CRM tools
Excellent analytical and problem-solving skills
Strong attention to detail and accuracy in data analysis
Nice to Haves
Familiarity with programming languages, particularly Python
Proficiency in DBT, Snowflake, Metabase, and/or Hex
Ability to work independently and collaboratively in a fast-paced environment
Analytical mindset with a passion for turning data into actionable insights
Proactive and adaptable with a continuous improvement mindset
Strong organizational and time-management skills
Benefits
Do great work that matters for customers who could really use your help
Competitive pay
Unlimited PTO
Fully Remote
Responsibilities
The Sales Data Analyst will play a key role in analyzing sales data, extracting valuable insights, and making our CRM data more actionable to enhance our sales strategies
If you are a data-driven individual with a keen interest in sales analytics and possess the required skills, we invite you to apply and contribute to the success of our sales operations
Analyze and interpret sales data to identify trends, patterns, and opportunities for improvement
Develop and maintain advanced Excel spreadsheets with complex formulas to streamline data analysis processes
Utilize SQL queries to extract and manipulate data from databases for comprehensive analysis
Collaborate with cross-functional teams to understand business requirements and provide data-driven insights
Generate reports and dashboards to visualize key performance indicators (KPIs) and sales metrics
Conduct ad-hoc analyses to support decision-making processes and address specific business challenges"""
    
    # Create analyzer
    analyzer = JobMatchAnalyzer(resume_text, job_posting_text)
    
    # Run analysis
    print("\n=== JOB MATCH ANALYSIS ===\n")
    
    # Calculate match score
    match_score, matching_skills, missing_skills, skill_importance = analyzer.calculate_match_score()
    print(f"Match Score: {match_score:.1f}%")
    
    print("\nMatching Skills:")
    for skill in matching_skills:
        print(f"- {skill}")
    
    print("\nMissing Skills:")
    for skill in missing_skills:
        print(f"- {skill}")
    
    # Generate report
    report = analyzer.generate_report()
    print(f"\nRecommendation: {report['recommendation']}")
    
    # Keyword analysis
    keyword_analysis = analyzer.keyword_frequency_analysis()
    
    print("\nTop Job Posting Keywords:")
    for word, count in keyword_analysis['top_job_keywords'][:10]:
        print(f"- {word}: {count}")
    
    print("\nTop Resume Keywords:")
    for word, count in keyword_analysis['top_resume_keywords'][:10]:
        print(f"- {word}: {count}")
    
    print("\nKey Job Requirements:")
    for req in report['requirements']:
        print(f"- {req.strip()}")
        
    # Print the first 10 skill patterns being used
    print("\nSample of Skill Patterns Used:")
    for pattern in analyzer.get_skill_patterns()[:10]:
        print(f"- {pattern}")
