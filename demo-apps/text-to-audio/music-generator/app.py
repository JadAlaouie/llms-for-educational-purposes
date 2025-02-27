import os
import asyncio
import aiohttp
import aiofiles
import requests
import streamlit as st
from typing import Dict, Any

# API Keys (Replace with your actual keys or use environment variables)
SEGMIND_API_KEY = "##"
BEATOVEN_API_KEY = "##"

# API URLs
SEGMIND_API_URL = "https://api.segmind.com/v1/meta-musicgen-medium"
BEATOVEN_API_URL = "https://public-api.beatoven.ai/api/v1"

# Existing music generation functions
def generate_music_with_segmind(prompt: str, duration: int = 15, seed: int = 42) -> str:
    """Generate music using the Segmind API."""
    data = {"prompt": prompt, "duration": duration, "seed": seed}
    headers = {'x-api-key': SEGMIND_API_KEY}

    try:
        response = requests.post(SEGMIND_API_URL, json=data, headers=headers)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '').lower()
            output_file = "output_segmind.wav" if content_type == "audio/wav" else "output_segmind.mp3"
            with open(output_file, "wb") as audio_file:
                audio_file.write(response.content)
            return output_file
        else:
            raise Exception(f"Failed to generate audio: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Error generating music with Segmind: {e}")


async def generate_music_with_beatoven(prompt: str, duration: int = 5000, genre: str = "cinematic", mood: str = "happy", tempo: str = "medium") -> str:
    """Generate music using the Beatoven API."""
    async with aiohttp.ClientSession() as session:
        try:
            track_meta = {"prompt": {"text": prompt}, "duration": duration, "genre": genre, "mood": mood, "tempo": tempo}
            create_response = await session.post(f"{BEATOVEN_API_URL}/tracks", json=track_meta, headers={"Authorization": f"Bearer {BEATOVEN_API_KEY}"})
            create_data = await create_response.json()
            track_id = create_data["tracks"][0]

            # Start composition
            compose_response = await session.post(f"{BEATOVEN_API_URL}/tracks/compose/{track_id}", json=track_meta, headers={"Authorization": f"Bearer {BEATOVEN_API_KEY}"})
            compose_data = await compose_response.json()
            task_id = compose_data["task_id"]

            # Check task status
            while True:
                status_response = await session.get(f"{BEATOVEN_API_URL}/tasks/{task_id}", headers={"Authorization": f"Bearer {BEATOVEN_API_KEY}"})
                status_data = await status_response.json()
                if status_data.get("status") == "composing":
                    await asyncio.sleep(10)
                elif status_data.get("status") == "failed":
                    raise Exception("Task failed")
                else:
                    track_url = status_data["meta"]["track_url"]
                    break

            # Download track
            output_file = "output_beatoven.mp3"
            async with session.get(track_url) as track_response:
                if track_response.status == 200:
                    async with aiofiles.open(output_file, "wb+") as f:
                        await f.write(await track_response.read())
                    return output_file
                else:
                    raise Exception("Failed to download track")
        except Exception as e:
            raise Exception(f"Error generating music with Beatoven: {e}")


async def generate_music(prompt: str, genre: str = "cinematic", mood: str = "happy", tempo: str = "medium") -> str:
    """Generate music using Segmind API as the primary option and Beatoven API as the fallback."""
    try:
        return generate_music_with_segmind(prompt)
    except Exception as segmind_error:
        try:
            return await generate_music_with_beatoven(prompt, genre=genre, mood=mood, tempo=tempo)
        except Exception as beatoven_error:
            raise Exception(f"Both Segmind and Beatoven APIs failed: {beatoven_error}")

# Streamlit UI
st.title("🎵 AI Music Generator")
st.write("Generate custom music using AI powered by Segmind and Beatoven APIs")

# Initialize session state
if "generating" not in st.session_state:
    st.session_state.generating = False

# Form UI
with st.form("music_form"):
    prompt = st.text_input("Enter your music description:", placeholder="e.g., 'lo-fi music with a soothing melody'")
    
    col1, col2 = st.columns(2)
    with col1:
        genre = st.selectbox("Genre", ["cinematic", "lofi", "rock", "classical", "jazz"])
    with col2:
        mood = st.selectbox("Mood", ["happy", "sad", "relaxed", "energetic", "calm"])
    
    tempo = st.selectbox("Tempo", ["medium", "fast", "slow", "variable"])
    
    submitted = st.form_submit_button("Generate Music", disabled=st.session_state.generating)

# Process form submission
if submitted:
    if not prompt:
        st.warning("Please enter a music description")
    else:
        st.session_state.generating = True
        with st.spinner("🎼 Composing your music... This may take up to 2 minutes"):
            try:
                output_file = asyncio.run(generate_music(prompt, genre, mood, tempo))
                st.success("🎉 Music generated successfully!")
                st.audio(output_file)
                st.download_button("Download Track", data=open(output_file, "rb"), file_name=output_file, mime="audio/mpeg")
            except Exception as e:
                st.error(f"🚫 Error generating music: {str(e)}")
        st.session_state.generating = False  # Re-enable button after process

st.markdown("---")
