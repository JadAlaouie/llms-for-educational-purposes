from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import streamlit as st
import PyPDF2
import docx
import pandas as pd
import base64
from Model_Manager import ModelManager
from Config import PRIMARY_MODEL, SECONDARY_MODEL, Images_MODEL
from dotenv import load_dotenv
from PIL import Image
import io

load_dotenv()

# 3.5 sonnet for images 
# 3 haiku for text 

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_doc" not in st.session_state:
    st.session_state.uploaded_doc = None
if "original_image" not in st.session_state:
    st.session_state.original_image = None
if "image_summary" not in st.session_state:
    st.session_state.image_summary = None

def welcome_screen():
    st.title("Document Analysis AI")

def handle_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    return "\n".join([page.extract_text() for page in pdf_reader.pages])

def handle_docx(docx_file):
    doc = docx.Document(docx_file)
    return "\n".join([para.text for para in doc.paragraphs])

def encode_image(uploaded_file):
    img = Image.open(uploaded_file)
    img = img.convert("RGB") 
    img = img.resize((1024, 1024))  
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=75)  
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def process_uploaded_file(uploaded_file):
    file_type = uploaded_file.name.split(".")[-1].lower()
    content = None
    if file_type in ["jpg", "jpeg", "png"]:
        st.session_state.original_image = uploaded_file.getvalue()
        content = encode_image(uploaded_file)
    elif file_type == "pdf":
        content = handle_pdf(uploaded_file)
    elif file_type == "docx":
        content = handle_docx(uploaded_file)
    elif file_type == "csv":
        content = pd.DataFrame(uploaded_file).to_string()
    return {
        "type": file_type,
        "name": uploaded_file.name,
        "content": content
    }

def handle_image_query(user_input, image_content):
    model = ModelManager.get_model(PRIMARY_MODEL)
    content = [
        {"type": "text", "text": "Summarize this image before answering the query."},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_content}"}},
        {"type": "text", "text": user_input}
    ]
    
    try:
        summary_response = model.invoke([HumanMessage(content=content)]).content
        
        st.session_state.image_summary = summary_response
        
        query_prompt = ChatPromptTemplate.from_template("""
            {summary}
            Answer the following query in details if needed (don't state that you are summarizing but rather you know the info): {query}
            """)
        
        chain = query_prompt | ModelManager.get_model(PRIMARY_MODEL)
        return chain.invoke({"summary": summary_response, "query": user_input}).content
    except Exception as e:
        print(f"Primary model failed: {e}. Switching to secondary model...")
        secondary_model = ModelManager.get_model(Images_MODEL)
        return secondary_model.invoke([HumanMessage(content=content)]).content

def handle_text_query(user_input, doc_content):
    prompt = ChatPromptTemplate.from_template("""
        Analyze this document based on the user's query:
        Document Content:
        {content}
        Query: {query}
        Provide detailed insights and answer any specific questions.
    """)
    
    chain = prompt | ModelManager.get_model(PRIMARY_MODEL)
    return chain.invoke({"content": doc_content, "query": user_input}).content

welcome_screen()

with st.sidebar:
    uploaded_file = st.file_uploader(
        "Upload Document", 
        type=["pdf", "docx", "csv", "jpg", "jpeg", "png"]
    )
    if uploaded_file:
        st.session_state.uploaded_doc = process_uploaded_file(uploaded_file)
    
    if st.button("Clear Document"):
        st.session_state.uploaded_doc = None
        st.session_state.original_image = None
        st.session_state.image_summary = None
        st.rerun()

for msg in st.session_state.chat_history:
    role = "user" if isinstance(msg, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.write(msg.content)

if user_input := st.chat_input("Ask about your document..."):
    st.session_state.chat_history.append(HumanMessage(content=user_input))
    
    response = ""
    if st.session_state.uploaded_doc:
        doc = st.session_state.uploaded_doc
        try:
            if doc["type"] in ["jpg", "jpeg", "png"]:
                response = handle_image_query(user_input, doc["content"])
            else:
                response = handle_text_query(user_input, doc["content"])
        except Exception as e:
            response = f"Error processing document: {str(e)}"
    else:
        prompt = ChatPromptTemplate.from_template("{query}")
        chain = prompt | ModelManager.get_model(PRIMARY_MODEL)
        response = chain.invoke({"query": user_input}).content
    
    st.session_state.chat_history.append(AIMessage(content=response))
    st.rerun()