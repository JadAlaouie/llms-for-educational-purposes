import requests
import base64

api_key = "------"
url = "https://api.segmind.com/v1/kling-text2video"

data = {
    "prompt": "A border collie, wearing clothes made of laser film, wearing a headset, VR glasses, with the Milky Way reflected in his eyes, classic black and white, high-definition quality, surrealism, microcomputer, hacker dress, cyber style, anthropomorphism, reality",
    "negative_prompt": "No buildings, no artificial objects",
    "cfg_scale": 0.5,
    "mode": "std",
    "aspect_ratio": "16:9",
    "duration": 5
}

headers = {"x-api-key": api_key}

response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    # Check what the Content-Type is
    content_type = response.headers.get("Content-Type", "").lower()
    
    if "video" in content_type:
        # The API returned raw video data, so save it.
        video_filename = "output.mp4"
        with open(video_filename, "wb") as f:
            f.write(response.content)
        print(f"Video saved successfully as {video_filename}")
    else:
        print(f"Unexpected content type: {content_type}")
        print(f"Response (first 300 bytes): {response.content[:300]} ...")
else:
    print(f"Request failed with status code {response.status_code}")
    print(f"Error response:\n{response.text}")
