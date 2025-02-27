import streamlit as st
import requests
from elevenlabs import ElevenLabs
import os 
from dotenv import load_dotenv

segmind_api_key = os.getenv("SEGMIND_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
TEXT_LIMIT = 300
load_dotenv()

class TextToSpeech():
    def welcome_screen(self):
        st.title("Turn your text into speech!")
        st.write("Convert text to speech using AI.")

    def generate_audio_segmind(self, prompt, voice, api_key):
        url = "https://api.segmind.com/v1/tts-eleven-labs"
        headers = {'x-api-key': api_key}
        data = {"text": prompt, "voice": voice}

        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return response.content  
        else:
            return None

    def generate_audio_elevenlabs(self,prompt, voice_id, api_key):
        try:
            client = ElevenLabs(api_key=api_key)
            audio_generator = client.generate(
                text=prompt,
                voice=voice_id,
                output_format="mp3_44100_128",
            )
            audio_binary = b"".join(audio_generator)
            return audio_binary
        except Exception as e:
            st.error(f"Error using ElevenLabs API: {e}")
            return None
    
    def handle_input(self, limit=TEXT_LIMIT):
        prompt = st.text_area(
            "Enter text to convert to speech (max {limit})",
            placeholder="Type your text here...",
            max_chars=limit
        )

        voice = st.selectbox("Select a voice: ",
                             ["Sarah","George","Will","Matilda","Aria"])
        
        elevenlabs_voice_mapping = {
            "Sarah": "EXAVITQu4vr4xnSDxMaL",  
            "George": "CwhRBWXzGAHq8TQ4Fs17",     
            "Will": "IKne3meq5aSn9XLyUdCD",
            "Matilda": "FGY2WhTYpPnrIDTdsKH5",
            "Aria": "9BWtsMINqrJLrRacOk9x",
        }

        status_placeholder = st.empty()

        generate_audio = st.button("Generate Audio", disabled=True if not prompt else False)
        
        if generate_audio:
            with status_placeholder:
                st.info("Generating Audio...")
            
            audio_data = self.generate_audio_segmind(prompt, voice, segmind_api_key)

            if not audio_data:
                with status_placeholder:
                    st.info("Generating Audio...")
                    audio_data = self.generate_audio_elevenlabs(prompt, elevenlabs_voice_mapping.get(voice), elevenlabs_api_key)

            status_placeholder.empty()
        
            if audio_data:
                st.success("Audio generated successfully!")
                st.audio(audio_data, format="audio/mp3", start_time=0)
                st.download_button(
                    label = "Download Audio",
                    data= audio_data,
                    file_name = "output_audio.mp3",
                    mime= "audio/mp3"
                )
            else:
                st.error("Failed to generate audio using both APIs")

def main():
    app = TextToSpeech()
    app.welcome_screen()
    app.handle_input()

if __name__ == "__main__":
    main()