import os
from dotenv import load_dotenv
from sarvamai import SarvamAI
from typing import Optional
from agent import IncomingMessage

load_dotenv()

def process_audio(path, mime_type: Optional[str]) -> IncomingMessage:

    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        return IncomingMessage(
            type="audio",
            path=path,
            caption="[Audio transcription failed: SARVAM_API_KEY environment variable not configured]",
            mime_type=mime_type,
        )

    try:
        client = SarvamAI(api_subscription_key=api_key)
        
        # Open and send the audio file for transcription
        with open(path, "rb") as audio_file:
            response = client.speech_to_text.transcribe(
                file=audio_file,
                model="saaras:v3",
                mode="transcribe"
            )
            
        transcript = response.transcript.strip()
        
        return IncomingMessage(
            type="audio",
            path=path,
            mime_type=mime_type,
            caption=f"[Audio Transcript]: {transcript}"
        )
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return IncomingMessage(
            type="audio",
            path=path,
            caption=f"[Audio Transcription Error]: {str(e)}",
            mime_type=mime_type,
        )
