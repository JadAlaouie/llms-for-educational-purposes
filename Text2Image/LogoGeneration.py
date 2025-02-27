import streamlit as st
import requests
import base64
import random
from io import BytesIO
from PIL import Image
import os 
from dotenv import load_dotenv
import time 

load_dotenv()

API_KEY = os.getenv("SEGMIND_API_KEY")


class ImageGenerator():

    if "COST" not in st.session_state:
        st.session_state.COST = 0

    def welcome_screen(self):
        st.title("LogoGenie 🤖🎨")
        st.subheader("Your AI-powered logo wizard!")

    
    def generate_images_stable_diffusion(self, prompt, negative_prompt, api_key):
        url = "https://api.segmind.com/v1/stable-diffusion-3.5-turbo-txt2img"
        header = {"x-api-key": API_KEY}
        
        total_processing_time = 0  # ✅ Initialize before usage
        images = []
        
        for _ in range(2):
            random_seed = random.randint(0, 99999999999)

            data = {
                "prompt": prompt, 
                "negative_prompt": negative_prompt,
                "steps": 4,
                "guidance_scale": 1, 
                "seed": random_seed,
                "sampler": "dpmpp_2m",
                "scheduler": "sgm_uniform",
                "width": 512,
                "height": 512,
                "aspect_ratio": "custom",
                "batch_size": 1, 
                "image_format": "jpeg",
                "image_quality": 95,
                "base64": True
            }

            try:
                start_time = time.time() 
                response = requests.post(url, json=data, headers=header)
                end_time = time.time()  
                
                response.raise_for_status()
                response_data = response.json()

                image_base64 = response_data.get("image", "")
                if image_base64:
                    processing_time = end_time - start_time 
                    total_processing_time += processing_time  

                    img_data = base64.b64decode(image_base64)
                    img = Image.open(BytesIO(img_data))
                    images.append(img)
            
            except Exception as e:
                st.error(f"Stable Diffusion Error: {e}")
                continue 

        if total_processing_time > 0: 
            print(f"Total processing time: {total_processing_time:.2f} seconds")
            st.session_state.COST = 0.001 * total_processing_time
            print(f"Cost: {st.session_state.COST:.5f}")

        return images if images else None

    
    def generate_images_ideogram(self, prompt, negative_prompt, api_key):
        
        url = "https://api.segmind.com/v1/ideogram-txt-2-img"
        headers = {"x-api-key": API_KEY}

        images = []
        num_images = 2
        for _ in range(num_images):
            random_seed = random.randint(0,9999999)
            data = {
                "magic_prompt_option": "AUTO",
                "negative_prompt": negative_prompt,
                "prompt": prompt, 
                "resolution": "RESOLUTION_1024_1024",
                "seed": random_seed,
                "style_type": "GENERAL"
            }

            try:
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()

                img = Image.open(BytesIO(response.content))
                images.append(img)
                
            except Exception as e:
                st.error(f"Ideogram Error: {e}")
                continue 
        if images:
            st.session_state.COST = num_images * 0.1
            print(st.session_state.COST)
            return images 
        return images if images else None 
    
    def generate_images_with_fallback(self, prompt, negative_prompt, api_key=API_KEY, primary="stable_diffusion",secondary="ideogram"):
        if primary == "ideogram":
            primary_images = self.generate_images_ideogram(prompt, negative_prompt, api_key)
            if primary_images is not None:
                return primary_images

        elif primary == "stable_diffusion":
            primary_images = self.generate_images_stable_diffusion(prompt, negative_prompt, api_key)
            if primary_images is not None:
                return primary_images

        if secondary == "ideogram":
            return self.generate_images_ideogram(prompt, negative_prompt, api_key)
        
        elif secondary == "stable_diffusion":
            return self.generate_images_stable_diffusion(prompt, negative_prompt, api_key)

        return None

    def handle_input(self):
        if "generated_images" not in st.session_state:
            st.session_state["generated_images"] = None 

        with st.sidebar:
            company_name = st.text_input("Company Name", placeholder="Enter Name...")
            company_industry = st.text_input("Company Industry", placeholder="Fitness, Beauty, Restaurants ...")
            styles = st.text_input("Styles", placeholder="Enter some styles you'd like to add!")
            
        negative_prompt = "Low Quality, Blurry, Overly Complex, Cluttered, Harsh Colors, Too Many Details, Cartoonish, Generic Symbols, Excessive Gradients, Poor Contrast, Outdated Style, Unreadable Text, Overlapping Elements, Random Shapes, Neon Colors, Pixelated, Jagged Edges, Distorted, Inconsistent Theme"
        prompt = f"Generate a logo based on the following please: Company Name: {company_name}  Company Industry: {company_industry}  Ensure that Styles: {styles} are followed correctly."
        if st.button("Generate Images", disabled=True if not company_name or not company_industry or not styles else False):
            with st.spinner("Generting Images..."):
                images = self.generate_images_with_fallback(
                    prompt,
                    negative_prompt,
                    API_KEY,
                    primary="stable_diffusion",
                    secondary="ideogram"
                )
            st.session_state["generated_images"] = images 
        
        if st.session_state["generated_images"] is not None:
            images = st.session_state["generated_images"]
            col1, col2 = st.columns(2)
            for i, (col, img) in enumerate(zip([col1, col2], images), start=1):
                with col:
                    st.image(img, caption=f"Generated Image {i}", use_column_width=True)

                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    buffer.seek(0)

                    st.download_button(
                        label=f"Download Image {i}",
                        data=buffer,
                        file_name=f"generated_image_{i}.png",
                        mime="image/png"
                    )
        else:
            st.write("No images generated yet. Click the button above!")


def main():
    app = ImageGenerator()
    app.welcome_screen()
    app.handle_input()

if __name__ == "__main__":
    main()