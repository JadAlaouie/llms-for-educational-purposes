import streamlit as st
from openai import OpenAI
import PyPDF2
import docx

# --------------------------
# 1) Initialize OpenAI Client
# --------------------------
openai_api_key = "-----------"
client = OpenAI(api_key=openai_api_key)

# --------------------------
# 2) Functions to read PDF/DOCX
# --------------------------
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
    return len(text.split())

# --------------------------------
# 3) Streamlit Page Config
# --------------------------------
st.set_page_config(
    page_title="The Summarizer",
    page_icon="📝"
)

st.title("The Summarizer 📝")
st.write(
    "Enter (or paste) up to **300 words** of text in the box below, "
    "or upload a file via the small button on the right—then click **Summarize**!"
)

# ------------------------------------------------------
# 4) Side-by-Side Columns: Text Area (left), Uploader (right)
# ------------------------------------------------------
col_text, col_upload = st.columns([4, 1], gap="small")

with col_text:
    # This is the "big" text area
    user_text = st.text_area("Type or paste text here:", height=150)

with col_upload:
    # A smaller area for file uploading
    st.write("Or upload a file:")
    uploaded_file = st.file_uploader(
        label="",  # Hide label text
        type=["pdf", "docx"]
    )

# --------------------------
# 5) Summarize Button
# --------------------------
if st.button("Summarize"):
    extracted_text = ""

    # (a) If a file is uploaded, extract text from it
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

    # (b) If no file or file has no text, use user_text
    if not extracted_text.strip():
        extracted_text = user_text.strip()

    # (c) Check if we have any text at all
    if not extracted_text:
        st.error("Please either upload a file or type some text to summarize.")
        st.stop()

    # (d) Word limit check (300 words)
    total_words = count_words(extracted_text)
    if total_words > 300:
        st.error(f"Your text is {total_words} words, exceeding the 300-word limit.")
        st.stop()

    # --------------------------
    # 6) Summarize with GPT-4o
    # --------------------------
    with st.spinner("Summarizing...✍️"):
        try:
            completion = client.chat.completions.create(
                model="gpt-4o",  # Internally using GPT-4
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
                        "content": f"Summarize this for me:\n\n{extracted_text}"
                    }
                ],
                temperature=0.0,
            )
            summary = completion.choices[0].message.content.strip()

            st.success("✨ Here’s your summary:")
            st.code(summary, language="")
        except Exception as e:
            st.error(f"An error occurred during summarization: {e}")
