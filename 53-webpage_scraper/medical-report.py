#act as a medical report and see the query below


from openai import OpenAI
import PyPDF2
import docx
import streamlit as st

class MedicalAssistant:
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
        prompt = f"""Analyze this medical report and answer the following query:
        
Report Text: {text[:2000]}...

Query: {query}

Provide:
1. Direct answer to the query
2. Key medical findings or observations
3. Potential health risks or concerns
4. Recommendations for further action or follow-up
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical assistant skilled in analyzing medical reports, patient records, and clinical studies.",
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
    st.set_page_config(page_title="Medical Assistant", layout="wide")
    st.title("🏥 Medical Report Analyzer")
    
    assistant = MedicalAssistant()
    
    # Sidebar for document upload
    with st.sidebar:
        st.header("Upload Medical Reports")
        uploaded_files = st.file_uploader(
            "Upload medical reports (PDF, DOCX, TXT)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
        )
    
    # Main content area
    if uploaded_files:
        st.write(f"📄 {len(uploaded_files)} reports uploaded")
        
        # Query input
        query = st.text_area(
            "What would you like to know about these reports?",
            placeholder="Example: What are the key findings in this patient's lab results? Are there any potential health risks?",
            height=100,
        )
        
        if st.button("Analyze", type="primary"):
            with st.spinner("Analyzing reports..."):
                # Process each document
                for file in uploaded_files:
                    st.write(f"### Analysis of {file.name}")
                    text = assistant.extract_text(file)
                    
                    # Create tabs for different analyses
                    tab1, tab2, tab3 = st.tabs(
                        ["Main Analysis", "Key Findings", "Health Risks"]
                    )
                    
                    with tab1:
                        assistant.analyze_content(text, query)
                    
                    with tab2:
                        assistant.analyze_content(
                            text, "Extract and summarize key medical findings"
                        )
                    
                    with tab3:
                        assistant.analyze_content(text, "Identify potential health risks")

if __name__ == "__main__":
    main()