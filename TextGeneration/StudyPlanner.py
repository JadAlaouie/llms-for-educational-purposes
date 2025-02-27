import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from BaseApp import BaseApp
from Model_Manager import ModelManager
from Config import PRIMARY_MODEL, SECONDARY_MODEL
class StudyPlanner(BaseApp):
    def __init__(self, model_manager, app_name="Study Planner", app_slogan="📅 Plan Your Study Schedule!"):
        super().__init__(app_name)
        self.app_slogan = app_slogan
        self.model_manager = model_manager

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "generate_clicked" not in st.session_state:
            st.session_state.generate_clicked = False
        if "COST" not in st.session_state:
            st.session_state.COST = 0

    def welcome_screen(self, app_slogan):
        super().welcome_screen(app_slogan)

    def display_side(self):
        with st.sidebar:
            st.header("⚙️ Study Planner Settings")
            st.session_state.user_info = {
                "category": st.selectbox(
                    "Education Level",
                    [
                        "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
                        "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12",
                        "University Student"
                    ],
                    index=12
                ),
                "schedule_type": st.selectbox("Schedule Type", ["Daily", "Weekly"], index=1),
                "study_hours": st.selectbox("Study Hours/Day", ["1", "2", "3", "4", "5"], index=2)
            }
            st.session_state.study_tasks = st.text_area("📚 Study Tasks")
            st.session_state.other_activities = st.text_area("🎭 Other Activities")

            if st.button("📅 Generate Study Plan"):
                st.session_state.generate_clicked = True

    def generate_prompt(self, is_follow_up=False):
        if is_follow_up:
            return ChatPromptTemplate.from_template("""
                You are an AI assistant helping a {category} student with their study plan.
                Previous Context: {previous_context}
                User's Question: {user_question}
                ---
                Provide a helpful response.
            """)
        else:
            return ChatPromptTemplate.from_template("""
                Create a {schedule_type} study plan for a {category} student.
                Study Hours: {study_hours} hours/day
                Tasks: {study_tasks}
                Activities: {other_activities}
                ---
                Format as a structured table.
            """)

    def handle_input(self):
        if "generate_clicked" in st.session_state and st.session_state.generate_clicked:
            inputs = {
                "schedule_type": st.session_state.user_info["schedule_type"],
                "category": st.session_state.user_info["category"],
                "study_hours": st.session_state.user_info["study_hours"],
                "study_tasks": st.session_state.study_tasks,
                "other_activities": st.session_state.other_activities
            }
            prompt_template = self.generate_prompt(is_follow_up=False)
            response, st.session_state.COST = self.model_manager.generate(prompt_template, inputs)

            st.session_state.chat_history.append(("AI", response))
            st.session_state.generate_clicked = False  

        user_message = st.chat_input("Ask a follow-up question or request changes...")
        if user_message:
            st.session_state.chat_history.append(("User", user_message))

            prompt_template = self.generate_prompt(is_follow_up=True)
            previous_context = "\n".join([f"{role}: {msg}" for role, msg in st.session_state.chat_history[-5:]])  
            response = self.model_manager.generate(
                prompt_template,
                {
                    "category": st.session_state.user_info["category"],
                    "previous_context": previous_context,
                    "user_question": user_message
                }
            )
            st.session_state.chat_history.append(("AI", response))
        print(st.session_state.COST)
    def display_messages(self):
        for role, message in st.session_state.chat_history:
            if role == "User":
                with st.chat_message("User", avatar="😀"):
                    st.markdown(message)
            elif role == "AI":
                with st.chat_message("AI", avatar="🤖"):
                    st.markdown(message)

def main():
    model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)
    app = StudyPlanner(model_manager)
    app.welcome_screen('')
    app.handle_input()
    app.display_messages()
    app.display_side()

if __name__ == "__main__":
    main()