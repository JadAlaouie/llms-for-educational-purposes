import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from BaseApp import BaseApp
from Model_Manager import ModelManager
from Config import PRIMARY_MODEL, SECONDARY_MODEL
class LinkedInWizard(BaseApp):
    if "COST" not in st.session_state:
        st.session_state.COST = 0
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    def __init__(self, model_manager, app_name="LinkedIn Wizard", app_slogan="🚀 Optimize Your LinkedIn Profile for Success!"):
        super().__init__(app_name)
        self.app_slogan = app_slogan
        self.model_manager = model_manager
        
        # Initialize session state variables
        if "user_info" not in st.session_state:
            st.session_state.user_info = {
                "career_interest": "",
                "key_strengths": "",
                "education": "",
                "experiences": ""
            }
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "generate_clicked" not in st.session_state:
            st.session_state.generate_clicked = False

    def welcome_screen(self):
        super().welcome_screen(self.app_slogan)

    def display_side(self):
        with st.sidebar:
            st.header("📌 LinkedIn Profile Setup")
            st.session_state.user_info["career_interest"] = st.text_area("🎯 Career Interest", placeholder="e.g., Data Science")
            st.session_state.user_info["key_strengths"] = st.text_area("💪 Key Strengths", placeholder="e.g., Teamwork")
            st.session_state.user_info["education"] = st.text_area("🎓 Education", placeholder="e.g., Harvard University")
            st.session_state.user_info["experiences"] = st.text_area("🏆 Notable Experiences", placeholder="e.g., Built a website")
            
            if st.button("🚀 Generate LinkedIn Advice"):
                st.session_state.generate_clicked = True

    def generate_advice_prompt(self):
        return ChatPromptTemplate.from_template("""
        You are an expert in LinkedIn optimization. Provide advice for the user.
        **Career Interest:** {career_interest}
        **Key Strengths:** {key_strengths}
        **Education:** {education}
        **Notable Experiences:** {experiences}
        **Advice Format:**
        1. Profile Headline: Craft a compelling headline.
        2. Summary: Write a concise summary.
        3. Experience & Projects: Present experiences effectively.
        4. Skills Section: Recommend skills.
        5. Networking Tips: Provide strategies.
        6. Extra Improvements: Additional enhancements.
        """)

    def generate_followup_prompt(self):
        return ChatPromptTemplate.from_template("""
        You are an expert in LinkedIn optimization. The user has previously provided the following information:
        {previous_context}
        Now they ask: {user_question}
        Provide a helpful and concise response.
        """)

    def handle_input(self):
        # Handle initial LinkedIn advice generation
        if st.session_state.generate_clicked:
            user_input = {
                "career_interest": st.session_state.user_info["career_interest"],
                "key_strengths": st.session_state.user_info["key_strengths"],
                "education": st.session_state.user_info["education"],
                "experiences": st.session_state.user_info["experiences"]
            }
            prompt_template = self.generate_advice_prompt()
            response = self.model_manager.generate(prompt_template, user_input)

            # Add the AI-generated advice to the chat history
            st.session_state.chat_history.append(("User", "Generate LinkedIn advice"))
            st.session_state.chat_history.append(("AI", response))
            st.session_state.generate_clicked = False  # Reset the flag

        # Handle follow-up questions
        user_chat_input = st.chat_input("Ask follow-up questions or request further refinements:")
        if user_chat_input:
            # Add user message to chat history
            st.session_state.chat_history.append(("User", user_chat_input))

            # Generate a response to the follow-up question
            previous_context = "\n".join([f"{role}: {msg}" for role, msg in st.session_state.chat_history[-5:]])  # Use recent context
            prompt_template = self.generate_followup_prompt()
            response, st.session_state.COST = self.model_manager.generate(
                prompt_template,
                {
                    "previous_context": previous_context,
                    "user_question": user_chat_input
                }
            )
            print(st.session_state.COST)
            # Add AI response to chat history
            st.session_state.chat_history.append(("AI", response))

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
        model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)
        app = LinkedInWizard(model_manager)
        app.welcome_screen()
        app.display_side()
        app.display_messages()
        app.handle_input()

if __name__ == "__main__":
    main()