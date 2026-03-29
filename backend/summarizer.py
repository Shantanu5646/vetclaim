"""
summarizer.py
-------------
Extracts VA-claim-relevant information from a call transcript
using Claude (already wired up in backend/main.py).
"""

import os
import json


EXTRACT_PROMPT = """You are a VA claims assistant. A veteran just called the VA to check on their disability claim.
Below is the transcript of that call.

Extract the following information if mentioned. Return ONLY valid JSON.

{
  "claim_status": "current status of the claim (e.g. pending, under review, decision made, etc.)",
  "additional_evidence_needed": ["list of documents or evidence the VA requested"],
  "pending_actions": ["list of actions the veteran needs to take"],
  "deadlines": ["any dates or deadlines mentioned"],
  "next_steps": "brief summary of what happens next",
  "notes": "any other important information from the call"
}

If a field is not mentioned, use null for strings or [] for arrays.

TRANSCRIPT:
{transcript}
"""


def summarize_transcript(transcript: str) -> dict:
    """
    Runs the transcript through Claude and returns structured VA claim data.
    Falls back gracefully if ANTHROPIC_API_KEY is missing.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set — cannot summarize transcript"}

    try:
        import anthropic
    except ImportError:
        return {"error": "anthropic package not installed"}

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": EXTRACT_PROMPT.replace("{transcript}", transcript),
            }
        ],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if Claude wrapped the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_summary": raw}
