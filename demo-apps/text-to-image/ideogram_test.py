import requests
from io import BytesIO
from PIL import Image

def generate_image_from_prompt(prompt, negative_prompt, api_key, output_file="output_image_ideogram.jpg"):
    url = "https://api.segmind.com/v1/ideogram-txt-2-img"
    
    data = {
        "magic_prompt_option": "AUTO",
        "negative_prompt": negative_prompt,
        "prompt": prompt,
        "resolution": "RESOLUTION_1024_1024",
        "seed": 56698,
        "style_type": "GENERAL"
    }
    
    headers = {'x-api-key': api_key}
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Ensure the request was successful

        # Process binary image response
        img = Image.open(BytesIO(response.content))
        img.save(output_file)
        print(f"Image saved to {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

# Replace with your actual API key
api_key = "-----"

prompt = "flying koala inside a car"
negative_prompt = "low quality, blurry"

generate_image_from_prompt(prompt, negative_prompt, api_key)
