import streamlit as st
import requests
from elevenlabs import ElevenLabs
import os 
from dotenv import load_dotenv
from pydub import AudioSegment
import io 

load_dotenv()
segmind_api_key = os.getenv("SEGMIND_API_KEY")
elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
TEXT_LIMIT = 300

ElevenLabs_Segmind_Price =  0.3 / 1000 # this is the price per character
ElevenLabs_Price = 0.003 # price per second 
class TextToSpeech():
    def welcome_screen(self):
        st.title("Turn your text into speech!")
        st.write("Convert text to speech using AI.")

    def generate_audio_elevenlabs(self, prompt, voice_id, api_key):
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

    def generate_audio_segmind(self, prompt, voice, api_key):
        url = "https://api.segmind.com/v1/tts-eleven-labs"  
        data = {"prompt": prompt, "voice": voice}
        headers = {'x-api-key': api_key}
        try:
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                return response.content  
        except Exception as e:
            st.error(f"Error using Segmind API: {e}")
        return None
    
    def handle_input(self, limit=TEXT_LIMIT):
        prompt = st.text_area(
            f"Enter text to convert to speech (max {limit} characters)",
            placeholder="Type your text here...",
            max_chars=limit
        )
        num_characters = len(prompt)

        voice = st.selectbox("Select a voice:",
                             ["Sarah - Engaging Storyteller",
                              "George - Authoritative Narrator",
                               "Will - Friendly Communicator",
                               "Matilda - Soothing Guide",
                               "Aria - Expressive Performer"])
        
        elevenlabs_voice_mapping = {
            "Sarah - Engaging Storyteller": "EXAVITQu4vr4xnSDxMaL",  
            "George - Authoritative Narrator": "CwhRBWXzGAHq8TQ4Fs17",     
            "Will - Friendly Communicator": "IKne3meq5aSn9XLyUdCD",
            "Matilda - Soothing Guide": "FGY2WhTYpPnrIDTdsKH5",
            "Aria - Expressive Performer": "9BWtsMINqrJLrRacOk9x",
        }

        status_placeholder = st.empty()
        generate_audio = st.button("Generate Audio", disabled=not bool(prompt))

        if generate_audio:
            with status_placeholder:
                st.info("Generating Audio with ElevenLabs...")
            
            audio_data = self.generate_audio_elevenlabs(prompt, elevenlabs_voice_mapping.get(voice), elevenlabs_api_key)

            if audio_data:
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
                audio_duration_sec = audio_segment.duration_seconds
                st.session_state.COST = audio_duration_sec * ElevenLabs_Price
                print(st.session_state.COST)
            
            if not audio_data:
                with status_placeholder:
                    st.warning("ElevenLabs failed. Trying Segmind...")
                audio_data = self.generate_audio_segmind(prompt, voice, segmind_api_key)
                st.session_state.COST = num_characters * ElevenLabs_Segmind_Price 
                print(st.session_state.COST)

            status_placeholder.empty()
        
            if audio_data:
                st.success("Audio generated successfully!")
                st.audio(audio_data, format="audio/mp3", start_time=0)
                st.download_button(
                    label="Download Audio",
                    data=audio_data,
                    file_name="output_audio.mp3",
                    mime="audio/mp3"
                )
            else:
                st.error("Failed to generate audio using both APIs")

def main():
    app = TextToSpeech()
    app.welcome_screen()
    app.handle_input()

if __name__ == "__main__":
    main()