from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from BaseApp import BaseApp
import streamlit as st
from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
from Model_Manager import ModelManager
from Config import PRIMARY_MODEL, SECONDARY_MODEL
import os

if "user_info" not in st.session_state:
    st.session_state.user_info = {
        "category": None,
        "subject": None,
        "web_search": False
    }

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "COST" not in st.session_state:
    st.session_state.COST = 0

class CareerAdvisor(BaseApp):
    def __init__(self, model_manager, app_name="Career Advisor 🌟", app_slogan="Guiding Every Step of Your Journey—From Classroom to Career!"):
        super().__init__(app_name)
        self.app_slogan = app_slogan
        self.model_manager = model_manager
    
    def process_input(self, user_input):
        chain_input = {
            "category": st.session_state.user_info["category"],
            "chat_history": st.session_state.chat_history,
            "documents": self.process_document(),
            "user_question": user_input
        }
        return self.model_manager.generate(chain_input)

    def welcome_screen(self, app_slogan):
        super().welcome_screen(app_slogan)

    def display_side(self):
        with st.sidebar:
            selected_category = st.selectbox("Select your level", 
                                            [None, "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
                                             "Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12",
                                             "University Student", "Working Professional"])
            st.session_state.user_info["category"] = selected_category
            
            uploaded_file = st.file_uploader("Upload a file", ["pdf","csv","docx"], 
                                           accept_multiple_files=False, 
                                           disabled=not selected_category)
            st.session_state.uploaded_file = uploaded_file
            
            web_search = st.toggle("Search the web (Optional)", 
                                 value=st.session_state.user_info.get("web_search", False),
                                 disabled=not selected_category)
            st.session_state.user_info["web_search"] = web_search

    def generate_prompt(self):
        prompt_template = ChatPromptTemplate.from_template("""                                              
            You are Career Compass 🌟, an empathetic and insightful career advisor. 
            [Keep previous template content unchanged]
            user question : {user_question}
            document : {documents}
            """)
        return prompt_template
    
    def handle_input(self):
        user_input = st.chat_input("Type your message here", disabled=not st.session_state.user_info["category"])
        document_content = super().upload(st.session_state.uploaded_file)
        
        if user_input:
            st.session_state.chat_history.append(HumanMessage(user_input))
            
            with st.chat_message("Student", avatar="😀"):
                st.markdown(user_input)

            prompt_template = self.generate_prompt()
            response, st.session_state.COST = self.model_manager.generate(
                prompt_template,
                {
                    "category": st.session_state.user_info["category"],
                    "chat_history": st.session_state.chat_history,
                    "documents": document_content,
                    "user_question": user_input
                }
            )

            # Web search enhancement
            if st.session_state.user_info.get("web_search", False):
                try:
                    search_query = f"{st.session_state.user_info['category']} career advice: {user_input}"
                    google_search = GoogleSearchAPIWrapper()
                    search_tool = Tool(
                        name="Career Search",
                        description="Searches Google for career-related information",
                        func=google_search.run
                    )
                    raw_results = search_tool.run(search_query)
                    summarized_results = self.summarize_web_results(raw_results, user_input)
                    response = f"{response}\n\n**Web Research Insights:**\n{summarized_results}"
                except Exception as e:
                    response = f"{response}\n\n⚠️ Could not retrieve web results: {str(e)}"
            print(st.session_state.COST)
            super().display_ai_response(response)
            st.session_state.chat_history.append(AIMessage(response))

    def summarize_web_results(self, raw_results, user_input):
        summarization_prompt = ChatPromptTemplate.from_template("""
            Analyze these career-related web results for: "{user_input}"
            {raw_results}

            Extract and summarize key information about:
            - Career paths and progression
            - Required education/training
            - Salary ranges and job outlook
            - Industry trends and opportunities
            - Professional development resources

            Present in Markdown with clear sections and bullet points.
            Include relevant links as [source](URL) when available.
            Keep explanations concise and age-appropriate for {category}.
            """)
        
        return self.model_manager.generate(
            summarization_prompt,
            {
                "user_input": user_input,
                "raw_results": raw_results,
                "category": st.session_state.user_info["category"]
            }
        )

def main():
    model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)
    app = CareerAdvisor(model_manager)
    app.welcome_screen("TEST")
    app.display_side()
    app.handle_input()

if __name__ == "__main__":
    main()
