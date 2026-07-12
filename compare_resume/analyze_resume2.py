import re
import string
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd

class JobMatchAnalyzer:
    def __init__(self, resume_text, job_posting_text):
        """Initialize with resume and job posting text"""
        self.resume_text = resume_text
        self.job_posting_text = job_posting_text
        self.stop_words = self._get_stop_words()
        
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
        # Define patterns for common technical skills and tools
        skill_patterns = [
            r'\bsql\b', r'\bpython\b', r'\bexcel\b', r'\btableau\b', 
            r'\bdata\s*analytics\b', r'\bvisualization\b', r'\breporting\b',
            r'\bspreadsheet\b', r'\bcrm\b', r'\bsalesforce\b', r'\bdashboard\b',
            r'\banalysis\b', r'\banalytics\b', r'\bstatistics\b', r'\bvba\b',
            r'\bforecasting\b', r'\bmachine\s*learning\b', r'\bjavascript\b',
            r'\bhtml\b', r'\bcss\b', r'\bapi\b', r'\bmongodb\b', r'\bmysql\b',
            r'\bhadoop\b', r'\bbig\s*data\b', r'\br\b', r'\bgit\b', r'\bgithub\b',
            r'\bd3\b', r'\baws\b', r'\bcloud\b', r'\bdbt\b', r'\bsnowflake\b',
            r'\bmetabase\b', r'\bhex\b'
        ]
        
        # Extract skills
        skills = []
        clean_text = text.lower()
        
        for pattern in skill_patterns:
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
