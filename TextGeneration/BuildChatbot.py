import streamlit as st
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from BaseApp import BaseApp
from Config import PRIMARY_MODEL, SECONDARY_MODEL
from Model_Manager import ModelManager
class BuildChatbot(BaseApp):
    if "COST" not in st.session_state:
        st.session_state.COST = 0

    def __init__(self, model_manager, app_name="Chatbot Builder 🚀", app_slogan="Customize your own Chatbot in seconds💡"):
        super().__init__(app_name)
        if "app_name" not in st.session_state:
            st.session_state.app_name = app_name
        if "app_slogan" not in st.session_state:
            st.session_state.app_slogan = app_slogan
        
        self.model_manager = model_manager

        if "uploaded_file" not in st.session_state:
            st.session_state.uploaded_file = None

        if "user_requirements" not in st.session_state:
            st.session_state.user_requirements = {
                "category": "",
                "description": "",
                "instructions": "",
                "ready": False  
            }
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

    def welcome_screen(self, app_slogan):
        st.title(f"{st.session_state.app_name}")
        st.subheader(f"{st.session_state.app_slogan}")

    def display_side(self):
        with st.sidebar:
            selected_category = st.selectbox(
                "Select your level",
                ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
                "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12",
                "University Student", "Working Professional"]
            )
            bot_description = st.text_input("Add a short Description 🤗", placeholder="You are a bot that knows how to cook...")
            additional_instructions = st.text_input("Additional Instructions", placeholder="Concise and Specific in your responses")

            create_now = st.button(
                "Create Now!",
                disabled=not (selected_category and bot_description),
                key="create_now_button"
            )
            
            if create_now:
                st.session_state.user_requirements.update({
                    "category": selected_category,
                    "description": bot_description,
                    "instructions": additional_instructions,
                    "ready": True
                })
                self.generate_bot_name()
            
                st.rerun()

            uploaded_file = st.file_uploader(
                "Upload a file",
                type=["pdf", "csv", "docx"],
            )
            st.session_state.uploaded_file = uploaded_file

    def generate_prompt(self, user_question):
        prompt_template = ChatPromptTemplate.from_template("""
        You are an AI assistant designed to assist users based on their specific background and requirements. 
        Below are the details provided by the user:

        - **Category**: {category} (Be kind to younger students, add emojis, and make their experience fun.)
        - **User Description**: {description}
        - **Additional Instructions**: {instructions}

        Please ensure that your responses align with the user's background and preferences.

        **User's Question**: {user_question}
        User could also provide PDFs or DOCX files: {document}

        Respond in a way that best suits the user's category and aligns with their requirements.
        """)
        return prompt_template
    
    def generate_bot_name(self):
        prompt_template = ChatPromptTemplate.from_template("""
            Generate a short name (max 5 words) based on:
            - User's level: {user_level}
            - Bot description: {description}
            - Additional instructions: {instructions}
            Keep it catchy and relevant.
        """)
        response_name, st.session_state.COST = self.model_manager.generate(
            prompt_template, 
            {
                "user_level": st.session_state.user_requirements["category"],
                "description": st.session_state.user_requirements["description"],
                "instructions": st.session_state.user_requirements["instructions"]
            }
        )
        st.session_state.app_name = response_name
        print(st.session_state.COST)
        prompt_template = ChatPromptTemplate.from_template("""\
            Create a creative slogan for the app named '{app_name}' targeting {user_level}.
            Make it engaging and concise.
        """)
        response_slogan, st.session_state.COST = self.model_manager.generate(
            prompt_template,
            {
                "app_name": st.session_state.app_name,
                "user_level": st.session_state.user_requirements["category"]
            }
        )
        st.session_state.app_slogan = response_slogan

    def handle_input(self):
        chatbot_ready = st.session_state.user_requirements["ready"]
        
        user_input = st.chat_input(
            "Type your message here",
            disabled=not chatbot_ready,
            key="chat_input_disabled"
        )

        doc = super().upload(st.session_state.uploaded_file) if st.session_state.uploaded_file else None

        if user_input:
            st.session_state.chat_history.append(HumanMessage(user_input))
            
            with st.chat_message("Student", avatar="😀"):
                st.markdown(user_input)

            prompt_template = self.generate_prompt(user_input)

            response, st.session_state.COST = self.model_manager.generate(
                prompt_template,
                {
                    "category": st.session_state.user_requirements["category"],
                    "description": st.session_state.user_requirements["description"],
                    "instructions": st.session_state.user_requirements["instructions"],
                    "user_question": user_input,
                    "document": doc
                }
            )
            print(st.session_state.COST)
            super().display_ai_response(response)

        return user_input, doc

def main():
    model_manager = ModelManager(PRIMARY_MODEL,SECONDARY_MODEL)
    app = BuildChatbot(model_manager)
    app.welcome_screen(app_slogan="TEST")
    app.display_side()
    app.handle_input()

if __name__ == "__main__":
    main()