#Yes, exactly. The application presents the AI model (in this case, the locally-hosted "deepseek-r1:1.5b" through Ollama) with a specific prompt that instructs it to act as an economic expert when analyzing the uploaded documents.

from openai import OpenAI
import PyPDF2
import docx
import streamlit as st

class EconomicExpert:
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
        prompt = f"""Analyze this economic report and answer the following query:
        
Report Text: {text[:2000]}...

Query: {query}

Provide:
1. Direct answer to the query
2. Key economic indicators or trends
3. Potential market risks or opportunities
4. Recommendations for strategic action or investment
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an economic expert skilled in analyzing financial reports, market research, and economic studies.",
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
    st.set_page_config(page_title="Economic Expert", layout="wide")
    st.title("📊 Economic Report Analyzer")
    
    expert = EconomicExpert()
    
    # Sidebar for document upload
    with st.sidebar:
        st.header("Upload Economic Reports")
        uploaded_files = st.file_uploader(
            "Upload economic reports (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
        )
    
    # Main content area
    if uploaded_files:
        st.write(f"📄 {len(uploaded_files)} reports uploaded")
        
        # Query input
        query = st.text_area(
            "What would you like to know about these reports?",
            placeholder="Example: What are the key economic trends in this market analysis? Are there any potential investment opportunities?",
            height=100,
        )
        
        if st.button("Analyze", type="primary"):
            with st.spinner("Analyzing reports..."):
                # Process each document
                for file in uploaded_files:
                    st.write(f"### Analysis of {file.name}")
                    text = expert.extract_text(file)
                    
                    # Create tabs for different analyses
                    tab1, tab2, tab3 = st.tabs(
                        ["Main Analysis", "Key Indicators", "Market Opportunities"]
                    )
                    
                    with tab1:
                        expert.analyze_content(text, query)
                    
                    with tab2:
                        expert.analyze_content(
                            text, "Extract and summarize key economic indicators"
                        )
                    
                    with tab3:
                        expert.analyze_content(text, "Identify potential market opportunities")

if __name__ == "__main__":
    main()