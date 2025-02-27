import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
import pandas as pd 
import os 
from io import BytesIO
from dotenv import load_dotenv
import time 
import docx 

class BaseApp:
    
    def __init__(self, app_name):
        self.name = app_name
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1000,
            chunk_overlap = 200
        ) 

    def process_document(self):
        return "\n".join(st.session_state.documents)
        
    def initialize(self):
        print(f"{self.app} is initializing...")

    

    def welcome_screen(self, bot_slogan=None):
        st.markdown(f"""
            <div style="text-align: center;">
            <h1>{self.name}</h1>  {bot_slogan}
            </div>
            """, unsafe_allow_html=True)
    
    def upload(self, uploaded_file):
        document_content = ""
    
        if uploaded_file:        
            st.session_state.documents = []

            if uploaded_file.name.lower().endswith("pdf"):
                pdf_bytes = uploaded_file.read()
                pdf_stream = BytesIO(pdf_bytes)
                pdf_reader = PdfReader(pdf_stream)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size = 1000,
                    chunk_overlap = 200
                )    
                text_chunks = splitter.split_text(text)
                st.session_state.documents.append({
                    "name": uploaded_file.name,
                    "type": "pdf",
                    "content": text_chunks
                    }
                )
                document_content = "\n".join(text_chunks)
            
            elif uploaded_file.name.lower().endswith(".csv"):
                csv_df = pd.read_csv(uploaded_file)
                csv_text = csv_df.to_string(index=False)
                st.session_state.documents.append({
                        "name": uploaded_file.name,
                        "type": "csv",
                        "content": csv_text
                        }
                    )
                document_content = csv_text

            elif uploaded_file.name.lower().endswith(".docx"):
                doc = docx.Document(uploaded_file)
                fulltext = []
                for para in doc.paragraphs:
                    fulltext.append(para.text)
                document_content = '\n'.join(fulltext)
                st.session_state.documents.append({
                    "name": uploaded_file.name,
                    "type": "docx",
                    "content": document_content
                })

        return document_content 
    
    def run_model(self, model, prompt_template):
        self.chain = prompt_template | model | StrOutputParser()
        return self.chain  

    def display_messages(self):
        for message in st.session_state.chat_history:
            if isinstance(message, HumanMessage):
                with st.chat_message("User", avatar="😀"):
                    st.markdown(message.content)
            elif isinstance(message, AIMessage):
                with st.chat_message("AI", avatar="🤖"):
                    st.markdown(message.content)

    def display_ai_response(self, ai_response):
        with st.chat_message("AI", avatar="🤖"):
            response_placeholder = st.empty()
            full_response = ""
        for chunk in ai_response.split(" "):
            full_response += chunk + " "
            response_placeholder.markdown(full_response + "▌")
            time.sleep(0.05)
        response_placeholder.markdown(full_response)
        st.session_state.chat_history.append(AIMessage(full_response))