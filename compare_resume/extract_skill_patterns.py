import re  # Add this import at the top of the file

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

# Example usage
if __name__ == "__main__":
    job_posting = """
    Data Quality Analyst
    Tatari • San Francisco, CA • via Tatari
    Full-time
    Health insurance
    Paid time off
    Apply on Tatari
    Apply on ZipRecruiter
    Apply directly on Wellfound
    Apply on Adzuna
    Apply on Simplify
    Apply on Monster
    Apply on Unanimous Capital Job Board
    Apply on Startup Jobs
    Job highlights
    Identified by Google from the original job post
    Qualifications
    * Bachelor's in a technical field (e.g., Computer Science, Mathematics, Physics)
    * 1+ year of relevant work experience, but also open to new grads
    * Intermediate to advanced experience in Data Manipulation Software (e.g., SQL, Python, Pandas)
    * Steadfast focus on the details, while keeping strategic priorities top-of-mind
    * Radiate positivity and possess a "can-do" attitude
    * Strong presentation skills, with the ability to translate data into business insights
    * A quick learner, with the ability to work independently in a fast-paced environment; adaptability and a strong self-teaching ethic are highly valued
    * Strong strategic thinking capabilities and project management skills
    * Proven passion for the data quality discipline
    * Extremely meticulous in approach to work
    * Outstanding attention to detail
    * Advanced degree in a technical field
    * Experience with reporting tools (such as Tableau, Looker, etc.)
    * Ability to manipulate, analyze, and interpret large amounts of data and to organize findings and translate into actionable insights using original or innovative techniques
    """
    
    skill_patterns = extract_skill_patterns_from_job_posting(job_posting)
    
    print("Extracted Skill Patterns:")
    for pattern in skill_patterns:
        print(f"- {pattern}")
