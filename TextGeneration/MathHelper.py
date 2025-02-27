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
if "math_problem" not in st.session_state:
    st.session_state.math_problem = None
if "original_image" not in st.session_state:
    st.session_state.original_image = None
if "image_summary" not in st.session_state:
    st.session_state.image_summary = None
if "COST" not in st.session_state:
    st.session_state.COST = 0
if "education_level" not in st.session_state:
    st.session_state.education_level = "University Student"

class MathHelper(BaseApp):
    def __init__(self, model_manager, app_name="Math Helper", app_slogan="📚 Get Instant Math Solutions!"):
        super().__init__(app_name)
        self.app_slogan = app_slogan
        self.model_manager = model_manager
    def welcome_screen(self, bot_slogan=None):
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
        """Prompt for text-based math problems."""
        return ChatPromptTemplate.from_template(
            """
            You are a math tutor. The student is at {education_level} level.
            Solve the following problem:

            {math_problem}

            Provide a clear, step-by-step solution. Show relevant formulas.
            """
        )

    def display_side(self):
        """Sidebar UI: user selects education level, either uploads or pastes a problem, then clicks Solve."""
        with st.sidebar:
            st.header("Math Solver Settings")
            st.session_state.education_level = st.selectbox(
                "Select Education Level",
                [
                    "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5",
                    "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10",
                    "Grade 11", "Grade 12", "University Student",
                    "Working Professional"
                ],
                index=12  # default: "University Student"
            )

            uploaded_file = st.file_uploader(
                "Upload Your Math Problem (image or doc)",
                type=["pdf", "docx", "csv", "jpg", "jpeg", "png"]
            )
            pasted_problem = st.text_area("Or Paste Your Problem Here")

            if uploaded_file:
                file_type = uploaded_file.name.split(".")[-1].lower()
                if file_type in ["jpg", "jpeg", "png"]:
                    # It's an image
                    st.session_state.math_problem = self.encode_image(uploaded_file)
                    st.session_state.original_image = uploaded_file.getvalue()
                else:
                    # It's text-based
                    st.session_state.original_image = None
                    content = None
                    if file_type == "pdf":
                        content = self.extract_text_from_pdf(uploaded_file)
                    elif file_type == "docx":
                        content = self.extract_text_from_docx(uploaded_file)
                    elif file_type == "csv":
                        df = pd.read_csv(uploaded_file, encoding="latin1")
                        content = df.to_string()
                    st.session_state.math_problem = content
            else:
                # No file → take the pasted text
                st.session_state.math_problem = pasted_problem
                st.session_state.original_image = None

            if st.button("Solve Problem"):
                st.session_state.solve_clicked = True

    def handle_input(self):
        """Once Solve button is clicked, handle the problem if it exists."""
        if "solve_clicked" in st.session_state and st.session_state.solve_clicked:
            if not st.session_state.math_problem:
                st.warning("⚠️ Please input a problem (paste text or upload a file).")
                return

            if st.session_state.original_image:
                final_answer = self.handle_image_query(
                    st.session_state.math_problem,
                    st.session_state.math_problem  # The base64 string
                )
                st.write("## Solution:")
                st.write(final_answer)
                return
            else:
                prompt_template = self.generate_text_prompt()
                inputs = {
                    "education_level": st.session_state.education_level,
                    "math_problem": st.session_state.math_problem
                }

                try:
                    response, cost = self.model_manager.generate(prompt_template, inputs)
                    st.session_state.COST += cost
                    st.write("## Solution:")
                    st.write(response)
                    print(st.session_state.COST)
                    st.session_state.COST = 0
                except Exception as e:
                    st.error(f"An error occurred: {e}")

    def handle_image_query(self, user_input_str, base64_image_str):
        """
        Handles an image-based query:
          - Tries GPT-4o-mini first
          - Fallback to Claude 3.5 Sonnet
          Accumulates cost from usage metadata.
        """
        try:
            model_name = PRIMARY_MODEL["model_name"]  # e.g. "gpt-4o-mini"
            model = ChatOpenAI(model=model_name, temperature=PRIMARY_MODEL["temperature"])
            used_model = "GPT-4o-mini"
        except Exception as e:
            st.warning(f"Primary Model Failed: {e}, switching to Claude 3.5 Sonnet.")
            model_name = Images_MODEL["model_name"]
            model = ChatAnthropic(model=model_name, temperature=Images_MODEL["temperature"])
            used_model = "Claude 3.5 Sonnet"

        try:
            content = [
                {
                    "type": "text",
                    "text": "You are a math tutor. Interpret any math problem in this image and solve it step by step."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image_str}"}
                },
                {
                    "type": "text",
                    "text": f"Level: {st.session_state.education_level}. If the image doesn't contain a math problem, tell the user."
                }
            ]
            response = model.invoke([HumanMessage(content=content)])
            summary_response = response.content

            input_tokens = response.usage_metadata.get("input_tokens", 0)
            output_tokens = response.usage_metadata.get("output_tokens", 0)
            cost_summary = (input_tokens * PRICING[model_name]["input"]) + (output_tokens * PRICING[model_name]["output"])
            st.session_state.COST += cost_summary

            refine_prompt = ChatPromptTemplate.from_template(
                """
                {existing_answer}
                Provide a final, refined answer to the math problem (if any).
                """
            )
            chain = refine_prompt | model
            final_response = chain.invoke({"existing_answer": summary_response})
            input_tokens2 = final_response.usage_metadata.get("input_tokens", 0)
            output_tokens2 = final_response.usage_metadata.get("output_tokens", 0)
            cost_refine = (
                input_tokens2 * PRICING[model_name]["input"]
                + output_tokens2 * PRICING[model_name]["output"]
            )
            st.session_state.COST += cost_refine

            print(f"**Model used:** {used_model}")
            print(f"**Cost so far:** ${st.session_state.COST}")
            st.session_state.COST = 0
            return final_response.content

        except Exception as e:
            st.error(f"Primary model failed mid-query: {e}. Switching to fallback...")

            # Fallback
            fallback_model_name = Images_MODEL["model_name"]
            fallback_model = ChatAnthropic(
                model=fallback_model_name,
                temperature=Images_MODEL["temperature"]
            )
            fallback_response = fallback_model.invoke([HumanMessage(content=[
                {
                    "type": "text",
                    "text": "You are a math tutor. Interpret any math problem in this image and solve it step by step."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image_str}"}
                }
            ])])

            input_tokens_f = fallback_response.usage_metadata.get("input_tokens", 0)
            output_tokens_f = fallback_response.usage_metadata.get("output_tokens", 0)
            cost_fallback = (
                input_tokens_f * PRICING[fallback_model_name]["input"]
                + output_tokens_f * PRICING[fallback_model_name]["output"]
            )
            st.session_state.COST += cost_fallback
            print(f"**Cost so far:** ${st.session_state.COST}")
            st.session_state.COST = 0
            return fallback_response.content

def main():
    model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)
    app = MathHelper(model_manager)
    app.welcome_screen()
    app.display_side()
    app.handle_input()

if __name__ == "__main__":
    main()
