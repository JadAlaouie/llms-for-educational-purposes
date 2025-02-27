import streamlit as st
import requests
import os 
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SEGMIND_API_KEY")
API_URL = "https://api.segmind.com/v1/kling-text2video"

if "generating" not in st.session_state:
    st.session_state["generating"] = False 

if "run_generation" not in st.session_state:
    st.session_state["run_generation"] = False 

class Text2Video():
    def welcome_screen(self):
        st.set_page_config("Text-to-Video Magic", page_icon="✨")

        st.title("Text-to-Video Magic! 🚀🎥")
        st.subheader("Turn your ideas into a short animated video!")
        st.write("1) Type in something awesome you want to see."
                 "2) Pick your video shape."
                 "3) Click the **Generate Video** button and watch the magic happen!")
    

    def generate_video_segmind(self, prompt, aspect_ratio):
        data = {
            "prompt": prompt, 
            "negative-prompt": "No buildings, no artificial objects",
            "cfg_scale": 0.5,
            "mode": "std",
            "aspect_ratio": aspect_ratio,
            "duration": 5
        }
        headers = {"x-api-key": API_KEY}
        response = requests.post(API_URL, json=data, headers=headers)
        return response 

    def on_click_generate(self):
        if st.session_state["generating"]:
            return 
        st.session_state["generating"] = True 
        st.session_state["run_generation"] = True 

    def handle_input(self):
        prompt = st.text_area("Describe your dream video!","A border collie, wearing clothes made of laser film, wearing a headset, VR glasses, with the Milky Way reflected in his eyes, classic black and white, high-definition quality, surrealism, microcomputer, hacker dress, cyber style, anthropomorphism, reality")
        aspect_ratio = st.selectbox("Pick your video shape (Aspect Ratio)", ["16:9", "9:16", "1:1"], index=0)
        st.button("Generate Video 🚀", on_click=self.on_click_generate, disabled=st.session_state["generating"])
        if st.session_state["run_generation"]:
            if not prompt.strip():
                st.error("Oops! You need to type your idea first.")
                st.session_state["generating"] = False 
                st.session_state["run_generation"] = False 
                st.stop()
            
            with st.spinner("Hang on, we're creating your video..."):
                response = self.generate_video_segmind(prompt, aspect_ratio)
            
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "").lower()
                if "video" in content_type:
                    st.success("Your magical video is ready! 🎉")
                    video_data = response.content
                    st.video(video_data)
                else:
                    st.error("Hmm, the server said 200 (Ok), but it's not a video.")
                    st.write("Here's the first bit of what we got back:")
                    st.write(response.content[:300])
            else:
                st.error("Oops! We got an error: {response.status_code}")
                st.write("Server says:")
                st.write(response.text)

            st.session_state["generating"] = False 
            st.session_state["run_generation"] = False 

def main():
    app = Text2Video()
    app.welcome_screen()
    app.handle_input()

if __name__ == "__main__":
    main()