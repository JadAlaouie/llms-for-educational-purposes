import streamlit as st
from openai import OpenAI
import PyPDF2
import docx

# Set your OpenAI API key here or set it as an environment variable
openai_api_key = "----------"  # Or get from st.secrets / environment variable
client = OpenAI(api_key=openai_api_key)

def extract_text_from_pdf(file) -> str:
    """Extracts all text from a PDF file object using PyPDF2."""
    pdf_reader = PyPDF2.PdfReader(file)
    text_content = []
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text_content.append(page.extract_text())
    return "\n".join(text_content)

def extract_text_from_docx(file) -> str:
    """Extracts all text from a DOCX file object using python-docx."""
    doc = docx.Document(file)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def count_words(text: str) -> int:
    """Return the approximate number of words in the given text."""
    return len(text.split())

# Streamlit page config
st.set_page_config(
    page_title="The Translator",
    page_icon="🌐"
)

st.title("The Translator🌐")
st.write(
    "Pick a language to translate into, and let the translator do the rest!"
)


uploaded_file = st.file_uploader(
    "Upload a PDF or DOCX file (optional)",
    type=["pdf", "docx"]
)

# 1) Text input
user_text = st.text_area(
    "or Enter your text (up to 500 words):",
    max_chars=None,  # We'll enforce the limit via word count instead of characters
    height=150
)

# 2) Language dropdown
languages = ["Arabic", "French", "Spanish", "German", "Italian", "Japanese"]
target_language = st.selectbox("Choose a language to translate into:", languages)

if st.button("Unleash the Translator!"):
    extracted_text = ""

    # (a) If a file is uploaded, parse it
    if uploaded_file is not None:
        file_type = uploaded_file.name.lower()
        try:
            if file_type.endswith(".pdf"):
                extracted_text = extract_text_from_pdf(uploaded_file)
            elif file_type.endswith(".docx"):
                extracted_text = extract_text_from_docx(uploaded_file)
        except Exception as e:
            st.error(f"Could not read the uploaded file. Error: {e}")
            st.stop()

    # (b) Otherwise, fallback to typed text
    if not extracted_text.strip():
        extracted_text = user_text.strip()

    # (c) Final check: do we have text at all?
    if not extracted_text:
        st.error("Please either upload a file or type some text to translate.")
        st.stop()

    # (d) Word limit check
    word_count = count_words(extracted_text)
    if word_count > 500:
        st.error(f"Your text is {word_count} words, which exceeds the 500-word limit. Please shorten it.")
        st.stop()

    # --------------------------------------
    # 10. Call the model to perform translation
    # --------------------------------------
    with st.spinner("Translating...✍️"):
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful translation assistant. "
                            "Please translate the user-provided text into the specified language. "
                            "Respond ONLY with the translated text."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Please translate the following into {target_language}:\n\n{extracted_text}"
                    }
                ],
                temperature=0.0,
            )
            translation = completion.choices[0].message.content.strip()

            st.success(f"Awesome! Your text in {target_language}:")
            # Using st.code so kids can easily copy with the built-in copy icon
            st.code(translation, language="")

        except Exception as e:
            st.error(f"An error occurred during translation: {e}")
