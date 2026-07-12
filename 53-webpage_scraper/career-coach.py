#what does this do? 
#creates a streamlit app web app that allows you to analyze your resume



from openai import OpenAI
import PyPDF2
import docx
import streamlit as st

class CareerCoach:
    def __init__(self):
        self.client = OpenAI(
            api_key='ollama',
            base_url='http://localhost:11434/v1/'
        )
        self.model = 'deepseek-r1:1.5b'
    
    def extract_text(self, uploaded_file):
        text = ""
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            text = str(uploaded_file.read(), "utf-8")
        return text
    
    def analyze_content(self, text, query):
        prompt = f"""Analyze this resume/career document and answer the following query:
        
Document Text: {text[:2000]}...

Query: {query}

Provide:
1. Direct answer to the query
2. Key strengths and skills identified
3. Areas for improvement or development
4. Specific recommendations for career advancement or resume enhancement
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a career coach and resume expert skilled in analyzing resumes, cover letters, and career documents.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )
            
            result = st.empty()
            collected_chunks = []
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    collected_chunks.append(chunk.choices[0].delta.content)
                result.markdown("".join(collected_chunks))
            
            return "".join(collected_chunks)
        except Exception as e:
            return f"Error: {str(e)}"

def main():
    st.set_page_config(page_title="Career Coach", layout="wide")
    st.title("💼 Resume and Career Document Analyzer")
    
    coach = CareerCoach()
    
    # Sidebar for document upload
    with st.sidebar:
        st.header("Upload Career Documents")
        uploaded_files = st.file_uploader(
            "Upload resumes, cover letters, or other career documents (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
        )
    
    # Main content area
    if uploaded_files:
        st.write(f"📄 {len(uploaded_files)} documents uploaded")
        
        # Query input
        query = st.text_area(
            "What would you like to know about these documents?",
            placeholder="Example: How can I improve my resume? What skills should I highlight? Is my resume ATS-friendly?",
            height=100,
        )
        
        if st.button("Analyze", type="primary"):
            with st.spinner("Analyzing documents..."):
                # Process each document
                for file in uploaded_files:
                    st.write(f"### Analysis of {file.name}")
                    text = coach.extract_text(file)
                    
                    # Create tabs for different analyses
                    tab1, tab2, tab3, tab4 = st.tabs(
                        ["Main Analysis", "Strengths & Skills", "Improvement Areas", "ATS Optimization"]
                    )
                    
                    with tab1:
                        coach.analyze_content(text, query)
                    
                    with tab2:
                        coach.analyze_content(
                            text, "Extract and summarize key strengths, skills, and accomplishments"
                        )
                    
                    with tab3:
                        coach.analyze_content(text, "Identify areas for improvement and development")
                        
                    with tab4:
                        coach.analyze_content(text, "Provide recommendations for ATS optimization and keyword alignment")

if __name__ == "__main__":
    main()
