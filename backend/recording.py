"""
recording.py
------------
Downloads the Twilio recording, runs speech-to-text via OpenAI Whisper
(or falls back gracefully), then calls the summarizer.
"""

import os
import tempfile
import requests
from requests.auth import HTTPBasicAuth

from backend.transcript import transcribe_audio
from backend.summarizer import summarize_transcript


async def handle_recording_webhook(
    call_sid: str,
    recording_sid: str,
    recording_url: str,
    duration: int,
    account_sid: str,
    auth_token: str,
) -> dict:
    """
    Downloads the MP3 from Twilio, transcribes it, summarizes it.
    Returns a dict that gets merged into the call record.
    """
    result = {
        "recording_sid": recording_sid,
        "recording_url": recording_url,
        "duration_seconds": duration,
        "transcript": None,
        "summary": None,
        "error": None,
    }

    # ── 1. Download audio from Twilio ────────────────────────────────
    mp3_url = recording_url + ".mp3"
    try:
        resp = requests.get(
            mp3_url,
            auth=HTTPBasicAuth(account_sid, auth_token),
            timeout=60,
        )
        resp.raise_for_status()
        audio_bytes = resp.content
    except Exception as e:
        result["error"] = f"Failed to download recording: {e}"
        return result

    # ── 2. Transcribe ────────────────────────────────────────────────
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        transcript = transcribe_audio(tmp_path)
        result["transcript"] = transcript
    except Exception as e:
        result["error"] = f"Transcription failed: {e}"
        return result
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    # ── 3. Summarize ─────────────────────────────────────────────────
    try:
        summary = summarize_transcript(transcript)
        result["summary"] = summary
    except Exception as e:
        result["error"] = f"Summarization failed: {e}"

    return result
