import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from BaseApp import BaseApp
from Model_Manager import ModelManager, PRICING
from Config import PRIMARY_MODEL, SECONDARY_MODEL, Images_MODEL
import base64
from PIL import Image
import io
import PyPDF2
import docx
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# Ensure session state variables
if "original_image" not in st.session_state:
    st.session_state.original_image = None
if "image_summary" not in st.session_state:
    st.session_state.image_summary = None
if "COST" not in st.session_state:
    st.session_state.COST = 0
if "education_level" not in st.session_state:
    st.session_state.education_level = "University Student"
if "topic" not in st.session_state:
    st.session_state.topic = None
if "details" not in st.session_state:
    st.session_state.details = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "doc" not in st.session_state:
    st.session_state.doc = None
if "doc_type" not in st.session_state:
    st.session_state.doc_type = None
if "exam_duration" not in st.session_state:
    st.session_state.exam_duration = "30 minutes"

class ExamGenerator(BaseApp):
    def __init__(self, model_manager, app_name="Exam Generator", app_slogan="Create structured assessments quickly"):
        super().__init__(app_name)
        self.app_slogan = app_slogan
        self.model_manager = model_manager

    def welcome_screen(self, bot_slogan="Create exams to test topic understanding 📝🧠"):
        return super().welcome_screen(bot_slogan)

    def extract_text_from_pdf(self, pdf_file):
        """Extracts text from a PDF file."""
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        return "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])

    def extract_text_from_docx(self, docx_file):
        """Extracts text from a DOCX file."""
        doc = docx.Document(docx_file)
        return "\n".join(para.text for para in doc.paragraphs)

    def encode_image(self, image_file):
        """Encodes an image as a base64 string for passing to the model."""
        img = Image.open(image_file).convert("RGB").resize((1024, 1024))
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=75)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def generate_text_prompt(self):
        return ChatPromptTemplate.from_template(
            """
            You are an intelligent exam builder. Generate a structured exam based on the following details:

            Topic: {topic}
            Education Level: {education_level}
            Exam Duration: {exam_duration}
            Additional Details: {details}
            Reference Material: {doc_context}

            Create a set of questions that test the understanding of the topic for the given education level and duration.
            """
        )

    def generate_chat_prompt(self):
        return ChatPromptTemplate.from_template(
            """
            Continue the conversation about the exam generation with the following details:

            Topic: {topic}
            Education Level: {education_level}
            Exam Duration: {exam_duration}
            Chat History: {chat_history}
            User Question: {user_question}

            Provide a response that assists in generating or refining the exam questions.
            """
        )

    def display_side(self):
        """Sidebar UI: user selects education level, exam duration, either uploads or pastes a problem, then clicks Generate."""
        with st.sidebar:
            st.header("Exam Builder Settings")
            st.session_state.education_level = st.selectbox(
                "Select Education Level",
                [
                    "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5",
                    "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10",
                    "Grade 11", "Grade 12", "University Student",
                    "Working Professional"
                ],
                index=12
            )

            st.session_state.exam_duration = st.selectbox(
                "Exam Duration",
                ["30 minutes", "45 minutes", "1 hour", "1.5 hours", "2 hours"],
                index=0
            )

            st.session_state.topic = st.text_input("Enter Topic")
            st.session_state.details = st.text_input("Other details (e.g., specific concepts to focus on)")

            uploaded_file = st.file_uploader(
                "Upload reference material (image or document)",
                type=["pdf", "docx", "csv", "jpg", "jpeg", "png"]
            )

            if uploaded_file:
                file_type = uploaded_file.name.split(".")[-1].lower()
                st.session_state.doc_type = file_type

                if file_type in ["jpg", "jpeg", "png"]:
                    st.session_state.img = self.encode_image(uploaded_file)
                    st.session_state.original_image = uploaded_file.getvalue()
                else:
                    st.session_state.original_image = None
                    content = None
                    try:
                        if file_type == "pdf":
                            content = self.extract_text_from_pdf(uploaded_file)
                        elif file_type == "docx":
                            content = self.extract_text_from_docx(uploaded_file)
                        elif file_type == "csv":
                            df = pd.read_csv(uploaded_file, encoding="latin1")
                            content = df.to_string()
                        st.session_state.doc = content
                    except Exception as e:
                        st.error(f"Error processing file: {e}")
            else:
                st.session_state.doc = None
                st.session_state.doc_type = None

            if st.button("Generate Exam!"):
                st.session_state.solve_clicked = True
                # Force a rerun to immediately handle the click
                st.rerun()

    def display_chat_history(self):
        """Display the chat history in a consistent manner."""
        # First message from assistant
        st.chat_message("assistant").write("**Exam Generation Assistant:**")
        
        # Display all messages in the chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])

    def handle_input(self):
        """Handle user input and generate responses with proper cost tracking"""
        # Display existing chat history first
        self.display_chat_history()
        
        # Handle Generate Exam button click
        if "solve_clicked" in st.session_state and st.session_state.solve_clicked:
            st.session_state.solve_clicked = False

            # Store user message first
            user_content = f"Generate an exam about: {st.session_state.topic} for {st.session_state.exam_duration}"
            if st.session_state.original_image:
                user_content += " [+image]"

            st.session_state.chat_history.append(
                {"role": "user", "content": user_content}
            )

            with st.spinner("Generating exam..."):
                if st.session_state.original_image:
                    final_answer = self.handle_image_query(
                        st.session_state.topic,
                        st.session_state.img
                    )
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": final_answer}
                    )
                else:
                    prompt_template = self.generate_text_prompt()
                    doc_context = ""
                    if st.session_state.doc:
                        doc_context = f"""
                        **Reference Material Content:**
                        {st.session_state.doc[:3000]}
                        """

                    inputs = {
                        "education_level": st.session_state.education_level,
                        "topic": st.session_state.topic,
                        "exam_duration": st.session_state.exam_duration,
                        "details": st.session_state.details,
                        "doc_context": doc_context
                    }

                    try:
                        response, cost = self.model_manager.generate(prompt_template, inputs)
                        st.session_state.COST += cost
                        print(f"Cost: ${st.session_state.COST}")  # Terminal logging

                        if response.strip():  # Check if the response is not empty
                            st.session_state.chat_history.append(
                                {"role": "assistant", "content": response}
                            )
                        else:
                            st.error("Received an empty response from the model.")

                        st.session_state.COST = 0  # Reset after processing
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
            
            # Force a rerun to update the chat display
            st.rerun()

        # Handle ongoing chat
        user_input = st.chat_input("Ask for modifications or clarifications:")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            
            with st.spinner("Generating your exam"):
                prompt_template = self.generate_chat_prompt()
                inputs = {
                    "topic": st.session_state.topic,
                    "education_level": st.session_state.education_level,
                    "exam_duration": st.session_state.exam_duration,
                    "chat_history": "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_history[:-1]]),  # Exclude the most recent user message
                    "user_question": user_input
                }

                try:
                    response, cost = self.model_manager.generate(prompt_template, inputs)
                    st.session_state.COST += cost
                    print(f"Cost: ${st.session_state.COST}") 

                    if response.strip(): 
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                    else:
                        st.error("Received an empty response from the model.")

                    st.session_state.COST = 0 
                except Exception as e:
                    st.error(f"An error occurred: {e}")
            
            # Force a rerun to update the chat display with the new messages
            st.rerun()

    def handle_image_query(self, user_input_str, base64_image_str):
        """Handle image queries with proper cost tracking"""
        try:
            model_name = PRIMARY_MODEL["model_name"]
            model = ChatOpenAI(model=model_name, temperature=PRIMARY_MODEL["temperature"])
            used_model = "GPT-4o-mini"
        except Exception as e:
            st.warning(f"Primary Model Failed: {e}, switching to Claude 3.5 Sonnet.")
            model_name = Images_MODEL["model_name"]
            model = ChatAnthropic(model=model_name, temperature=Images_MODEL["temperature"])
            used_model = "Claude 3.5 Sonnet"

        try:
            content = [
                {"type": "text", "text": f"You are an intelligent exam builder..."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image_str}"}},
                {"type": "text", "text": f"Education Level: {st.session_state.education_level}..."}
            ]

            response = model.invoke([HumanMessage(content=content)])
            input_tokens = response.usage_metadata.get("input_tokens", 0)
            output_tokens = response.usage_metadata.get("output_tokens", 0)
            cost = (input_tokens * PRICING[model_name]["input"]) + (output_tokens * PRICING[model_name]["output"])
            
            print(f"Image processing cost: ${cost}")  # Terminal logging
            st.session_state.COST = cost  # Set rather than accumulate

            refine_prompt = ChatPromptTemplate.from_template("...")
            chain = refine_prompt | model
            final_response = chain.invoke({
                "existing_answer": response.content,
                "education_level": st.session_state.education_level,
                "exam_duration": st.session_state.exam_duration
            })

            input_tokens2 = final_response.usage_metadata.get("input_tokens", 0)
            output_tokens2 = final_response.usage_metadata.get("output_tokens", 0)
            refine_cost = (input_tokens2 * PRICING[model_name]["input"]) + (output_tokens2 * PRICING[model_name]["output"])
            
            print(f"Refinement cost: ${refine_cost}")  # Terminal logging
            st.session_state.COST += refine_cost
            print(f"Total image processing cost: ${st.session_state.COST}")  # Terminal logging
            
            return final_response.content

        except Exception as e:
            st.error(f"Primary model failed mid-query: {e}. Switching to fallback...")
            # Fallback implementation with similar cost tracking
            # [Remaining fallback code with print statements...]

def main():
    model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)
    app = ExamGenerator(model_manager)
    app.welcome_screen()
    app.display_side()
    app.handle_input()

if __name__ == "__main__":
    main()