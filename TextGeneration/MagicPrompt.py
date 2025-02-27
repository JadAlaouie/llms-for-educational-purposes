import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from BaseApp import BaseApp

class MagicPrompt(BaseApp):

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "document_content" not in st.session_state:
        st.session_state.document_content = ''
    
    if "COST" not in st.session_state:
        st.session_state.COST = 0

    def __init__(self, model_manager, app_name="Magic Prompt ✨", app_slogan="Generate high-quality AI prompts effortlessly!"):
        super().__init__(app_name)
        
        # Initialize session state variables
        if "app_name" not in st.session_state:
            st.session_state.app_name = app_name
        if "app_slogan" not in st.session_state:
            st.session_state.app_slogan = app_slogan
        
        self.model_manager = model_manager
        
        # Additional session state variables
        if "generated_prompt" not in st.session_state:
            st.session_state.generated_prompt = ""
        if "content_type" not in st.session_state:
            st.session_state.content_type = ""
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

    def welcome_screen(self):
        # Access the slogan from session state
        super().welcome_screen(st.session_state.app_slogan)

    def display_side(self):
        with st.sidebar:
            # Content type selection
            selected_type = st.selectbox(
                "Select content type",
                ["Image", "Text", "Video", "Audio"]
            )
            st.session_state.content_type = selected_type


        # Generate a creative slogan
        prompt_template = ChatPromptTemplate.from_template("""
            Create an engaging slogan for the app named '{app_name}' that generates {content_type} content.
            Make it concise and relevant to the user's description: {user_description}.
        """)
    
    def generate_ai_prompt(self, user_description):
        # Generate the AI prompt template
        prompt_template = ChatPromptTemplate.from_template(
            f"""
            Generate a high-quality AI prompt for creating {st.session_state.content_type.lower()} content.
            User Description: {user_description}
            """
        )
        chain_input = {
            "content_type": st.session_state.content_type,
            "user_description": user_description
        }
        response, st.session_state.COST = self.model_manager.generate(prompt_template, chain_input)
        print(st.session_state.COST)
        return response

    def handle_input(self):
        # Get user input from the chat input box
        user_description = st.chat_input("Describe what you want to generate")

        if user_description:
            # Add user message to chat history
            st.session_state.chat_history.append(("User", user_description))

            # Generate magic prompt (app name and slogan)
            self.generate_ai_prompt(user_description)

            # Generate AI prompt
            generated_prompt = self.generate_ai_prompt(user_description)
            st.session_state.generated_prompt = generated_prompt

            # Add AI response to chat history
            st.session_state.chat_history.append(("AI", generated_prompt))

            super().display_ai_response(generated_prompt)
            # Rerun the app to reflect changes
            st.rerun()

    def display_messages(self):
        # Display chat history
        for role, message in st.session_state.chat_history:
            if role == "User":
                with st.chat_message("User", avatar="😀"):
                    st.markdown(message)
            elif role == "AI":
                with st.chat_message("AI", avatar="🤖"):
                    st.markdown(message)

def main():
    # Initialize the model manager
    from Model_Manager import ModelManager
    from Config import PRIMARY_MODEL, SECONDARY_MODEL

    model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)


    
    app = MagicPrompt(model_manager)
    app.welcome_screen()
    app.handle_input()
    app.display_side()

if __name__ == "__main__":
    main()