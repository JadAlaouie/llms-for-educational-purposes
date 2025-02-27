from langchain_core.messages import HumanMessage,AIMessage
from langchain_core.prompts import ChatPromptTemplate
from BaseApp import BaseApp
import streamlit as st 
from Model_Manager import ModelManager
from Config import PRIMARY_MODEL, SECONDARY_MODEL
class Chatbot(BaseApp):
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "COST" not in st.session_state:
        st.session_state.COST = 0

    def __init__(self, model_manager, app_name="ChatBot 🤖", app_slogan="Where Questions Meet Solutions"):
        super().__init__(app_name)
        self.app_slogan = app_slogan
        self.model_manager = model_manager 

    
    def process_input(self, user_input):
        chain_input = {
            "user_question": user_input,
            "chat_history": st.session_state.chat_history
        }
        return self.model_manager.generate(chain_input)
    
    def welcome_screen(self, app_slogan):
        return super().welcome_screen(app_slogan)

    def generate_prompt(self):
        prompt_template = ChatPromptTemplate.from_template("""
                                                                  
            You are a friendly and helpful AI assistant trained to assist with a variety of tasks, including answering questions, providing recommendations, offering educational content, and solving problems.
            Your responses should be clear, concise, and tailored to the user’s level of understanding.
            You should ask clarifying questions when necessary and ensure that the user feels comfortable and confident in the information you provide.
            Maintain a polite and engaging tone throughout the conversation.    
            Be concise and specific in your answers if user question requires creativity be more creative.
            User Question: {user_question}
            Chat History: {chat_history}
            """)
        return prompt_template 
    
    def handle_input(self):
        user_input = st.chat_input("Type your message here", disabled=False)

        if user_input:
            st.session_state.chat_history.append(HumanMessage(user_input))

            with st.chat_message("user", avatar="😀"):
                st.markdown(user_input)
            
            prompt_template = self.generate_prompt()

            response, st.session_state.COST = self.model_manager.generate(
                prompt_template,
                {
                    "user_question":  user_input,
                    "chat_history": st.session_state.chat_history
                }
            )
            print(f"{st.session_state.COST}$")
            super().display_ai_response(response)
            return user_input


def main():
    model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)
    app = Chatbot(model_manager)
    app.welcome_screen("Welcome")
    app.handle_input()

if __name__ == "__main__":
    main()