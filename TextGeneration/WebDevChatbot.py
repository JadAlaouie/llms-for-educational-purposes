from BaseApp import BaseApp
import streamlit as st
from Model_Manager import ModelManager
import asyncio
import openai
from anthropic import Anthropic
from dotenv import load_dotenv
import os 
import htmlmin
load_dotenv()
from Config import PRIMARY_MODEL, SECONDARY_MODEL

openai.api_key = os.getenv("OPENAI_API_KEY")

anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

if "COST" not in st.session_state:
    st.session_state.COST = 0

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "HTML" not in st.session_state:
    st.session_state.HTML = ""

class WebDevChatbot(BaseApp):
    
    def welcome_screen(self):
        return

    
    def __init__(self, model_manager):
        self.TOTAL = 0
        self.tokens = {
            "input_tokens": 0,
            "response_tokens": 0,
            "total_tokens_per_prompt": 0
        }
        self.model_manager = model_manager
        try:
            self.assistant = openai.beta.assistants.create(
                name="Web Development Assistant",
                instructions="""
                Generate complete index.html with HTML/CSS/JS (all included in index.html no separate files please).
                Responsive & cross-browser compatible.
                No explanations, only code.
                Update entire code for changes.
                Include modern design elements.
                """,
                model="gpt-4o-mini",
                temperature=0.1,
            )
        except Exception as e:
            print(f"Failed to create OpenAI assistant: {e}")
            self.assistant = None

    def generate_with_claude(self, prompt_text):
        try:
            message = anthropic.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=4096,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": f"""Generate complete index.html with HTML/CSS/JS (all included in index.html no separate files please).
                    Responsive & cross-browser compatible. No explanations, only code. Include modern design elements. Don't tell the user what you did just REPLY with code.
                    
                    USER REQUEST: {prompt_text}
                    
                    CURRENT HTML: {st.session_state.HTML[:3000] if st.session_state.HTML else ''}"""
                }]
            )

            self.tokens["input_tokens"] = message.usage.input_tokens
            self.tokens["response_tokens"] = message.usage.output_tokens
            self.tokens["total_tokens_per_prompt"] = self.tokens["input_tokens"] + self.tokens["response_tokens"] 
            input_cost = self.tokens["input_tokens"] * (0.25 / 1000000)
            output_cost = self.tokens["response_tokens"] * (1.25 / 1000000)
            st.session_state.COST = input_cost + output_cost
            print(f"Claude Haiku 3\nInput: {self.tokens["input_tokens"]} | Output: {self.tokens["response_tokens"]} | Total: {self.tokens["total_tokens_per_prompt"]}")
            print(st.session_state.COST)
            return message.content[0].text

        except Exception as e:
            print(f"Claude generation failed: {e}")
            return "Both OpenAI and Claude failed to generate a response. Please try again later."
    
    def chunk_content(self, content, max_tokens=3000):
        words = content.split()
        chunk_size = int(max_tokens * 0.9)
        overlap = int(max_tokens * 0.1)

        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunks.append(" ".join(words[start:end]))
            start = end - overlap 
        
        return chunks

    async def async_generate_response(self, user_input):
        context = st.session_state.chat_history[-1].content if st.session_state.chat_history else ""

        prev_html = htmlmin.minify(
            st.session_state.HTML,
            remove_comments=True,
            remove_empty_space=True
        )

        context_chunks = self.chunk_content(prev_html)
        context = context_chunks[-1] if context_chunks else ""

        prompt_text = f"USER REQUEST: {user_input}\nCURRENT HTML CONTEXT:\n{context[:3000]}"

        try:
            if not self.assistant:
                raise Exception("OpenAI assistant not initialized")

            thread = openai.beta.threads.create()
            for chunk in self.chunk_content(prompt_text):
                openai.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=chunk
                )

            run = openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant.id,
            )

            while run.status != "completed":
                run = openai.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id,
                )
                await asyncio.sleep(1)

            messages = openai.beta.threads.messages.list(thread_id=thread.id)
            response = messages.data[0].content[0].text.value

            self.tokens["input_tokens"] = run.usage.prompt_tokens
            self.tokens["response_tokens"] = run.usage.completion_tokens
            self.tokens["total_tokens_per_prompt"] = run.usage.total_tokens
            input_cost = self.tokens["input_tokens"] * (0.150 / 1000000)
            output_cost = self.tokens["response_tokens"] * (0.600 / 1000000)
            st.session_state.COST = input_cost + output_cost
            print(f"GPT-4o-Mini\nInput Tokens {self.tokens["input_tokens"]} | Response Tokens {self.tokens["response_tokens"]} | Total Tokens {self.tokens["total_tokens_per_prompt"]}")
            print(st.session_state.COST)
        except Exception as e:
            print(f"OpenAI generation failed: {e}")
            print("Falling back to Claude...")
            response = self.generate_with_claude(prompt_text)

        st.session_state.HTML = response.strip().replace("```html", "").replace("```", "")
        return response

    def handle_input(self):
        col1, col2 = st.columns(2)

        with col1:
            st.title("AI WEB DEV")
            user_input = st.chat_input("Describe your website!")
            if user_input:
                response = asyncio.run(self.async_generate_response(user_input))
                self.display_ai_response(response)
                
        with col2:
            st.title("Preview")
            if st.session_state.HTML:
                st.components.v1.html(st.session_state.HTML, width=600, height=700, scrolling=True)

def main():
    from Config import PRIMARY_MODEL, SECONDARY_MODEL
    model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)
    st.set_page_config(layout="wide")
    app = WebDevChatbot(model_manager)
    app.welcome_screen()
    app.handle_input()

if __name__ == "__main__":
    main()
