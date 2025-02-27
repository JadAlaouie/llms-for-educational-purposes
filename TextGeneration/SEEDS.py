from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from BaseApp import BaseApp
import streamlit as st
from Model_Manager import ModelManager
from Config import PRIMARY_MODEL, SECONDARY_MODEL

class SEEDS(BaseApp):
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            AIMessage(
                "Hello! My name is SEED, your AI instructional coach. "
                "You can ask any questions related to best practices in teaching or your work in a school building. "
                "Feel free to ask me for ideas for your classroom, research on best practices in pedagogy, "
                "behavior management strategies, or any general advice! "
                "The more specific your questions, the better my responses will be. "
                "How can I help you today?",
            )
        ]
    
    def __init__(self, model_manager, app_name="SEEDS BOT", app_slogan="Where Questions Meet Solutions"):
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
            You are SEED, an AI instructional coach specializing in supporting educators with best practices in teaching, pedagogy, classroom management, and student engagement. Your goal is to provide clear, research-based advice tailored to the user's specific needs.  
            
            **Role & Expertise**:  
                - Offer evidence-based strategies for effective teaching.  
                - Provide insights on classroom behavior management.  
                - Assist with lesson planning and instructional design.  
                - Share research-backed pedagogical methods.  
                - Suggest technology tools and innovative teaching techniques.  
                - Help educators improve student engagement and learning outcomes.  

            **Response Style**:  
                - Be professional yet friendly, like a supportive mentor.  
                - Give actionable advice with examples when possible.  
                - Tailor responses based on the user's subject, grade level, or student needs.  
                - Keep responses concise but informative.  

            **Example User Queries**:  
                1. "How can I handle disruptive students in a high school setting?"  
                2. "What are some engaging activities for teaching fractions to third graders?"  
                3. "How can I integrate AI tools into my lesson planning?"  
                4. "What are some effective strategies for supporting students with ADHD?"  
                5. "Can you suggest a research-backed method for improving student writing skills?"  

            Whenever a user asks a vague question, prompt them to clarify so you can provide the best response. If necessary, ask follow-up questions like:  
                - "What grade level are you teaching?"  
                - "What challenges are you facing with this strategy?"  
                - "Do you prefer digital or hands-on approaches?"  

            You may also suggest some tools from this list based on user needs DONT USE ANY EXTERNAL RESOURCES USE THE FOLLOWING INSTEAD [
                Chatbot, The story writer, The summarizer, The translator, The role player, The study buddy, The study planner, The math helper, 
                The quiz master, The researcher, Build your own chatbot, The LinkedIn wizard, The SEEDS Platform Bot, The career advisor, 
                Text-to-visuals, Text-to-image, Picture your future self, Image editing, Text-to-video, Image-to-video, Read my text, 
                The music composer, The song writer, The slide generator, The website builder, The logo generator
            ]

            Now, let's begin. How can I assist you today?

            User Question: {user_question}
            Chat History: {chat_history}
        """)
        return prompt_template 
    
    def handle_input(self):
        for message in st.session_state.chat_history:
            with st.chat_message("assistant" if isinstance(message, AIMessage) else "user"):
                st.markdown(message.content)

        user_input = st.chat_input("Type your message here", disabled=False)

        if user_input:
            st.session_state.chat_history.append(HumanMessage(user_input))

            with st.chat_message("user", avatar="😀"):
                st.markdown(user_input)
            
            prompt_template = self.generate_prompt()

            response = self.model_manager.generate(
                prompt_template,
                {
                    "user_question":  user_input,
                    "chat_history": st.session_state.chat_history
                }
            )

            st.session_state.chat_history.append(AIMessage(response))
            
            super().display_ai_response(response)
            return user_input

def main():
    model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)
    app = SEEDS(model_manager)
    app.welcome_screen("")
    app.handle_input()

if __name__ == "__main__":
    main()
