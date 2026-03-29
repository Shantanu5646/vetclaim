"""
transcript.py
-------------
Transcribes an audio file using OpenAI Whisper API.
Falls back to a placeholder if the key is not configured.
"""

import os


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribes the audio file at audio_path.
    Requires OPENAI_API_KEY in .env.
    Falls back gracefully if the key is missing.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return "[Transcription unavailable — set OPENAI_API_KEY in .env to enable]"

    # Import here so the module loads even without openai installed
    try:
        from openai import OpenAI
    except ImportError:
        return "[Transcription unavailable — run: pip install openai]"

    openai_client = OpenAI(api_key=api_key)

    with open(audio_path, "rb") as f:
        response = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="text",
        )

    return response if isinstance(response, str) else response.text
