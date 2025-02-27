import streamlit as st
import requests
import base64
import random
from io import BytesIO
from PIL import Image

def generate_images_stable_diffusion(prompt, negative_prompt, api_key):
    """
    Calls the stable-diffusion-3.5-turbo-txt2img endpoint TWICE,
    each time with batch_size=1 and a RANDOM seed,
    to produce two distinct images.
    Returns a list of 2 PIL.Image objects if successful, else None.
    """
    url = "https://api.segmind.com/v1/stable-diffusion-3.5-turbo-txt2img"
    headers = {"x-api-key": api_key}

    images = []
    for _ in range(2):
        # Random seed each time to avoid getting identical images
        random_seed = random.randint(0, 999999999)

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
            "batch_size": 1,      # Single image per request
            "image_format": "jpeg",
            "image_quality": 95,
            "base64": True        # Request base64-encoded output
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            
            # Each single-image request returns "image" (not "images" array)
            image_base64 = response_data.get("image", "")
            if image_base64:
                img_data = base64.b64decode(image_base64)
                img = Image.open(BytesIO(img_data))
                images.append(img)
            else:
                # If the API didn't return a valid image, we consider this a failure
                return None
        except Exception as e:
            st.error(f"Stable Diffusion Error: {e}")
            return None

    if len(images) == 2:
        return images
    else:
        return None


def generate_images_ideogram(prompt, negative_prompt, api_key):
    """
    Calls the ideogram-txt-2-img endpoint TWICE, using the same
    seed each time (can be changed to random if desired).
    Returns a list of 2 PIL.Image objects if successful, otherwise None.
    """
    for _ in range(2):
        # Random seed each time to avoid getting identical images
        random_seed = random.randint(0, 99999)
    
    url = "https://api.segmind.com/v1/ideogram-txt-2-img"
    headers = {"x-api-key": api_key}

    data = {
        "magic_prompt_option": "AUTO",
        "negative_prompt": negative_prompt,
        "prompt": prompt,
        "resolution": "RESOLUTION_1024_1024",
        "seed": random_seed,
        "style_type": "GENERAL"
    }

    images = []
    try:
        # Call endpoint twice
        for _ in range(2):
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            img = Image.open(BytesIO(response.content))
            images.append(img)

        if len(images) == 2:
            return images
        else:
            return None
    except Exception as e:
        st.error(f"Ideogram Error: {e}")
        return None


def generate_images_with_fallback(prompt, negative_prompt, api_key,
                                  primary="stable_diffusion",
                                  secondary="ideogram"):
    """
    Generates 2 images using the primary model first (twice).
    If that fails or returns invalid images, tries the secondary model.
    Returns a list of 2 PIL Images if successful, otherwise None.
    """
    if primary == "stable_diffusion":
        primary_images = generate_images_stable_diffusion(prompt, negative_prompt, api_key)
        if primary_images is not None:
            return primary_images

        # If primary fails, try secondary
        if secondary == "ideogram":
            secondary_images = generate_images_ideogram(prompt, negative_prompt, api_key)
            return secondary_images

    elif primary == "ideogram":
        primary_images = generate_images_ideogram(prompt, negative_prompt, api_key)
        if primary_images is not None:
            return primary_images

        # If primary fails, try secondary
        if secondary == "stable_diffusion":
            secondary_images = generate_images_stable_diffusion(prompt, negative_prompt, api_key)
            return secondary_images

    # If neither worked
    return None


def main():
    st.title("Text-to-Image Generator")

    # Initialize session state for images if not already present
    if "generated_images" not in st.session_state:
        st.session_state["generated_images"] = None

    api_key = "--------"
    prompt = st.text_area("Prompt", value="flying koala inside a car")
    negative_prompt = st.text_area("Negative Prompt", value="low quality, blurry")

    # Button to generate new images
    if st.button("Generate Images"):
        with st.spinner("Generating images..."):
            images = generate_images_with_fallback(
                prompt,
                negative_prompt,
                api_key,
                primary="stable_diffusion",
                secondary="ideogram"
            )
        st.session_state["generated_images"] = images  # store in session_state

    # If images exist in session_state, display them
    if st.session_state["generated_images"] is not None:
        images = st.session_state["generated_images"]
        col1, col2 = st.columns(2)
        for i, (col, img) in enumerate(zip([col1, col2], images), start=1):
            with col:
                st.image(img, caption=f"Generated Image {i}", use_column_width=True)
                
                # Prepare the download button for each image
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)

                st.download_button(
                    label=f"Download Image {i}",
                    data=buffer,
                    file_name=f"generated_image_{i}.png",
                    mime="image/png"
                )
    #else:
        #st.write("No images generated yet. Click the button above!")

if __name__ == "__main__":
    main()
