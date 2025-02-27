import streamlit as st
import time
import os
from openai import OpenAI
from dotenv import load_dotenv
import shelve
from PyPDF2 import PdfReader

load_dotenv()

BOT_AVATAR = "🤖"
USER_AVATAR = "🤓"

st.write("")
st.write("")
st.write("")
st.write("")
col1,col2,col3 = st.columns([7,10,1], gap="small")
with col2:
    col2_1,col2_2,col2_3 = st.columns([1,1,1], gap="small")
    with col2_1:
        st.image("E:/Zaka 2.0/Engineering/SEEDS/text-to-text/study-buddy/robot.png", width=100)

col1,col2,col3 = st.columns([1,500,1], gap='small')
with col2:
    
        st.write("Hello! My name is xyz, your AI study partner. I'm here to help you with anything related to your academic journey. Whether you need study tips, assistance with assignments, or resources to improve your focus and productivity, I'm here to support you! Feel free to ask about specific subjects, problem-solving strategies, or even how to stay motivated during your studies. The more specific your questions, the better I can help you. How can I assist you today?")

if "user_info" in st.session_state:
    user_info = st.session_state.user_info

if "document" not in st.session_state:
    st.session_state.document = {}

def typing_effect(text, speed=0.1):
    placeholder = st.empty()
    output_text = ""
    for char in text:
        output_text += char 
        placeholder.markdown(f"<h1 style='text-align: center;'>{output_text}</h1>", unsafe_allow_html=True)
        time.sleep(speed)

if "greeting_shown" not in st.session_state:
    st.session_state.greeting_shown = False

if not st.session_state.greeting_shown:
    text = "Hello, buddy!😊 How can I assist you today?"
    typing_effect(text, speed=0.05)
    st.session_state.greeting_shown = True

openai_api_key = "-------------"
client = OpenAI(api_key=openai_api_key)

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

def load_chat_history():
    with shelve.open("chat_history") as db:
        return db.get("messages", [])

def save_chat_history(messages):
    with shelve.open("chat_history") as db:
        db["messages"] = messages


st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")
st.write("")

file = st.file_uploader("Attach pdf file", type=["pdf"], accept_multiple_files=False, label_visibility="collapsed")
if file:
    try:
        pdf_reader = PdfReader(file)
        extracted_text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_text += page_text 
            else:
                st.markdown('<p style="color: red; font-size: 20px;">Failed to extract text from pdf.</p>', unsafe_allow_html=True)
        
        if extracted_text:
            st.markdown('<p style="color: green; font-size: 20px;">PDF file uploaded and text extracted successfully!</p>', unsafe_allow_html=True)
            st.session_state.document.update({"pdf": extracted_text})
        else:
            st.markdown('<p style="color: red; font-size: 20px;">No text found in the uploaded PDF!</p>', unsafe_allow_html=True)
    
    except Exception as e:
        st.markdown(f'<p style="color: red; font-size: 20px;">Error processing PDF: {str(e)}</p>', unsafe_allow_html=True)

with st.sidebar:
    if st.button("Delete Chat History"):
        st.session_state.messages = []
        save_chat_history([])

if "messages" not in st.session_state:
    prompt = """You are my study buddy, designed to help me stay focused, improve my productivity, and assist me with various tasks and suggest resources online. Based on my current role, you will adapt your advice and responses to suit my needs. Below is my category and the topic I am struggling with, and I would like you to tailor your suggestions accordingly:
    
    Topic: {topic}
    Category: {category}
    
    1. For a University Student: Offer academic support, time management tips, and suggestions for balancing assignments and extracurriculars. Be ready to discuss specific course-related topics and provide study strategies to improve focus during lectures, revision, and exams.
    
    2. For a School Student: Based on their grade (grade 1, grade 2, grade 3, etc...). Help with homework, exam preparation, and understanding school subjects. Offer motivation to stay organized and manage time effectively between schoolwork, hobbies, and social activities. Provide study tips and assistance with specific topics.
    
    3. For a Working Professional: Focus on career development, work-life balance, professional skills enhancement, and time management strategies. Offer guidance on improving productivity at work, handling stress, and continuing education or self-improvement alongside professional responsibilities.
    
    Feel free to ask me for any clarification on the current tasks I'm focusing on, and I'll give you more context about my day-to-day activities.
    
    The user could also be providing documents or text Document: {document} """.format(
        topic=st.session_state.user_info.get("topic"), 
        category=st.session_state.user_info.get("category"),
        document=st.session_state.document.get("pdf")
    )
    
    st.session_state.messages = [{"role": "system", "content": prompt}]
    st.session_state.messages.extend(load_chat_history())

for message in st.session_state.messages:
    if message["role"] != "system":
        avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

if prompt := st.chat_input("How can I help?"):
    user_message = f"The user uploaded this PDF text: /n{st.session_state.document['pdf']}/n/n{prompt}" if 'pdf' in st.session_state.document else prompt
    
    st.session_state.messages.append({"role": "user", "content": user_message})
    
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)
    
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        message_placeholder = st.empty()
        full_response = ""
        
        for response in client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=st.session_state["messages"],
            stream=True,
        ):
            full_response += response.choices[0].delta.content or ""
            message_placeholder.markdown(full_response + "|")
        
        message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    save_chat_history(st.session_state.messages)
