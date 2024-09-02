import streamlit as st
import google.generativeai as genai
from io import BytesIO
from PyPDF2 import PdfReader
import docx
import pandas as pd
import time
from google.api_core.exceptions import ResourceExhausted, InternalServerError

# Function to call the Google Gemini AI API
def call_gemini_api(api_key, user_input):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.0-pro-latest')
    
    retries = 3
    for attempt in range(retries):
        try:
            response = model.generate_content(user_input)
            content = response.candidates[0].content.parts[0].text
            return content
        except (AttributeError, IndexError):
            return "Failed to extract content from the AI response."
        except (ResourceExhausted, InternalServerError):
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                return "Resource exhausted or internal server error. Please try again later."

# Function to extract text from PDF using PdfReader
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(BytesIO(uploaded_file.read()))
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to extract text from Word
def extract_text_from_word(uploaded_file):
    doc = docx.Document(uploaded_file)
    text = '\n'.join([para.text for para in doc.paragraphs])
    return text

# Function to extract text from Excel
def extract_text_from_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    text = df.to_string(index=False)
    return text

# Streamlit app
st.title('TUNCER AI - YAPAY ZEKA ')

# Input for API key
api_key = st.text_input('Enter your Google Gemini API key:', type='password')

# Ensure the API key is entered before proceeding
if api_key:
    # File uploader
    uploaded_file = st.file_uploader('Upload a document (PDF, Word, Excel)', type=['pdf', 'docx', 'xlsx'])

    extracted_text = ''
    if uploaded_file is not None:
        if uploaded_file.type == 'application/pdf':
            extracted_text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            extracted_text = extract_text_from_word(uploaded_file)
        elif uploaded_file.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            extracted_text = extract_text_from_excel(uploaded_file)

    # Input for user query
    user_input = st.text_input('Ask something to the AI about the document:')

    # Submit button for user query
    if st.button('Submit'):
        if user_input:
            combined_input = f"Document content: {extracted_text}\n\nUser question: {user_input}"
            response = call_gemini_api(api_key, combined_input)
            st.write('Yapay Zeka Yanıtı:', response)
        else:
            st.write('Please enter a query.')
else:
    st.write('Please enter your Google Gemini API key.')

