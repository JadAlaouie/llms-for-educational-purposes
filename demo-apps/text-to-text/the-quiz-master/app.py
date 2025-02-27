# app.py
import streamlit as st
import PyPDF2
from openai import OpenAI
client = OpenAI(api_key="---------")


# --- Set up the Streamlit UI ---
st.set_page_config(page_title="Quiz Generator", layout="wide")
st.title("📄 AI Quiz Generator")

# Apply custom font style
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono&display=swap');
    html, body, [class*="st-"] {
        font-family: 'Space Mono', monospace;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Sidebar: Settings ---
with st.sidebar:
    st.header("Settings")

    # Education Level Dropdown
    education_level = st.selectbox(
        "Select Education Level",
        ["Grade 1", "Grade 2", "Grade 3","Grade 4","Grade 5","Grade 6","Grade 7","Grade 8","Grade 9","Grade 10","Grade 11","Grade 12", "University Student", "Working Professional"],
        index=12  # Default: University Student
    )

    # Question Type Dropdown
    question_type = st.selectbox(
        "Select Question Type",
        ["True/False", "Multiple Choice", "Open-ended"],
        index=1  # Default: Multiple Choice
    )

    # Number of Questions Slider
    num_questions = st.slider("Number of Questions", min_value=1, max_value=20, value=5)

# --- File Upload and Text Input ---
uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")
text_input = st.text_area("Or paste text manually:")

def extract_text_from_pdf(file) -> str:
    pdf_reader = PyPDF2.PdfReader(file)
    text_content = []
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text_content.append(page.extract_text())
    return "\n".join(text_content)

# --- Generate Quiz ---
if st.button("Generate Quiz"):

    # Get text from PDF or input field
    if uploaded_file:
        document_text = extract_text_from_pdf(uploaded_file)
    elif text_input:
        document_text = text_input
    else:
        st.warning("Please upload a PDF or enter text.")
        st.stop()

    if question_type == "Multiple Choice":
        prompt = f"""
    You are an expert educator. Create a multiple-choice quiz based on the following content.

    - Target Audience: {education_level}
    - Provide {num_questions} questions.
    - Format: First list all questions with four possible answers (A, B, C, D), each answer choice should be on its own separate line.
    - Do NOT place the correct answer immediately after the question. Instead, provide all questions first, then list correct answers in a separate section.
    - End the line immediately after the question and start the possible answers on a new line.
    - Randomly assign the correct answer to A), B), C), or D).
    - Ensure that B) is **less likely** to be the correct answer and distribute correct answers **evenly** across A), B), C), and D). Avoid using B) as the correct answer more than 25% of the time.

    Content:
    {document_text}

    --- OUTPUT FORMAT ---
    ## Questions:
    1. Question 1

       A) Option 1
       B) Option 2
       C) Option 3
       D) Option 4

    2. Question 2

       A) Option 1
       B) Option 2
       C) Option 3
       D) Option 4

    ...

    ## Answers:
    1. (C) Correct Answer 1
    2. (A) Correct Answer 2
    3. (D) Correct Answer 3
    4. (B) Correct Answer 4
    5. (A) Correct Answer 5
    """


    elif question_type == "True/False":
        prompt = f"""
        You are an expert educator. Create a True/False quiz based on the following content.

        - Target Audience: {education_level}
        - Provide {num_questions} statements.
        - Format: First list all statements, then provide answers in a separate section.

        Content:
        {document_text}

        --- OUTPUT FORMAT ---
        ## Questions:
        1. Statement 1
        2. Statement 2
        ...

        ## Answers:
        1. True/False
        2. True/False
        ...
        """

    else:  # Open-ended
        prompt = f"""
        You are an expert educator. Create an open-ended quiz based on the following content.

        - Target Audience: {education_level}
        - Provide {num_questions} open-ended questions.
        - Format: First list all questions, then provide detailed answers in a separate section.

        Content:
        {document_text}

        --- OUTPUT FORMAT ---
        ## Questions:
        1. Question 1
        2. Question 2
        ...

        ## Answers:
        1. Answer 1
        2. Answer 2
        ...
        """

    # Add SYSTEM MESSAGE to enforce randomness of correct answers
    messages = [
        {"role": "system", "content": "Ensure correct answers are randomly distributed among A, B, C, and D. The answer distribution should be even, avoiding favoring any specific letter."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3
    )

    quiz = response.choices[0].message.content
    st.subheader("Generated Quiz")
    st.markdown(quiz)
