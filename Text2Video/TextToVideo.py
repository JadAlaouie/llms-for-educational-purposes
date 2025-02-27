import streamlit as st
import requests
import os
import json
import time
import cv2
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_URL = "https://api.segmind.com/v1/kling-text2video"
MINIMAXI_API_KEY = os.getenv("MINIMAXI_API_KEY")
SEGMIND_API_KEY = os.getenv("SEGMIND_API_KEY")

# Initialize session state
if "generating" not in st.session_state:
    st.session_state["generating"] = False

if "run_generation" not in st.session_state:
    st.session_state["run_generation"] = False

if "COST" not in st.session_state:
    st.session_state["COST"] = 0

# -------------------------------------------------------------------
# UTILITY FUNCTIONS
# -------------------------------------------------------------------

def log_debug(message, data=None):
    """Helper function to log debug information in Streamlit."""
    st.write(f"DEBUG: {message}")
    if data:
        st.write("Data:", data)

def get_video_duration_cv2(video_path: str) -> float:

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()

    if fps <= 0 or frame_count < 0:
        raise RuntimeError("Could not retrieve valid FPS/frame count from video")

    duration = frame_count / fps
    return duration

# -------------------------------------------------------------------
# MAIN CLASS
# -------------------------------------------------------------------

class Text2Video:
    def welcome_screen(self):
        st.set_page_config("Text-to-Video Magic", page_icon="✨")
        st.title("Text-to-Video Magic! 🚀🎥")
        st.subheader("Turn your ideas into a short animated video!")
        st.write("1) Type in something awesome you want to see.\n"
                 "2) Pick your video shape.\n"
                 "3) Click the **Generate Video** button and watch the magic happen!")

    # -----------------------------------------------
    # MINIMAXI-RELATED METHODS
    # -----------------------------------------------
    def invoke_video_generation_minimaxi(self, api_key, prompt):
        """Create a Minimaxi video generation task."""
        url = "https://api.minimaxi.chat/v1/video_generation"
        payload = {
            "prompt": prompt,
            "model": "video-01"
        }
        headers = {
            'authorization': f'Bearer {api_key}',
            'content-type': 'application/json'
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()['task_id']
        except (requests.exceptions.RequestException, KeyError, json.JSONDecodeError) as e:
            st.error(f"Minimaxi creation failed: {str(e)}")
            return None

    def query_video_generation_minimaxi(self, api_key, task_id):
        """Poll Minimaxi for task status."""
        url = f"https://api.minimaxi.chat/v1/query/video_generation?task_id={task_id}"
        headers = {'authorization': f'Bearer {api_key}'}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            status = data.get('status', 'Unknown')
            if status == 'Success':
                file_id = data.get('file_id', '')
                return file_id, 'Success'
            elif status in ['Queueing', 'Processing']:
                return '', status
            else:
                return '', 'Fail'
        except Exception as e:
            st.error(f"Error polling Minimaxi status: {str(e)}")
            return '', 'Fail'

    def fetch_video_result_minimaxi(self, api_key, file_id, output_path):
        """Fetch and save the generated Minimaxi video."""
        url = f"https://api.minimaxi.chat/v1/files/retrieve?file_id={file_id}"
        headers = {'authorization': f'Bearer {api_key}'}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            download_url = response.json()['file']['download_url']

            # Download and save video
            video_response = requests.get(download_url)
            video_response.raise_for_status()
            with open(output_path, 'wb') as f:
                f.write(video_response.content)

            # Calculate cost based on duration
            try:
                duration_seconds = get_video_duration_cv2(output_path)
                # Minimaxi T2V-01 pricing: $0.43 per 6s
                st.session_state.COST = 0.43 * (duration_seconds / 6.0)
                print(st.session_state.COST)
            except Exception as e:
                st.warning(f"Could not calculate video duration: {str(e)}")

            return download_url
        except Exception as e:
            st.error(f"Error retrieving video from Minimaxi: {str(e)}")
            return None

    def generate_video_minimaxi(self, prompt):
        """Attempt the entire Minimaxi flow."""
        api_key = MINIMAXI_API_KEY
        if not api_key:
            st.warning("No Minimaxi API key found!")
            return None

        output_file_name = "output.mp4"

        # 1) Submit generation task
        task_id = self.invoke_video_generation_minimaxi(api_key, prompt)
        if not task_id:
            return None

        # 2) Poll for status
        status_container = st.empty()
        while True:
            time.sleep(10)
            file_id, status = self.query_video_generation_minimaxi(api_key, task_id)

            if status == "Queueing":
                status_container.text("Waiting in queue (Minimaxi)...")
            elif status == "Processing":
                status_container.text("Generating video (Minimaxi)...")
            elif status == "Success" and file_id:
                status_container.text("Video generated successfully by Minimaxi!")
                break
            else:
                st.error(f"Minimaxi generation ended with status: {status}")
                return None

        # 3) Fetch and save video
        status_container.text("Downloading Minimaxi video...")
        download_url = self.fetch_video_result_minimaxi(api_key, file_id, output_file_name)
        status_container.empty()
        return download_url

    # -----------------------------------------------
    # SEGMIND-RELATED METHODS
    # -----------------------------------------------
    def generate_video_segmind(self, prompt, aspect_ratio):
        """Generates video using Segmind's Text-to-Video API."""
        data = {
            "prompt": prompt,
            "negative-prompt": "No buildings, no artificial objects",
            "cfg_scale": 0.5,
            "mode": "std",
            "aspect_ratio": aspect_ratio,
            "duration": 5
        }
        headers = {"x-api-key": SEGMIND_API_KEY}
        response = requests.post(API_URL, json=data, headers=headers)
        st.session_state.COST = 0.28
        print(st.session_state.COST)
        return response

    # -----------------------------------------------
    # MAIN LOGIC: fallback to Segmind if Minimaxi fails
    # -----------------------------------------------
    def attempt_generation(self, prompt, aspect_ratio):
        """
        1) Attempt Minimaxi first.
        2) If Minimaxi fails => fallback to Segmind.
        3) Return True if success from either, False if both fail.
        """
        st.info("Trying Minimaxi first...")
        minimaxi_url = self.generate_video_minimaxi(prompt)

        if minimaxi_url:
            # Minimaxi succeeded
            st.success("Your magical video (Minimaxi) is ready! 🎉")
            st.video(minimaxi_url)
            # Provide a download button
            st.download_button(
                "Download Video Now!",
                minimaxi_url,
                file_name="output.mp4",
                mime="video/mp4"
            )
            st.write(f"**Estimated Minimaxi Cost:** ${st.session_state.COST:.2f}")
            return True
        else:
            # Minimaxi failed => fallback to Segmind
            st.warning("Minimaxi failed, attempting Segmind next...")
            segmind_response = self.generate_video_segmind(prompt, aspect_ratio)
            if segmind_response.status_code == 200:
                content_type = segmind_response.headers.get("Content-Type", "").lower()
                if "video" in content_type:
                    st.success("Your magical video (Segmind) is ready! 🎉")
                    video_data = segmind_response.content
                    st.video(video_data)
                    st.write(f"**Estimated Segmind Cost:** ${st.session_state.COST:.2f}")
                    return True
                else:
                    st.error("Segmind responded with 200 but it's not a video.")
                    st.write("First part of the response content:")
                    st.write(segmind_response.content[:300])
                    return False
            else:
                st.error(f"Segmind failed with status code: {segmind_response.status_code}")
                st.write("Response text:", segmind_response.text)
                return False

    # -----------------------------------------------
    # STREAMLIT UI
    # -----------------------------------------------
    def on_click_generate(self):
        """Handle Generate Video button click."""
        if st.session_state["generating"]:
            return
        st.session_state["generating"] = True
        st.session_state["run_generation"] = True

    def handle_input(self):
        """Handle user input and fallback logic."""
        prompt = st.text_area(
            "Describe your dream video!",
            "A border collie, wearing clothes made of laser film, wearing a headset, VR glasses, "
            "with the Milky Way reflected in his eyes, classic black and white, high-definition quality, "
            "surrealism, microcomputer, hacker dress, cyber style, anthropomorphism, reality"
        )
        aspect_ratio = st.selectbox(
            "Pick your video shape (Aspect Ratio)",
            ["16:9", "9:16", "1:1"],
            index=0
        )

        st.button("Generate Video 🚀", on_click=self.on_click_generate, disabled=st.session_state["generating"])

        if st.session_state["run_generation"]:
            if not prompt.strip():
                st.error("Oops! You need to type your idea first.")
                st.session_state["generating"] = False
                st.session_state["run_generation"] = False
                st.stop()

            with st.spinner("Hang on, we're creating your video..."):
                success = self.attempt_generation(prompt, aspect_ratio)
                if not success:
                    st.error("Both Minimaxi and Segmind attempts failed.")

            st.session_state["generating"] = False
            st.session_state["run_generation"] = False

# -------------------------------------------------------------------
# MAIN ENTRY POINT
# -------------------------------------------------------------------
def main():
    app = Text2Video()
    app.welcome_screen()
    app.handle_input()

if __name__ == "__main__":
    main()
