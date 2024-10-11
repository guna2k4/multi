import streamlit as st
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import assemblyai as aai
from translate import Translator
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
import uuid
from pathlib import Path

# Global configuration
ASSEMBLY_AI_API_KEY = "6fcc70ef9823441d97116e3f8c5c5601"
ELEVEN_LABS_API_KEY = "sk_ee2386ac3b2717ff6dab24905cb69d0d49a2f9199136e7e8"

# Supported languages
SUPPORTED_LANGUAGES = {
    "tamil":"Ta",
    "Spanish": "es",
    "Turkish": "tr",
    "Japanese": "ja",
    "French": "fr",
    "German": "de",
    "Chinese": "zh",
    "english":"en"
}

# Define functions for audio processing
def audio_transcription(audio_file):
    aai.settings.api_key = ASSEMBLY_AI_API_KEY
    transcriber = aai.Transcriber()
    transcription = transcriber.transcribe(audio_file)
    return transcription

def text_translation(text, target_lang_code):
    translator = Translator(from_lang="en", to_lang=target_lang_code)
    return translator.translate(text)

def text_to_speech(text):
    client = ElevenLabs(api_key=ELEVEN_LABS_API_KEY)
    response = client.text_to_speech.convert(
        voice_id="pNInz6obpgDQGcFmaJgB",  # Replace with valid Voice ID
        text=text,
    )
    save_file_path = Path(f"{uuid.uuid4()}.mp3")
    with open(save_file_path, "wb") as audio_file:
        for chunk in response:
            audio_file.write(chunk)
    return save_file_path

# Function to record audio
def record_audio(duration):
    st.write("Recording...")
    recording = sd.rec(int(duration * 44100), samplerate=44100, channels=2, dtype='int16')
    sd.wait()  # Wait until the recording is finished
    st.write("Recording finished.")
    return recording

# Layout
st.set_page_config(page_title="Chat App", layout="wide")

# Sidebar for user selection
user = st.sidebar.selectbox("Select User", ["User 1", "User 2"])

# Placeholder for the conversation
if "conversation" not in st.session_state:
    st.session_state.conversation = []

# Function to handle conversation
def add_to_conversation(user, text, translated_audio_path):
    st.session_state.conversation.append({
        "user": user,
        "text": text,
        "audio_path": translated_audio_path
    })

# User 1 or User 2 interaction
if user == "User 1":
    st.title("User 1: Send Voice Message")
else:
    st.title("User 2: Send Voice Message")

# Record audio
duration = st.slider("Select duration (seconds)", 1, 10, 5)
if st.button("Record"):
    audio_data = record_audio(duration)
    wav_file = "recorded_audio.wav"
    write(wav_file, 44100, audio_data)
    st.success("Audio recorded and saved.")
    
    # Transcribe audio
    transcription_response = audio_transcription(wav_file)
    if transcription_response.status == aai.TranscriptStatus.error:
        st.error("Transcription Error")
    else:
        text = transcription_response.text
        st.success("Transcription successful!")
        
        # Select language for translation
        selected_language = st.selectbox("Select Language for Translation", list(SUPPORTED_LANGUAGES.keys()))
        lang_code = SUPPORTED_LANGUAGES[selected_language]
        translation = text_translation(text, lang_code)
        
        # Convert text to speech
        translated_audio_path = text_to_speech(translation)
        
        # Add to conversation
        add_to_conversation(user, translation, translated_audio_path)

# Display the conversation
st.header("Conversation")
for message in st.session_state.conversation:
    if message["user"] == "User 1":
        st.markdown(f"**User 1:** {message['text']}")
    else:
        st.markdown(f"**User 2:** {message['text']}")
    
    # Play the translated audio
    with open(message["audio_path"], "rb") as audio_file:
        audio_bytes = audio_file.read()
    st.audio(audio_bytes)

