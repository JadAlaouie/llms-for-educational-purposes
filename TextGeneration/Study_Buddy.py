from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from BaseApp import BaseApp
import streamlit as st 
from Model_Manager import ModelManager
from Config import PRIMARY_MODEL, SECONDARY_MODEL
if "user_info" not in st.session_state:
    st.session_state.user_info = {
        "category": None,
        "subject": None
    }

if "uploaded_file" not in st.session_state:
     st.session_state.uploaded_file = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "COST" not in st.session_state:
    st.session_state.COST = 0

class StudyBuddy(BaseApp):
    def __init__(self, model_manager, app_name="Study Buddy 🚀", app_slogan="Your Personalized Learning Companion for Smarter Studies 👩🏻‍💻📓✍🏻💡"):
        super().__init__(app_name)
        self.app_slogan = app_slogan
        self.model_manager = model_manager
    
    def welcome_screen(self, app_slogan):
        super().welcome_screen(app_slogan)

    def process_input(self, user_input):
        chain_input = {
            "category": st.session_state.user_info["category"],
            "subject": st.session_state.user_info["subject"],
            "docuemnts": self.process_document(),
            "user_question": user_input
        }

    def display_side(self):
        with st.sidebar:
            selected_category = st.selectbox("Select your level", 
                                            ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
                                             "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12",
                                             "University Student", "Working Professional"])
            selected_subject = st.text_input("Enter subject for assistance 🤗", placeholder="Math, Physics, Biology")
            st.session_state.user_info = {"category": selected_category, "subject": selected_subject}


    def generate_prompt(self):
        prompt_template = ChatPromptTemplate.from_template("""                                              
            
            You are Study Buddy, an educational assistant for {category} students.
            Current subject: {subject}
            Chat history: {chat_history}
            
            **Instructions:**
            - Respond appropriately for a {category} student.
            - Focus on {subject} concepts.
            - Use age-appropriate language add some emojis and easy learning approaches for younger ages which are based on the category.
            - Keep responses concise and educational.
            - For CSV data, analyze trends and patterns.
            - For PDF content, reference specific page sections if needed.
            - If a kid makes a typo correct it in a gentle way.
            
            User's question: {user_question}""")
        
        return prompt_template
    
    
    def handle_input(self):
        
        user_input = st.chat_input("Type your message here", disabled = True if not st.session_state.user_info.get("category") or not st.session_state.user_info.get("subject") else False)
        
    
        if user_input:
            
            st.session_state.chat_history.append(HumanMessage(user_input))
            
            with st.chat_message("Student", avatar="😀"):
                st.markdown(user_input)

            prompt_template = self.generate_prompt()
            
            response, st.session_state.COST = self.model_manager.generate(
                prompt_template,
                {
                "category": st.session_state.user_info["category"],
                "subject": st.session_state.user_info["subject"],
                "chat_history": st.session_state.chat_history, 
                "user_question": user_input
                }
            )   
            print(st.session_state.COST)
            super().display_ai_response(response)

        return user_input
    
def main():
    model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)
    app = StudyBuddy(model_manager)
    app.welcome_screen("")
    app.handle_input()
    app.display_side()

if __name__ == "__main__":
    main()