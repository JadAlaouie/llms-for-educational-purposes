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
if "grade_level" not in st.session_state:
    st.session_state.grade_level = "University Student"
if "scale" not in st.session_state:
    st.session_state.scale = 5
if "assignment_type" not in st.session_state:
    st.session_state.assignment_type = "Essay"
if "assignment_description" not in st.session_state:
    st.session_state.assignment_description = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "doc" not in st.session_state:
    st.session_state.doc = None
if "doc_type" not in st.session_state:
    st.session_state.doc_type = None

class RubricGenerator(BaseApp):
    def __init__(self, model_manager, app_name="Rubric Generator", app_slogan="Create structured grading rubrics quickly"):
        super().__init__(app_name)
        self.app_slogan = app_slogan
        self.model_manager = model_manager

    def welcome_screen(self, bot_slogan="Create rubrics to evaluate assignments effectively 📝🧠"):
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
            You are an expert educational rubric creator with deep knowledge of curriculum development and evaluation methods. Your task is to create a comprehensive, well-structured grading rubric for a {assignment_type} assignment for a {grade_level} student.

            # RUBRIC INFORMATION
            Assignment Type: {assignment_type}
            Grade Level: {grade_level}
            Scale for Criteria: {scale}
            Assignment Description: {assignment_description}

            {doc_context}

            # RUBRIC STRUCTURE
            Create a complete, well-structured rubric with these components:

            1. **Criteria:** Define the key areas of evaluation.
            2. **Description:** Provide a brief description of what each criterion assesses.
            3. **Scale:** Use a scale of {scale} levels to evaluate each criterion.
            4. **Level Descriptions:** For each level in the scale, provide a description of what performance at that level looks like.

            # FORMATTING GUIDELINES
            - Output the rubric as a table with clear headings and subheadings.
            - Ensure the rubric is easy to read and understand.
            - Use age-appropriate language and examples.
            - Include any necessary formulas, diagrams, or reference material (described in words).

            The rubric should be clear, fair, and aligned with the specified grade level and assignment type. Focus on evaluating understanding of key concepts and application of knowledge rather than just memorization.
            """
        )

    def generate_chat_prompt(self):
        return ChatPromptTemplate.from_template(
            """
            You are an expert educational rubric creator continuing a conversation with a teacher or educator.

            # CONTEXT
            Assignment Type: {assignment_type}
            Grade Level: {grade_level}
            Scale for Criteria: {scale}

            # CHAT HISTORY
            {chat_history}

            # CURRENT QUESTION
            {user_question}

            Respond directly and helpfully to the user's current question. If they're asking for modifications to the rubric, offer specific improvements or alternatives. If they want clarification, provide detailed explanations with examples where appropriate.

            Keep your response focused on educational assessment best practices and curriculum development. If the user asks for additional rubric content, maintain the same high-quality structure and assessment principles as in the original rubric.

            Your goal is to help the user create the most effective assessment materials possible for evaluating their students' understanding.
            """
        )

    def display_side(self):
        """Sidebar UI: user selects grade level, scale for criteria, assignment type, and provides assignment description."""
        with st.sidebar:
            st.header("Rubric Builder Settings")
            st.session_state.grade_level = st.selectbox(
                "Select Grade Level",
                [
                    "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5",
                    "Grade 6", "Grade 7", "Grade 8", "Grade 9", "Grade 10",
                    "Grade 11", "Grade 12", "University Student",
                    "Working Professional"
                ],
                index=12
            )

            st.session_state.scale = st.selectbox(
                "Scale for Criteria",
                [3, 4, 5, 6, 7],
                index=2  # Default to 5
            )

            st.session_state.assignment_type = st.selectbox(
                "Assignment Type",
                ["Essay", "Project", "Presentation", "General Assessment"],
                index=0
            )

            st.session_state.assignment_description = st.text_area("Assignment Description")

            uploaded_file = st.file_uploader(
                "Upload reference material (image or document)",
                type=["pdf", "docx", "csv", "jpg", "jpeg", "png"]
            )

            if uploaded_file:
                file_type = uploaded_file.name.split(".")[-1].lower()
                st.session_state.doc_type = file_type

                if file_type in ["jpg", "jpeg", "png"]:
                    # It's an image
                    st.session_state.img = self.encode_image(uploaded_file)
                    st.session_state.original_image = uploaded_file.getvalue()
                else:
                    # It's text-based
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
                # No file → reset document state
                st.session_state.doc = None
                st.session_state.doc_type = None

            if st.button("Generate Rubric!"):
                st.session_state.solve_clicked = True
                # Force a rerun to immediately handle the click
                st.rerun()

    def display_chat_history(self):
        """Display the chat history in a consistent manner."""
        # First message from assistant
        st.chat_message("assistant").write("**Rubric Builder Assistant:**")

        # Display all messages in the chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])

    def handle_input(self):
        """Handle user input and generate responses with proper cost tracking"""
        # Display existing chat history first
        if len(st.session_state.chat_history) > 0:
            self.display_chat_history()

        # Handle Generate Rubric button click
        if "solve_clicked" in st.session_state and st.session_state.solve_clicked:
            st.session_state.solve_clicked = False

            # Store user message first
            user_content = f"Generate a rubric for: {st.session_state.assignment_description}"
            if st.session_state.original_image:
                user_content += " [+image]"

            st.session_state.chat_history.append(
                {"role": "user", "content": user_content}
            )

            with st.spinner("Generating rubric..."):
                if st.session_state.original_image:
                    final_answer = self.handle_image_query(
                        st.session_state.assignment_description,
                        st.session_state.img
                    )
                    rubric_df = self.parse_rubric_to_dataframe(final_answer)
                    st.table(rubric_df)

                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": final_answer}
                    )
                else:
                    prompt_template = self.generate_text_prompt()
                    doc_context = ""
                    if st.session_state.doc:
                        doc_context = f"""
                        **Reference Material Content:**
                        {st.session_state.doc[:3000]}  # Limit length to avoid token issues

                        Use the above document content as reference material for creating this rubric.
                        """

                    inputs = {
                        "grade_level": st.session_state.grade_level,
                        "assignment_type": st.session_state.assignment_type,
                        "scale": st.session_state.scale,
                        "assignment_description": st.session_state.assignment_description,
                        "doc_context": doc_context
                    }

                    try:
                        response, cost = self.model_manager.generate(prompt_template, inputs)
                        st.session_state.COST += cost
                        rubric_df = self.parse_rubric_to_dataframe(response)
                        st.table(rubric_df)
                        print(f"Total cost: ${st.session_state.COST}")

                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": response}
                        )

                        st.session_state.COST = 0  # Reset after processing
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

            # Force a rerun to update the chat display
            st.rerun()

        # Handle ongoing chat
        user_input = st.chat_input("Ask for modifications or clarifications:")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            with st.spinner("Updating rubric..."):
                prompt_template = self.generate_chat_prompt()
                inputs = {
                    "assignment_type": st.session_state.assignment_type,
                    "grade_level": st.session_state.grade_level,
                    "scale": st.session_state.scale,
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

    def parse_rubric_to_dataframe(self, rubric_text):
        lines = rubric_text.strip().split("\n")
        table_lines = [line for line in lines if "|" in line]
        if not table_lines:
            return pd.DataFrame({"Rubric": [rubric_text]})
        headers = [h.strip() for h in table_lines[0].split("|") if h.strip()]
        separator_line = table_lines[1] if len(table_lines) > 1 else ""

        if all(c == "-" or c == ":" or c == "|" or c == " " for c in separator_line):
            data_lines = table_lines[2:]
        else:
            data_lines = table_lines[1:]

        data = []
        for line in data_lines:
            row = [cell.strip() for cell in line.split("|") if cell.strip()]
            if row:
                data.append(row)

        max_columns = len(headers)
        for i in range(len(data)):
            if len(data[i]) < max_columns:
                data[i].extend([""] * (max_columns - len(data[i])))
            elif len(data[i]) > max_columns:
                data[i] = data[i][:max_columns]

        try:
            df = pd.DataFrame(data, columns=headers)
            return df
        except Exception as e:
            return pd.DataFrame({"Rubric Content": [rubric_text]})

    def handle_image_query(self, user_input_str, base64_image_str):
        """
        Handles an image-based query:
          - Tries GPT-4o-mini first
          - Fallback to Claude 3.5 Sonnet
          Accumulates cost from usage metadata.
        """
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
                {
                    "type": "text",
                    "text": f"You are an intelligent rubric builder. Analyze the image and generate a structured rubric based on its content."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image_str}"}
                },
                {
                    "type": "text",
                    "text": f"Grade Level: {st.session_state.grade_level}. Assignment Type: {st.session_state.assignment_type}. Scale: {st.session_state.scale}. If the image does not contain educational content, inform the user."
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

                Make sure the rubric is appropriate for the grade level: {grade_level} and uses a scale of: {scale}.
                Provide an enhanced version if needed (don't mention that you refined it).
                """
            )
            chain = refine_prompt | model
            final_response = chain.invoke({
                "existing_answer": summary_response,
                "grade_level": st.session_state.grade_level,
                "scale": st.session_state.scale
            })
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
                    "text": f"You are an intelligent rubric builder. Analyze the image and generate a structured rubric based on its content."
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image_str}"}
                },
                {
                    "type": "text",
                    "text": f"Grade Level: {st.session_state.grade_level}. Assignment Type: {st.session_state.assignment_type}. Scale: {st.session_state.scale}."
                }
            ])])

            input_tokens_f = fallback_response.usage_metadata.get("input_tokens", 0)
            output_tokens_f = fallback_response.usage_metadata.get("output_tokens", 0)
            cost_fallback = (
                input_tokens_f * PRICING[fallback_model_name]["input"]
                + output_tokens_f * PRICING[fallback_model_name]["output"]
            )
            st.session_state.COST = cost_fallback
            print(f"**Cost so far:** ${st.session_state.COST}")
            st.session_state.COST = 0
            return fallback_response.content

def main():
    model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)
    app = RubricGenerator(model_manager)
    app.welcome_screen()
    app.display_side()
    app.handle_input()

if __name__ == "__main__":
    main()
