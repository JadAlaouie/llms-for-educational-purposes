import requests
import base64
import sys

def image_file_to_base64(image_path):
    with open(image_path, 'rb') as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode('utf-8')

def image_url_to_base64(image_url):
    response = requests.get(image_url)
    image_data = response.content
    return base64.b64encode(image_data).decode('utf-8')

api_key = "-------"
url = "https://api.segmind.com/v1/kling-image2video"

# Request payload
data = {
    "image": image_url_to_base64("https://segmind-sd-models.s3.amazonaws.com/display_images/kling_ip.jpeg"),  
    "prompt": "Kitten riding in an aeroplane and looking out the window.",
    "negative_prompt": "No sudden movements, no fast zooms.",
    "cfg_scale": 0.5,
    "mode": "std",
    "duration": 5
}

headers = {
    'x-api-key': api_key
}

# Make the request (one run only!)
print("Sending request to the API...")
response = requests.post(url, json=data, headers=headers)

# Log basic details
print(f"Status code: {response.status_code}")
content_type = response.headers.get("content-type", "")
print(f"Content-Type: {content_type}")
print(f"Response length: {len(response.content)} bytes")

if response.status_code == 200:
    # Check if we're dealing with JSON or raw binary data based on Content-Type
    if "application/json" in content_type.lower():
        print("Response is JSON. Attempting to parse as JSON...")
        try:
            result = response.json()
            # Check if there's a field that contains the video URL
            video_url = result.get("video_url")  # Adjust if the actual key is different
            if not video_url:
                print("No video_url in JSON response. Here is the full JSON for debugging:")
                print(result)
            else:
                # Now download the video from the returned URL
                print(f"Downloading video from: {video_url}")
                video_response = requests.get(video_url)
                if video_response.status_code == 200:
                    with open("output.mp4", "wb") as f:
                        f.write(video_response.content)
                    print("Video downloaded successfully as output.mp4")
                else:
                    print(f"Failed to download from {video_url} with status code {video_response.status_code}")
        except ValueError:
            print("Failed to parse the JSON response. Here is the raw content for debugging:")
            print(response.content)
    else:
        print("Response does not appear to be JSON. Treating it as raw binary data...")
        # Attempt to save directly as a video (mp4)
        video_filename = "output.mp4"
        try:
            with open(video_filename, "wb") as f:
                f.write(response.content)
            print(f"Video saved successfully as {video_filename}")
        except Exception as e:
            print(f"Error saving video: {e}")
            print("Here is the raw content for debugging:")
            print(response.content[:200], "...")  # Print only first 200 bytes to avoid huge log
else:
    print("Request failed.")
    print(f"Status code: {response.status_code}")
    print(f"Error response:\n{response.text}")
    sys.exit(1)
