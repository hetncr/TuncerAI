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
        except (ResourceExhausted, InternalServerError) as e:
            st.error(f"Attempt {attempt + 1} failed with error: {e}")
            if attempt < retries - 1:
                continue  # Retry on resource exhaustion or internal server error
            else:
                return "Resource exhausted or internal server error. Please try again later."

# Function to extract text from PDF in chunks
def extract_text_from_pdf(uploaded_file, chunk_size=20):
    reader = PdfReader(BytesIO(uploaded_file.read()))
    chunks = []
    text = ''
    for i, page in enumerate(reader.pages):
        text += page.extract_text()
        if (i + 1) % chunk_size == 0:
            chunks.append(text)
            text = ''
    if text:
        chunks.append(text)
    return chunks

# Function to extract text from Word documents
def extract_text_from_word(uploaded_file, chunk_size=50):
    doc = docx.Document(uploaded_file)
    chunks = []
    text = ''
    for i, para in enumerate(doc.paragraphs):
        text += para.text + '\n'
        if (i + 1) % chunk_size == 0:
            chunks.append(text)
            text = ''
    if text:
        chunks.append(text)
    return chunks

# Function to extract text from Excel spreadsheets
def extract_text_from_excel(uploaded_file, chunk_size=100):
    df = pd.read_excel(uploaded_file)
    chunks = []
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i + chunk_size]
        chunks.append(chunk.to_string(index=False))
    return chunks

# Streamlit app with rate limiting logic
st.title("**:blue[HOCALAR AI]**")
st.subheader("**:blue[Beyin Bedava]    :sunglasses:**", divider='rainbow')

# Input for API key
api_key = st.text_input('Google Gemini API anahtarını giriniz:', type='password')

last_call_time = None  # Initialize for rate limiting

# Ensure the API key is entered before proceeding
if api_key:
    # File uploader
    uploaded_file = st.file_uploader('Belgenizi yükleyiniz (PDF, Word, Excel)', type=['pdf', 'docx', 'xlsx'])

    extracted_chunks = []
    if uploaded_file is not None:
        if uploaded_file.type == 'application/pdf':
            extracted_chunks = extract_text_from_pdf(uploaded_file)
        elif uploaded_file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            extracted_chunks = extract_text_from_word(uploaded_file)
        elif uploaded_file.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            extracted_chunks = extract_text_from_excel(uploaded_file)

    # Input for user query
    user_input = st.text_input('Tuncer AI ile belge hakkında iletişime geçin:')

    # Submit button for user query
    if st.button('Submit'):
        if user_input:
            responses = []
            for chunk in extracted_chunks:
                combined_input = f"Document content: {chunk}\n\nUser question: {user_input}"
                response = call_gemini_api(api_key, combined_input, last_call_time)
                last_call_time = time.time()  # Update last call time for rate limiting
                responses.append(response)
                time.sleep(5)  # Delay between requests to avoid rate limits
            st.write('\n\n'.join(responses))
        else:
            st.write('Lütfen sorunuzu ya da mesajınızı giriniz.')
else:
    st.write('Lütfen Google Gemini API anahtarını giriniz.')
