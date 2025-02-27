import streamlit as st
from openai import OpenAI
import PyPDF2
import docx

# -----------------------------------
# 1. Initialize OpenAI Client (internally)
# -----------------------------------
openai_api_key = "----------"
client = OpenAI(api_key=openai_api_key)

# -----------------------------------
# 2. Helper Functions for Reading PDF/DOCX
# -----------------------------------
def extract_text_from_pdf(file) -> str:
    pdf_reader = PyPDF2.PdfReader(file)
    text_content = []
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text_content.append(page.extract_text())
    return "\n".join(text_content)

def extract_text_from_docx(file) -> str:
    doc_obj = docx.Document(file)
    full_text = []
    for para in doc_obj.paragraphs:
        full_text.append(para.text)
    return "\n".join(full_text)

def count_words(text: str) -> int:
    """Return the approximate number of words in the given text."""
    return len(text.split())

# -----------------------------------
# 3. Streamlit Page Config
# -----------------------------------
st.set_page_config(
    page_title="The Summarizer",
    page_icon="📝"
)

# -----------------------------------
# 4. App Title and Intro
# -----------------------------------
st.title("The Summarizer 📝")
st.write(
    "Upload or paste and let the Summarizer pull out the main ideas for you!"
)

# -----------------------------------
# 5. File Uploader for PDF/DOCX
# -----------------------------------
uploaded_file = st.file_uploader(
    "Upload a PDF or DOCX file (optional)",
    type=["pdf", "docx"]
)

# -----------------------------------
# 6. Text Input
# -----------------------------------
user_text = st.text_area(
    "Or paste your text below (up to 500 words):",
    height=150
)

# -----------------------------------
# 7. Summarize Button
# -----------------------------------
if st.button("Summarize Now!"):
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

    # (b) If no file, use the typed text
    if not extracted_text.strip():
        extracted_text = user_text.strip()

    # (c) Check if we have any text at all
    if not extracted_text:
        st.error("Please either upload a file or type some text to summarize.")
        st.stop()

    # (d) Word limit check
    word_count = count_words(extracted_text)
    if word_count > 500:
        st.error(f"Your text is {word_count} words, which exceeds the 500-word limit. Please shorten it.")
        st.stop()

    # -----------------------------------
    # 8. Call GPT-4o to Summarize (internally)
    # -----------------------------------
    with st.spinner("Summarizing...✍️"):
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",  # Internally uses GPT-4o
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that summarizes text. "
                            "Please provide a concise summary of the user-provided text. "
                            "Respond ONLY with the summary, nothing more."
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Please summarize the following text:\n\n{extracted_text}"
                    }
                ],
                temperature=0.0,
            )

            summary = completion.choices[0].message.content.strip()

            st.success("✨ Here’s your summary:")
            # Use st.code for the built-in copy button
            st.code(summary, language="")

        except Exception as e:
            st.error(f"An error occurred during summarization: {e}")
