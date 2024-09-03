import streamlit as st
import google.generativeai as genai
from io import BytesIO
from PyPDF2 import PdfReader
import docx
import pandas as pd
import time
from google.api_core.exceptions import ResourceExhausted, InternalServerError

# Function to call the Google Gemini AI API with rate limiting
def call_gemini_api(api_key, user_input, last_call_time=None):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')

    retries = 3
    min_delay = 2  # Minimum delay (seconds) between retries
    max_delay = 60  # Maximum delay (seconds) between retries

    for attempt in range(retries):
        if last_call_time is not None:
            delay = min(max_delay, 2 ** attempt * (time.time() - last_call_time))
            time.sleep(delay)  # Implement exponential backoff

        try:
            response = model.generate_content(user_input)
            content = response.candidates[0].content.parts[0].text
            return content
        except (AttributeError, IndexError):
            return "Failed to extract content from the AI response."
        except (ResourceExhausted, InternalServerError):
            if attempt < retries - 1:
                continue  # Retry on resource exhaustion or internal server error
            else:
                return "Resource exhausted or internal server error. Please try again later."

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(BytesIO(uploaded_file.read()))
    text = ''
    for page in reader.pages:
        text += page.extract_text()
    return text

# Function to extract text from Word documents
def extract_text_from_word(uploaded_file):
    doc = docx.Document(uploaded_file)
    text = '\n'.join([para.text for para in doc.paragraphs])
    return text

# Function to extract text from Excel spreadsheets
def extract_text_from_excel(uploaded_file):
    df = pd.read_excel(uploaded_file)
    text = df.to_string(index=False)
    return text

# Streamlit app with rate limiting logic
st.title("**:blue[HOCALAR AI]**")
st.subheader("**:blue[Beyin Bedava]    :sunglasses:**", divider='rainbow')

# Input for API key
api_key = st.text_input('Google Gemini API anahtarını giriniz:', type='password')

last_call_time = None  # Initialize for rate limiting

# Ensure the API key is entered before proceeding
if api_key:
    # File uploader
    uploaded_file = st.file_uploader('Belgenizi yükleyiniz (PDF, Word, Excel)', type=['pdf', 'docx', 'xlsx'])

    extracted_text = ''
    if uploaded_file is not None:
        if uploaded_file.type == 'application/pdf':
            extracted_text = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            extracted_text = extract_text_from_word(uploaded_file)
        elif uploaded_file.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            extracted_text = extract_text_from_excel(uploaded_file)

    # Input for user query
    user_input = st.text_input('Tuncer AI ile belge hakkında iletişime geçin:')

    # Submit button for user query
    if st.button('Submit'):
        if user_input:
            combined_input = f"Document content: {extracted_text}\n\nUser question: {user_input}"
            response = call_gemini_api(api_key, combined_input, last_call_time)
            last_call_time = time.time()  # Update last call time for rate limiting
            st.write(response)
        else:
            st.write('Lütfen sorunuzu ya da mesajınızı giriniz.')
else:
    st.write('Lütfen Google Gemini API anahtarını giriniz.')
