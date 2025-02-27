import streamlit as st
import requests
import base64

# ----------------------------------------
# Session state initialization
# ----------------------------------------
if "generating" not in st.session_state:
    st.session_state["generating"] = False  # Is the app currently generating a video?
if "run_generation" not in st.session_state:
    st.session_state["run_generation"] = False  # Should we run the generation logic?

# ----------------------------------------
# Utility functions
# ----------------------------------------
def image_file_to_base64(uploaded_file):
    return base64.b64encode(uploaded_file.read()).decode('utf-8')

def generate_video(image_base64, prompt):
    url = "https://api.segmind.com/v1/kling-image2video"
    data = {
        "image": image_base64,
        "prompt": prompt,
        "negative_prompt": "No sudden movements, no fast zooms.",
        "cfg_scale": 0.5,
        "mode": "std",
        "duration": 5
    }
    headers = {'x-api-key': "----"}
    return requests.post(url, json=data, headers=headers)

# ----------------------------------------
# Callback to trigger generation
# ----------------------------------------
def on_click_generate():
    """
    This function is called when the user clicks 'Generate Video'.
    It sets flags in session_state, then Streamlit re-runs the script.
    """
    # If we are already generating, do nothing
    if st.session_state["generating"]:
        return
    # Otherwise, set the flags
    st.session_state["generating"] = True
    st.session_state["run_generation"] = True

# ----------------------------------------
# Streamlit page config and layout
# ----------------------------------------
st.set_page_config(page_title="Image to Video Creator", page_icon="🎨")

st.title("Image to Video Creator 📷🎥")
st.subheader("Hello, junior creators! Let's make a movie from a single picture!")
st.write(
    "1. Upload a fun picture.\n"
    "2. Describe what you want to see happen in your video.\n"
    "3. Click 'Generate Video' and watch the magic happen!"
)

# ----------------------------------------
# UI elements
# ----------------------------------------
uploaded_image = st.file_uploader(
    "Step 1: Upload your special image here!",
    type=["jpg", "jpeg", "png"]
)

prompt = st.text_input(
    "Step 2: Describe your dream video!",
    "Kitten riding in an aeroplane and looking out the window."
)

# The button is tied to the callback. The `disabled` parameter depends on whether we're generating.
st.button(
    "Generate Video",
    on_click=on_click_generate,
    disabled=st.session_state["generating"]
)

# ----------------------------------------
# Main logic: Run generation if triggered
# ----------------------------------------
if st.session_state["run_generation"]:

    # Basic validations
    if not uploaded_image:
        st.error("Oops! You need to upload an image first.")
        # Reset generating flags because we won't run the API call
        st.session_state["generating"] = False
        st.session_state["run_generation"] = False
        st.stop()

    if not prompt.strip():
        st.error("Oops! You need to enter a prompt first.")
        # Reset generating flags because we won't run the API call
        st.session_state["generating"] = False
        st.session_state["run_generation"] = False
        st.stop()

    # If we pass validations, show spinner and call the API
    with st.spinner("Hold on tight! We're creating your video..."):
        image_base64 = image_file_to_base64(uploaded_image)
        response = generate_video(image_base64, prompt)

    # Handle the response
    if response.status_code == 200:
        content_type = response.headers.get("Content-Type", "").lower()
        if "video" in content_type:
            st.success("Video generated successfully! 🎉")
            st.video(response.content)
        else:
            st.error("API returned 200 but does not appear to be video data.")
            st.write("Here is what we received from the server:")
            st.write(response.text)
    else:
        st.error(f"Oops! We got an error: {response.status_code}")
        st.write("Server response:")
        st.write(response.text)

    # Re-enable the button after generation finishes
    st.session_state["generating"] = False
    st.session_state["run_generation"] = False
