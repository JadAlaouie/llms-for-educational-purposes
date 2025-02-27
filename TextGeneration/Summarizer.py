import streamlit as st
from BaseApp import BaseApp
import PyPDF2
import docx
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from BaseApp import BaseApp


class Summarizer(BaseApp):

    if "summary_size" not in st.session_state:
        st.session_state.summary_size = 1

    def __init__(self, model_manager, app_name="The Summarizer 📝", app_slogan="Upload or paste and let the Summarizer pull out the main ideas for you!"):
        super().__init__(app_name)
        self.app_slogan = app_slogan
        self.model_manager = model_manager 

    
    def welcome_screen(self, app_slogan):
        super().welcome_screen(app_slogan)

    def extract_text_from_pdf(self, file) -> str:
        pdf_reader = PyPDF2.PdfReader(file)
        text_content = []
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text_content.append(page.extract_text())
        return "\n".join(text_content)

    def extract_text_from_docx(self, file) -> str:
        doc_obj = docx.Document(file)
        full_text = []
        for para in doc_obj.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)
    
    def count_words(self, text: str) -> int:
        try:
            return len(text.split())
        except Exception as e:
            pass

    def generate_prompt(self):
        prompt_template = ChatPromptTemplate.from_template("""

        You are a dedicated summarizer chatbot.
        Your only function is to summarize the text provided by the user.
        You cannot answer questions, provide explanations, or include external information.
        When summarizing, focus solely on condensing the content of the provided text while retaining its essential meaning.
        Users may only request modifications to the summary, such as making it shorter or longer.
        If the user asks for anything outside of summarization, politely remind them that your purpose is to summarize text only and maybe be extra polite and gentle if from the user content you noticed it is for a content for children.
        If the user is greeting you respond politely. 
        The user specifies the summary size 1 paragraph 2 paragraphs etc...
        Text: {user_text}
        chat_history: {chat_history}
        summary_size: {summary_size}
        """)
        return prompt_template

    def handle_input(self):
        extracted_text = ""
        with st.sidebar:
            uploaded_file = st.file_uploader(
                "Upload a PDF or DOCX file (optional)",
                type = ["pdf","docx"]
            )
            summarize_button = st.button("Summarize Now!")
            summary_size = st.text_input("Enter summary size: 1 paragraph, 2 paragraphs ...")
            st.session_state.summary_size = summary_size
            if summarize_button and uploaded_file is not None:
                try:
                    file_type = uploaded_file.name.lower()
                    if file_type.endswith(".pdf"):
                        extracted_text = self.extract_text_from_pdf(uploaded_file)
                    elif file_type.endswith(".docx"):
                        extracted_text = self.extract_text_from_docx(uploaded_file)
                except Exception as e:
                    st.error(f"Could not read the uploaded file. Error: {e}")
                    return 
        user_text = st.chat_input("Or pass your text below (up to 500 words)")
        if user_text:
            extracted_text = user_text 
        
        if extracted_text:
            word_count = self.count_words(extracted_text)
            if word_count > 500:
                st.error(f"Your text is {word_count} words, which exceeds the 500-word limit. Please shorten your text.")
                return 
        
            st.session_state.chat_history.append(HumanMessage(extracted_text))

            with st.chat_message("user", avatar="😀"):
                st.markdown(extracted_text)

            prompt_template = self.generate_prompt()

            response = self.model_manager.generate(
                prompt_template,
                {
                    "user_text": extracted_text,
                    "chat_history": st.session_state.chat_history,
                    "summary_size": st.session_state.summary_size
                }
            )

            super().display_ai_response(response)
            return extracted_text

