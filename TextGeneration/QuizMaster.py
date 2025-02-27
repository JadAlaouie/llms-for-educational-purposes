import streamlit as st
from BaseApp import BaseApp
from langchain_core.prompts import ChatPromptTemplate
from Model_Manager import ModelManager
from Config import PRIMARY_MODEL, SECONDARY_MODEL

if "document_content" not in st.session_state:
    st.session_state.document_content = ''

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "COST" not in st.session_state:
    st.session_state.COST = 0

class QuizGenerator(BaseApp):
    def __init__(self, model_manager, app_name="The Quiz Master", app_slogan="📄 Generate AI-Powered Quizzes!"):
        super().__init__(app_name)
        self.app_slogan = app_slogan
        self.model_manager = model_manager

        if "user_info" not in st.session_state:
            st.session_state.user_info = {
                "category": "University Student",
                "question_type": ["Multiple Choice"],
                "num_questions": 5,
                "open_question": False,
                "topic": ""
            }
        
        if "messages" not in st.session_state:
            st.session_state.messages = []

    def welcome_screen(self, app_slogan):
        super().welcome_screen(app_slogan)

    def display_main_ui(self):
        self.display_chat_history()

        user_input = st.chat_input("Chat with AI")
        if user_input:
            self.handle_chat_input(user_input)

    def display_side(self):
        with st.sidebar:
            st.header("Quiz Configuration")
            
            st.session_state.user_info["topic"] = st.text_input(
                "📝 Quiz Topic/Subject",
                placeholder="Enter your quiz topic (optional)"
            )
            
            st.session_state.user_info["category"] = st.selectbox(
                "🎓 Education Level", 
                ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
                 "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12", 
                 "University Student"], 
                index=12
            )
            
            st.session_state.user_info["question_type"] = st.multiselect(
                "🔢 Question Types:",
                options=["True/False", "Multiple Choice", "Open-ended"],
                default=st.session_state.user_info["question_type"]
            )
            
            st.session_state.user_info["num_questions"] = st.slider(
                "❓ Number of Questions", 1, 20, 5
            )
            
            with st.expander("⚙️ Advanced Options"):
                st.session_state.user_info["open_question"] = st.toggle(
                    "🔍 Include Case Study Question"
                )
            
            uploaded_file = st.file_uploader(
                "📂 Upload Study Material (optional)", 
                ["pdf", "csv", "docx"]
            )
            st.session_state.document_content = super().upload(uploaded_file)
            
            if st.button("🚀 Generate Quiz", use_container_width=True):
                self.handle_input()

    def generate_prompt(self):
        return ChatPromptTemplate.from_template("""
        Create a quiz for {education_level} students with these question types: {question_types}.
        Total Questions: {num_questions}
        {content_info}
        the user may also set use_case to True if True then provie a use_case of it {use_case_note}
        ---
        Format the quiz with clear sections for each question type.
        Include questions, options (where applicable), and answers.
        """)

    def handle_input(self):
        content_info = []
        if st.session_state.user_info["topic"]:
            content_info.append(f"Quiz Topic: {st.session_state.user_info['topic']}")
        if st.session_state.document_content:
            content_info.append(f"Study Material Content:\n{st.session_state.document_content}")
        
        inputs = {
            "education_level": st.session_state.user_info["category"],
            "question_types": ", ".join(st.session_state.user_info["question_type"]),
            "num_questions": st.session_state.user_info["num_questions"],
            "content_info": "\n".join(content_info) if content_info else "General Knowledge",
            "use_case_note": "Include a case study question about the main topic." 
                if st.session_state.user_info["open_question"] else ""
        }
        
        user_content = f"**Quiz Request:**\n"
        user_content += f"- Education Level: {inputs['education_level']}\n"
        user_content += f"- Question Types: {inputs['question_types']}\n"
        user_content += f"- Total Questions: {inputs['num_questions']}\n"
        user_content += f"- Case Study: {'Yes' if st.session_state.user_info['open_question'] else 'No'}\n"
        if st.session_state.user_info["topic"]:
            user_content += f"- Topic: {st.session_state.user_info['topic']}\n"
        if st.session_state.document_content:
            user_content += f"Uploaded Material: Yes\n"
        
        st.session_state.messages.append({"role": "user", "content": user_content})
        
        prompt_template = self.generate_prompt()
        response, st.session_state.COST = self.model_manager.generate(prompt_template, inputs)
        
        if not response:
            response = "No quiz generated. Please check your input parameters."
        print(st.session_state.COST)
        st.session_state.messages.append({"role": "assistant", "content": response})

    def handle_chat_input(self, user_message):
        if user_message.strip():
            st.session_state.messages.append({"role": "user", "content": user_message})

            prompt_template = ChatPromptTemplate.from_template("{messages}")

            response, _ = self.model_manager.generate(
                prompt_template,
                {"messages": "\n".join([msg['content'] for msg in st.session_state.messages])}
            )

            if not response:
                response = "No response from model. Please try again."

            st.session_state.messages.append({"role": "assistant", "content": response})
            super().display_ai_response(response)

        

    def display_chat_history(self):
        """Display the chat message history"""
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

def main():
    model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)
    app = QuizGenerator(model_manager)
    app.welcome_screen("")
    app.display_side()  # Sidebar should load first
    app.display_main_ui()  # Only display the chat interface


if __name__ == "__main__":
    main()