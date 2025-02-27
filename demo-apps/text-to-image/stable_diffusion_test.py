import requests
import base64

def generate_image_from_prompt(prompt, negative_prompt, api_key, output_file="output_image_stable_diffusion.jpg"):
    url = "https://api.segmind.com/v1/stable-diffusion-3.5-turbo-txt2img"
    
    # Request payload
    data = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "steps": 4,
        "guidance_scale": 1,
        "seed": 98552302,
        "sampler": "dpmpp_2m",
        "scheduler": "sgm_uniform",
        "width": 512,
        "height": 512,
        "aspect_ratio": "custom",
        "batch_size": 1,
        "image_format": "jpeg",
        "image_quality": 95,
        "base64": True  # Set this to True to get the image in base64 format
    }
    
    headers = {'x-api-key': api_key}
    
    # Make the API request
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        response_data = response.json()
        # Decode the base64 image
        image_base64 = response_data.get('image', '')
        if image_base64:
            with open(output_file, "wb") as img_file:
                img_file.write(base64.b64decode(image_base64))
            print(f"Image successfully saved to {output_file}")
        else:
            print("No image found in the response.")
    else:
        print(f"Failed to generate image. Status code: {response.status_code}, Response: {response.content}")

# Replace 'YOUR_API_KEY' with your actual API key
api_key = "-----"

# Take the prompt input from the user
prompt = "flying koala inside a car"
negative_prompt = "low quality, blurry"

# Generate the image and save it as output_image.jpg
generate_image_from_prompt(prompt, negative_prompt, api_key)
