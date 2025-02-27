import streamlit as st
from openai import OpenAI
import PyPDF2
import docx
import streamlit as st
from BaseApp import BaseApp
import PyPDF2
import docx
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from BaseApp import BaseApp
from Config import PRIMARY_MODEL, SECONDARY_MODEL
from Model_Manager import ModelManager

if "COST" not in st.session_state:
    st.session_state.COST = 0

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

class Translator(BaseApp):

    def __init__(self, model_manager, app_name="The Translator 🌐", app_slogan="Pick a language to translate into, and let the translator do the rest! 🌐"):
        super().__init__(app_name)
        self.app_slogan = app_slogan 
        self.model_manager = model_manager 
        self.tokens = {
            "input_tokens": 0,
            "response_tokens":0,
            "total_tokens_per_prompt":0
        }

    
    def welcome_screen(self, app_slogan):
        super().welcome_screen(app_slogan)
    

    def extract_text_from_pdf(self, file) -> str:
        """Extracts all text from a PDF file object using PyPDF2."""
        pdf_reader = PyPDF2.PdfReader(file)
        text_content = []
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text_content.append(page.extract_text())
        return "\n".join(text_content)

    def extract_text_from_docx(self,file) -> str:
        """Extracts all text from a DOCX file object using python-docx."""
        doc = docx.Document(file)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return "\n".join(full_text)

    def count_words(self, text: str) -> int:
        try:
            return len(text.split())
        except Exception as e:
            pass 
    
    def generate_prompt(self):
        prompt_template = ChatPromptTemplate.from_template("""
            You are a professional multilingual translator specializing in providing accurate and contextually appropriate translations between languages.
            Your sole responsibility is to translate the provided text from the source language to the target language as specified by the user.
            Do not provide explanations, interpretations, or additional comments—only the translated text.
            Ensure that the translation maintains the tone, style, and meaning of the original text.
            If no target language is specified, politely ask the user to specify it.
            If language is not arabic or french or english or deutsch don't translate it and mention that i can only translate these languages for now politely because you are a chatbot for kids.
            User Text: {user_text}
            Language: {chosen_language}
            chat_history: {chat_history}
        """)
        return prompt_template

    def handle_input(self):
        extracted_text = ""
        with st.sidebar:
            uploaded_file = st.file_uploader(
                "Upload a PDF or DOCX file (optional)",
                type = ["pdf","docx"]
            )
        
            options = ["None - Select a language","English","Français","العربية","Deutsch"]
            selected_language = st.selectbox(label="Select Language",options=options)
               
            translate_button = st.button("Translate Now!", disabled = selected_language == options[0])
            if translate_button and uploaded_file is not None:
                try:
                    file_type = uploaded_file.name.lower()
                    if file_type.endswith(".pdf"):
                        extracted_text = self.extract_text_from_pdf(uploaded_file)
                    elif file_type.endswith(".docx"):
                        extracted_text = self.extract_text_from_docx(uploaded_file)
                except Exception as e:
                    st.error(f"Could not read the uploaded file. Error: {e}")
                    return 
        user_text = st.chat_input("Or pass your text below (up to 500 words)", disabled = selected_language == options[0])
        if user_text:
            extracted_text = user_text
        
        if extracted_text:
            word_count = self.count_words(extracted_text)
            if word_count > 500:
                st.error(f"Your test is {word_count} words, which exceeds the 500-word limit. Please shorten your text")
                return 
            
            st.session_state.chat_history.append(HumanMessage(extracted_text))

            with st.chat_message("user", avatar="😀"):
                st.markdown(extracted_text)
            
            prompt_template = self.generate_prompt()

            response, st.session_state.COST = self.model_manager.generate(
                prompt_template, 
                {
                    "user_text": extracted_text,
                    "chat_history": st.session_state.chat_history,
                    "chosen_language": selected_language
                }
            )
            print(st.session_state.COST)
            super().display_ai_response(response)
            return extracted_text

def main():
    model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)
    app = Translator(model_manager)
    app.welcome_screen('')
    app.handle_input()
    app.display_messages()

if __name__ == "__main__":
    main()