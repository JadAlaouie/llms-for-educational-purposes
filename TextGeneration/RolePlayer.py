from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from BaseApp import BaseApp
import streamlit as st 
from Model_Manager import ModelManager

# select the role --> dropdown menu 
# and prompt 



if "user_choice" not in st.session_state:
    st.session_state.user_choice = {
        "role": None
    }


class RolePlayer(BaseApp):
    def __init__(self, model_manager, app_name="Role Player", app_slogan="🎭 Role Player: Adapting, Guiding, and Inspiring—One Role at a Time!"):
        super().__init__(app_name)
        self.app_slogan = app_slogan
        self.model_manager = model_manager
    
    def welcome_screen(self, app_slogan):
        super().welcome_screen(app_slogan)

    
    def process_input(self, user_input):
        chain_input = {
            "role": st.session_state.user_choice["role"],
            "chat_history": st.session_state.chat_history,
            "documents": self.process_document(),
            "user_question": user_input
        }

    def display_side(self):
        with st.sidebar:
            roles_with_emojis = st.selectbox("Select Role",["Science Teacher 🧪","Math Teacher ➗","Career Counselor 💼","Teacher 📝","Personal Trainer 💪","5-Year-Old Kid 🧸","Doctor 🩺"])
            st.session_state.user_choice = {"role": roles_with_emojis}
            uploaded_file = st.file_uploader("Upload a file",["pdf","csv","docx"], accept_multiple_files=False, disabled=True if not st.session_state.user_choice["role"] else False)
            st.session_state.uploaded_file = uploaded_file


    def generate_prompt(self):
        prompt_template = ChatPromptTemplate.from_template("""                                              
            
            You are a dynamic and engaging chatbot called Role Player 🎭, designed to adapt to various personalities and roles. Your main purpose is to assist, educate, and entertain users by fully embodying the following role: {role}
            When responding to users:
            Chat history: {chat_history}
            Tailor your language, tone, and expertise based on the role they select.
            For example, as a Science Teacher, provide detailed and engaging scientific explanations. As a 5-Year-Old Kid, keep your tone playful, curious, and simple.
            Use your emoji as a fun identifier in your responses to reinforce your role.
            Ensure your responses are concise, helpful, and aligned with the user's expectations for the selected role.
            Be empathetic, approachable, and proactive in suggesting resources or advice within your role's domain.
            Your ultimate goal is to make every interaction memorable, informative, and delightful by bringing each role to life authentically and dynamically based on user question {user_question}.
            Document : {documents}
        """)
        
        return prompt_template
    
    
    def handle_input(self):
        
        user_input = st.chat_input("Type your message here", disabled = True if not st.session_state.user_choice["role"]  else False)
        
        document_content = super().upload(st.session_state.uploaded_file)
        
        if user_input:
            
            st.session_state.chat_history.append(HumanMessage(user_input))
            
            with st.chat_message("Student", avatar="😀"):
                st.markdown(user_input)

            latest_document = document_content
            prompt_template = self.generate_prompt()
            
            response = self.model_manager.generate(
                prompt_template,
                {
                "role": st.session_state.user_choice["role"],
                "chat_history": st.session_state.chat_history, 
                "documents": latest_document,
                "user_question": user_input
                }
            )   
                     
            super().display_ai_response(response)

        return user_input, document_content 
