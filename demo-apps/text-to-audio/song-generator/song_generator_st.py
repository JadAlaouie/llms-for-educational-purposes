import streamlit as st
import requests
import subprocess
from openai import OpenAI
import os 
from dotenv import load_dotenv
load_dotenv()


OpenAI_key= os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OpenAI_key)
API_KEY = os.getenv("API_KEY")

file_name_male = "John Legend .mp3"
file_path_male = "John Legend .mp3"
file_name_female = "Adele - Rolling in the Deep .mp3"
file_path_female = "Adele - Rolling in the Deep .mp3"

class SongGenerator():
    def generate_lyrics(self, user_input: str):
        completion = client.chat.completions.create(
            model="gpt-4",  # Ensure you're using the correct model
            messages=[
                {"role": "system", "content": "You are a song writer. Generate a short song with five to six lines about the topic provided by the user."},
                {"role": "user", "content": f"Write a song about: {user_input}"}
            ]
        )
        return completion.choices[0].message.content



    def upload_audio(self, api_key, file_name, file_path):
        """Uploads an audio file to Minimax API and returns voice_id and instrumental_id."""
        url = "https://api.minimaxi.chat/v1/music_upload"
        
        payload = {'purpose': 'song'}
        try:
            files = [('file', (file_name, open(file_path, 'rb'), 'audio/mpeg'))]
        except FileNotFoundError:
            print("File not found. Please check the file path.")
            return None, None

        headers = {'authorization': 'Bearer ' + api_key}

        response = requests.post(url, headers=headers, data=payload, files=files)

        if response.status_code == 200:
            try:
                data = response.json()
                voice_id = data.get('voice_id')
                instrumental_id = data.get('instrumental_id')
                if voice_id and instrumental_id:
                    print("Upload successful!")
                    print("Voice ID:", voice_id)
                    print("Instrumental ID:", instrumental_id)
                    return voice_id, instrumental_id
                else:
                    print("Unexpected response structure:", response.text)
                    return None, None
            except Exception as e:
                print("Error parsing response:", e)
                print("Response text:", response.text)
                return None, None
        else:
            print("Upload failed with status code:", response.status_code)
            print("Response text:", response.text)
            return None, None



    def generate_music(self, api_key, voice_id, instrumental_id, lyrics):
        """Generates AI music using Minimax API."""
        url = "https://api.minimaxi.chat/v1/music_generation"

        payload = {
            'refer_voice': voice_id,
            'refer_instrumental': instrumental_id,
            'lyrics': lyrics,
            'model': 'music-01',
            'audio_setting': '{"sample_rate":44100,"bitrate":256000,"format":"mp3"}'
        }
        headers = {'authorization': 'Bearer ' + api_key}

        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 200:
            data = response.json()
            audio_hex = data['data']['audio']
            print("Music generation successful!")
            return audio_hex
        else:
            print("Music generation failed:", response.text)
            return None

    def play_audio(self, audio_hex):
        try:
            mpv_command = ["mpv", "--no-cache", "--no-terminal", "--", "fd://0"]
            mpv_process = subprocess.Popen(
                mpv_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            decoded_hex = bytes.fromhex(audio_hex)
            if mpv_process.stdin:
                mpv_process.stdin.write(decoded_hex)
                mpv_process.stdin.flush()
                mpv_process.stdin.close()
            mpv_process.wait()
            st.success("Playback finished successfully.")
        except FileNotFoundError:
            st.error("mpv is not found in PATH. Please check the installation.")
        except Exception as e:
            st.error(f"Error playing audio: {e}")

    # Function to save audio
    def save_audio(self, audio_hex, output_file="output.mp3"):
        try:
            decoded_audio = bytes.fromhex(audio_hex)
            with open(output_file, "wb") as f:
                f.write(decoded_audio)
            st.success(f"Audio saved to {output_file}")
        except Exception as e:
            st.error(f"Error saving audio: {e}")

    def welcome_screen(self):
        st.title("AI Music Generator")

    def handle_input(self):
        if "generating" not in st.session_state:
           st.session_state.generating = False

        user_input = st.text_area("Describe the song you want to generate:")
        voice_option = st.selectbox("Choose voice:", ("Male", "Female"))

        if st.button("Generate Music", disabled=st.session_state.generating):
            if user_input:
                try:
                    with st.spinner("Generating Lyrics..."):
                        lyrics = self.generate_lyrics(user_input)
                        st.write("Generated Lyrics:")
                        st.write(lyrics)

                    with st.spinner("Uploading Audio..."):
                        if voice_option == "Male":
                            file_name = "John Legend .mp3"
                            file_path = "John Legend .mp3"
                        else:
                            file_name = "Adele - Rolling in the Deep .mp3"
                            file_path = "Adele - Rolling in the Deep .mp3"
                        
                        voice_id, instrumental_id = self.upload_audio(API_KEY, file_name, file_path)
                    if voice_id and instrumental_id:
                        with st.spinner("Generating Music..."):
                            audio_hex = self.generate_music(API_KEY, voice_id, instrumental_id, lyrics)
                        if audio_hex:
                            audio_bytes = bytes.fromhex(audio_hex)
                            self.save_audio(audio_hex)
                            st.audio(audio_bytes, format="audio/mp3")
                finally:
                    st.session_state.generating = False
            else:
                st.error("Please enter a description for the song.")

def main():
    app = SongGenerator()
    app.welcome_screen()
    app.handle_input()

if __name__ == "__main__":
    main()
