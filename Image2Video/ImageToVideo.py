import streamlit as st
import requests
import base64
import os
from dotenv import load_dotenv
import time
import json

load_dotenv()

class ImageToVideo:
    if "COST" not in st.session_state:
        st.session_state.COST = 0

    def __init__(self):
        if "generating" not in st.session_state:
            st.session_state["generating"] = False
        if "run_generation" not in st.session_state:
            st.session_state["run_generation"] = False

        # API keys
        self.primary_api_key = os.getenv("MINIMAXI_API_KEY")
        self.secondary_api_key = os.getenv("SEGMIND_API_KEY")

    def image_file_to_base64(self, uploaded_file):
        return base64.b64encode(uploaded_file.read()).decode('utf-8')

    def on_click_generate(self):
        if not st.session_state["generating"]:
            st.session_state["generating"] = True
            st.session_state["run_generation"] = True

    def generate_video_with_primary_model(self, image_base64, prompt):
        try:
            task_id = self._submit_task_to_minimax(image_base64, prompt)
            return self._handle_minimax_task_result(task_id)
        except Exception as e:
            st.error(f"Primary model failed: {str(e)}")
            return None

    def _submit_task_to_minimax(self, image_base64, prompt):
        url = "https://api.minimaxi.chat/v1/video_generation"
        payload = json.dumps({
            "model": "video-01",
            "prompt": prompt,
            "first_frame_image": f"data:image/png;base64,{image_base64}"
        })
        headers = {
            'authorization': f'Bearer {self.primary_api_key}',
            'Content-Type': 'application/json'
        }

        response = requests.post(url, headers=headers, data=payload)
        if response.status_code != 200:
            raise Exception(f"API Error: {response.text}")

        task_id = response.json().get('task_id')
        if not task_id:
            raise Exception("No task ID received")

        return task_id

    def _handle_minimax_task_result(self, task_id):
        start_time = time.time()
        timeout = 300  

        while time.time() - start_time < timeout:
            status, file_id = self._check_minimax_task_status(task_id)

            if status == "Success":
                return self._download_minimax_video(file_id)
            elif status in ["Preparing", "Queueing", "Processing"]:
                time.sleep(10)
            else:
                raise Exception(f"Generation failed with status: {status}")

        raise Exception("Video generation timed out")

    def _check_minimax_task_status(self, task_id):
        url = f"https://api.minimaxi.chat/v1/query/video_generation?task_id={task_id}"
        headers = {'authorization': f'Bearer {self.primary_api_key}'}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Status check failed: {response.text}")
        data = response.json()
        return data['status'], data.get('file_id')

    def _download_minimax_video(self, file_id):
        url = f"https://api.minimaxi.chat/v1/files/retrieve?file_id={file_id}"
        headers = {'authorization': f'Bearer {self.primary_api_key}'}
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception("Failed to get download URL")

        st.session_state.COST = 0.43
        download_url = response.json()['file']['download_url']
        video_response = requests.get(download_url)

        return video_response.content

    def generate_video_with_secondary_model(self, image_base64, prompt):
        """Generate video using Segmind and track cost from response headers."""
        try:
            data = {
                "image": image_base64,
                "prompt": prompt,
                "negative_prompt": "No sudden movements, no fast zooms.",
                "cfg_scale": 0.5,
                "mode": "std",
                "duration": 5
            }
            headers = {'x-api-key': self.secondary_api_key}
            response = requests.post(
                "https://api.segmind.com/v1/kling-image2video",
                json=data,
                headers=headers
            )

            if response.status_code == 200 and "video" in response.headers.get("Content-Type", ""):
                # # Extract credit usage from response headers
                # remaining_credits = response.headers.get("x-remaining-credits")

                # if remaining_credits:
                #     st.session_state.COST = float(remaining_credits)  # Assuming credits are in a numeric format
                # else:
                #     st.session_state.COST = "Unknown"

                st.session_state.COST = 0.28

                return response.content
            
            raise Exception(f"API Error: {response.text}")

        except Exception as e:
            st.error(f"Secondary model failed: {str(e)}")
            return None

    def run(self):
        st.set_page_config(page_title="Image to Video Creator", page_icon="🎨")
        st.title("Image to Video Creator 📷🎥")
        st.subheader("Hello, junior creators! Let's make a movie from a single picture!")
        st.write("1. Upload a fun picture.\n2. Describe what you want to see happen in your video.\n3. Click 'Generate Video' and watch the magic!")

        uploaded_image = st.file_uploader(
            "Step 1: Upload your special image here!",
            type=["jpg", "jpeg", "png"]
        )
        prompt = st.text_input(
            "Step 2: Describe your dream video!",
            "Kitten riding in an aeroplane and looking out the window."
        )
        st.button(
            "Generate Video",
            on_click=self.on_click_generate,
            disabled=st.session_state["generating"]
        )
        if st.session_state["run_generation"]:
            if not uploaded_image or not prompt.strip():
                st.error("Please upload an image and enter a prompt")
                st.session_state.update({"generating": False, "run_generation": False})
                st.stop()
            
            with st.spinner("Creating your video..."):
                image_base64 = self.image_file_to_base64(uploaded_image)

                video_content = self.generate_video_with_primary_model(image_base64, prompt)

                if not video_content:
                    st.warning("Falling back to secondary model...")
                    video_content = self.generate_video_with_secondary_model(image_base64, prompt)

            if video_content:
                st.success(f"Video generated successfully! 🎉 (Cost: {st.session_state.COST} credits)")
                st.video(video_content)
                st.download_button("Download Video Now!", video_content, file_name="Output.mp4", mime="video/mp4")
            else:
                st.error("Failed to generate video with all available models")

            print(f"{st.session_state.COST}$/call")
            st.session_state.update({"generating": False, "run_generation": False})

if __name__ == "__main__":
    app = ImageToVideo()
    app.run()