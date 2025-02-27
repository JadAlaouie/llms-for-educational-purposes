from io import BytesIO
import json
import os 
from PIL import Image
import requests 
import time
import streamlit as st 
import random 
from dotenv import load_dotenv

load_dotenv()

STABILITY_KEY = os.getenv("STABILITY_KEY")

class ImageEditor():
    
    def __init__(self):
        if "user_selection" not in st.session_state:
            st.session_state.user_selection = ""
        if "COST" not in st.session_state:
            st.session_state.COST = 0

    def welcome_screen(self):
        st.title("🎨 AI Image Editor")
        st.markdown("Transform your images using AI-powered editing techniques!")
    
    def display_side(self):
        with st.sidebar:
            self.method = st.selectbox(
                "Editing Method",
                ["Sketch", "Style", "Remove Background"],
                help="Choose the AI editing technique",
                index = 2
            )
            if self.method == "Sketch" or self.method == "Style":
                self.prompt = st.text_input("✨ Prompt", 
                                        placeholder="A futuristic cityscape")
                self.negative_prompt = st.text_input("🚫 Negative Prompt (optional)", 
                                                placeholder="Blurry, low quality")
            self.uploaded_file = st.file_uploader(
                "📤 Upload Image", 
                type=["jpg", "jpeg", "png"],
                help="Select an image file to edit"
            )
                
            st.markdown("---")
            self.generate_btn = st.button("🚀 Generate", use_container_width=True)

    def sketch(self, image, prompt, negative_prompt=""):
        control_strength = 0.7
        seed = random.randint(0,99999)
        output_format = "jpeg"

        host = "https://api.stability.ai/v2beta/stable-image/control/sketch"
        params = {
            "control_strength": control_strength,
            "image": image,
            "seed": seed,
            "output_format": output_format,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
        }

        response = self.send_generation_request(host, params)
        output_image = response.content 
        
        filename, _ = os.path.splitext(os.path.basename(image))
        edited = f"edited_{filename}_{seed}.{output_format}"
        with open(edited, "wb") as f:
            f.write(output_image)
        st.session_state.COST = 0.03
        print(st.session_state.COST)
        return edited

    
    def style(self, image, prompt, negative_prompt=""):
        aspect_ratio = "1:1"
        fidelity = 0.5 
        seed = random.randint(0,999999)
        output_format = "jpeg"

        host = "https://api.stability.ai/v2beta/stable-image/control/style"
        params = {
            "fidelity" : fidelity,
            "image" : image,
            "seed" : seed,
            "output_format": output_format,
            "prompt" : prompt,
            "negative_prompt" : negative_prompt,
            "aspect_ratio": aspect_ratio
        }

        response = self.send_generation_request(host, params)
        output_image = response.content
        
        filename, _ = os.path.splitext(os.path.basename(image))
        edited = f"edited_{filename}_{seed}.{output_format}"
        with open(edited, "wb") as f:
            f.write(output_image)
        st.session_state.COST = 0.04
        print(st.session_state.COST)
        return edited


    def remove_background(self, image):
        
        output_format = "png"
        host = f"https://api.stability.ai/v2beta/stable-image/edit/remove-background"

        params = {
            "image" : image,
            "output_format": output_format
        }

        response = self.send_generation_request(host,params)

        output_image = response.content
        finish_reason = response.headers.get("finish-reason")
        seed = response.headers.get("seed")

        if finish_reason == 'CONTENT_FILTERED':
            raise Warning("Generation failed NSFW classifier")

        filename, _ = os.path.splitext(os.path.basename(image))
        edited = f"edited_{filename}_{seed}.{output_format}"
        with open(edited, "wb") as f:
            f.write(output_image)
        st.session_state.COST = 0.02
        print(st.session_state.COST)
        return edited 
    
    # --------------------------------------------
    # FALLBACK OPTION (IN CASE NEEDED)
    # --------------------------------------------

    # def remove_background_fallback(self, image):
    #     url = "https://api.removal.ai/3.0/remove"

    #     with open(image, "rb") as image_file:
    #         files = {
    #             'image_file': ('image.png', image_file, "image/png")
    #         }
    #         headers = {
    #             "Rm-Token": REMOVAL_API_KEY
    #         }
    #         response = requests.post(url, headers=headers,files=files)
    #         print(response.text)
    #     payload = {
    #         "image_url"
    #     } 
    #     response_data = response.json()
    #     image_url = response_data.get("url")

    def send_generation_request(self, host, params, files = None):
        headers = {
            "Accept": "image/*",
            "Authorization": f"Bearer {STABILITY_KEY}"
        }

        if files is None:
            files = {}

        image = params.pop("image", None)
        mask = params.pop("mask", None)
        if image is not None and image != '':
            files["image"] = open(image, 'rb')
        if mask is not None and mask != '':
            files["mask"] = open(mask, 'rb')
        if len(files)==0:
            files["none"] = ''

        print(f"Sending REST request to {host}...")
        response = requests.post(
            host,
            headers=headers,
            files=files,
            data=params
        )
        if not response.ok:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        return response

    def send_async_generation_request(
        host,
        params,
        files = None
    ):
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {STABILITY_KEY}"
        }

        if files is None:
            files = {}

        image = params.pop("image", None)
        mask = params.pop("mask", None)
        if image is not None and image != '':
            files["image"] = open(image, 'rb')
        if mask is not None and mask != '':
            files["mask"] = open(mask, 'rb')
        if len(files)==0:
            files["none"] = ''

        print(f"Sending REST request to {host}...")
        response = requests.post(
            host,
            headers=headers,
            files=files,
            data=params
        )
        if not response.ok:
            raise Exception(f"HTTP {response.status_code}: {response.text}")

        response_dict = json.loads(response.text)
        generation_id = response_dict.get("id", None)
        assert generation_id is not None, "Expected id in response"

        timeout = int(os.getenv("WORKER_TIMEOUT", 500))
        start = time.time()
        status_code = 202
        while status_code == 202:
            print(f"Polling results at https://api.stability.ai/v2beta/results/{generation_id}")
            response = requests.get(
                f"https://api.stability.ai/v2beta/results/{generation_id}",
                headers={
                    **headers,
                    "Accept": "*/*"
                },
            )

            if not response.ok:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            status_code = response.status_code
            time.sleep(10)
            if time.time() - start > timeout:
                raise Exception(f"Timeout after {timeout} seconds")

        return response

def main():
    editor = ImageEditor()
    editor.welcome_screen()
    editor.display_side()

    if editor.uploaded_file and editor.generate_btn:
        try:
            with st.spinner("🚀 Generating magic..."):
                temp_input = Image.open(editor.uploaded_file)
                temp_path = f"temp_{editor.uploaded_file.name}"
                temp_input.save(temp_path)

                if editor.method == "Sketch":
                    edited_path = editor.sketch(temp_path, editor.prompt, editor.negative_prompt)
                elif editor.method == "Style":
                    edited_path = editor.style(temp_path, editor.prompt, editor.negative_prompt)
                elif editor.method == "Remove Background":
                    edited_path = editor.remove_background(temp_path)
                col1, col2 = st.columns(2)
                with col1:
                    st.image(editor.uploaded_file, 
                           caption="Original Image", 
                           use_column_width=True)
                with col2:
                    st.image(Image.open(edited_path), 
                           caption="Edited Image", 
                           use_column_width=True)

        except Exception as e:
            st.error(f"Error: {str(e)}")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

   
if __name__ == "__main__":
    main()