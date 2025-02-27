import streamlit as st
from BaseApp import BaseApp
import streamlit as st
from BaseApp import BaseApp
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from Config import PRIMARY_MODEL, SECONDARY_MODEL
from Model_Manager import ModelManager
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
if "COST" not in st.session_state:
    st.session_state.COST = 0

class StoryWriter(BaseApp):
    def __init__(self, model_manager, app_name = "Story Writer ✨", app_slogan = "Write your world, one story at a time! 📖✍️"):
        super().__init__(app_name)
        self.app_slogan = app_slogan
        self.model_manager = model_manager
    
    def welcome_screen(self, app_slogan):
        super().welcome_screen(app_slogan)

    def generate_prompt(self):
        prompt_template = ChatPromptTemplate.from_template("""
    
        You are a creative and imaginative story-writing assistant for kids.
        The user will provide the main characters, the scenario, or the goal of the story, and your task is to craft an exciting, engaging, and age-appropriate tale based on their input.
        Follow these guidelines:
            Kid-Friendly Language: Use simple, playful, and vivid language that captures a child’s imagination.
            Exciting Story Structure: Create a story with a clear beginning, middle, and happy or meaningful ending. Ensure the story flows naturally and stays easy to follow.
            Adventurous and Positive Themes: Focus on themes like adventure, friendship, kindness, problem-solving, and magical or whimsical elements. Avoid anything overly scary or inappropriate.
            Interactive Feel: Add fun details that make the story exciting and relatable to kids, like quirky character traits, imaginative settings, or unexpected twists.
            Short and Sweet: Keep the story concise and engaging (around 300-500 words), perfect for short reading sessions.
            Always ensure the story aligns with the characters and scenario provided by the user while leaving room for wonder and surprise!
            The user might pass additional instructions related to the flow of the story.
            There's always a main character in the story
            The user will also describe the situation to you
            Be creative please
            We'll ask the user the following "Anything else to add" if his answer was no or thank you write the story based on the inputs
            else add the requirements the user asked for
            main_character: {main_character}
            Characters: {characters}
            user_input: {user_input}
            additional_instructions: {additional_instructions}
            situation: {situation}
            chat_history: {chat_history}
    """)
        
        return prompt_template 
    
    def handle_input(self):
        
        user_input = st.chat_input("Anything you'd like to add...")

        with st.sidebar:
                main_character = st.text_area("Enter Main Character")
                character1 = st.text_area("Enter a new character", key="Character1")
                character2 = st.text_area("Enter a new character", key="Character2")
                character3 = st.text_area("Enter a new character", key="Character3")
                character4 = st.text_area("Enter a new character", key="Character4")
                character5 = st.text_area("Enter a new character", key="Character5")
                character6 = st.text_area("Enter a new character", key="Character6")
                situation = st.text_area("Describe Situation")
                additional_instructions = st.text_area("Additional Instructions")
        
        
        
        prompt_template = self.generate_prompt()
        characters = [character1,character2,character3,character4,character5,character6]
        if user_input:

            with st.chat_message("user", avatar="😀"):
                st.markdown(user_input)
                st.session_state.chat_history.append(user_input)

            response, st.session_state.COST = self.model_manager.generate(
                prompt_template, 
                {
                    "main_character": main_character,
                    "characters": ", ".join([char for char in characters if char]),
                    "user_input": user_input,
                    "additional_instructions": additional_instructions,
                    "situation": situation,
                    "chat_history": st.session_state.chat_history
            }
        )
            print(st.session_state.COST)
            super().display_ai_response(response)
        return user_input

def main():
    model_manager = ModelManager(PRIMARY_MODEL, SECONDARY_MODEL)
    app = StoryWriter(model_manager)
    app.welcome_screen('test')
    app.handle_input()
    


if __name__ == "__main__":
    main()