"""
VA Caller Agent — Vapi-powered voice server
--------------------------------------------
POST /start-va-call     — create outbound call via Vapi
POST /vapi/webhook      — receive call events from Vapi
GET  /calls             — list saved call records
GET  /calls/{call_id}   — get a single call record
GET  /health
"""

import os
import json
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from backend.storage import save_call, get_call, list_calls

load_dotenv()

VAPI_API_KEY      = os.getenv("VAPI_API_KEY", "")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID", "")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID", "")
VA_NUMBER         = os.getenv("VA_NUMBER", "+18008271000")

VAPI_BASE_URL = "https://api.vapi.ai"

app = FastAPI(title="VetClaim VA Caller Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ───────────────────────────────────────────────────────────────

class StartCallRequest(BaseModel):
    customer_number: str
    full_name:       Optional[str] = None
    last_four_ssn:   Optional[str] = None
    va_file_number:  Optional[str] = None
    claim_date:      Optional[str] = None
    claim_type:      Optional[str] = "disability"


# ── Helpers ──────────────────────────────────────────────────────────────

def _vapi_headers() -> dict:
    return {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }


def _build_system_prompt(req: StartCallRequest) -> str:
    name_line  = f"Veteran name: {req.full_name}." if req.full_name else ""
    ssn_line   = f"Last 4 of SSN: {req.last_four_ssn}." if req.last_four_ssn else ""
    file_line  = f"VA file number: {req.va_file_number}." if req.va_file_number else ""
    date_line  = f"Claim submitted: {req.claim_date}." if req.claim_date else ""
    type_line  = f"Claim type: {req.claim_type}." if req.claim_type else ""

    claim_details = " ".join(filter(None, [name_line, ssn_line, file_line, date_line, type_line]))

    return f"""You are a call assistant helping a U.S. veteran check the status of their VA disability claim.

STEP 1 — CONSENT DISCLOSURE (say this first, verbatim):
"Hello. This call may be recorded for documentation and note-taking purposes. By staying on the line, you consent to the recording. We are now connecting you to the VA."

Wait 2 seconds.

STEP 2 — STATE THE CLAIM STATUS REQUEST to the VA representative:
"Hello. I am requesting a status update on a VA {req.claim_type or 'disability'} claim. {claim_details} Please provide the current claim status, whether any additional evidence or documents are needed, and any pending actions required. Thank you."

STEP 3 — LISTEN and take notes. Do not interrupt the VA representative.

STEP 4 — After the call, your summary should include:
- Current claim status
- Any documents or evidence the VA has requested
- Any deadlines mentioned
- Next steps for the veteran

IMPORTANT: You are not a lawyer or doctor. Do not give legal or medical advice. Always recommend the veteran work with an accredited VSO for complex questions."""


# ── Routes ───────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {
        "service": "VetClaim VA Caller Agent (Vapi)",
        "status": "running",
        "vapi_configured": bool(VAPI_API_KEY),
    }


@app.post("/start-va-call")
async def start_va_call(req: StartCallRequest):
    """
    Creates an outbound Vapi call to the veteran's number.
    The Vapi assistant handles consent disclosure, then states the claim request to the VA.
    """
    if not VAPI_API_KEY:
        return JSONResponse(status_code=400, content={
            "error": "VAPI_API_KEY not configured",
            "message": "Add VAPI_API_KEY to your .env file",
        })

    system_prompt = _build_system_prompt(req)

    # Use a transient assistant so we can inject the veteran's details dynamically
    body = {
        "assistant": {
            "name": "VetClaim VA Caller",
            "model": {
                "provider": "anthropic",
                "model": "claude-haiku-4-5-20251001",
                "systemPrompt": system_prompt,
                "temperature": 0.3,
            },
            "voice": {
                "provider": "playht",
                "voiceId": "jennifer",
            },
            "firstMessage": (
                "Hello. This call may be recorded for documentation and note-taking purposes. "
                "By staying on the line, you consent to the recording. "
                "We are now connecting to the VA."
            ),
            "recordingEnabled": True,
            "hipaaEnabled": False,
            "analysisPlan": {
                "summaryPrompt": (
                    "Summarize this VA call. Include: "
                    "1. Current claim status. "
                    "2. Documents or evidence requested by the VA. "
                    "3. Any deadlines mentioned. "
                    "4. Next steps for the veteran. "
                    "Return as JSON with keys: claim_status, evidence_needed, deadlines, next_steps, notes."
                ),
                "successEvaluationPrompt": "Was the VA agent able to provide a claim status update? Answer yes or no.",
                "successEvaluationRubric": "PassFail",
            },
        },
        "customer": {
            "number": req.customer_number,
        },
    }

    # Attach phone number ID if configured
    if VAPI_PHONE_NUMBER_ID:
        body["phoneNumberId"] = VAPI_PHONE_NUMBER_ID

    try:
        resp = requests.post(
            f"{VAPI_BASE_URL}/call",
            json=body,
            headers=_vapi_headers(),
            timeout=30,
        )

        # Sometimes Vapi returns non-JSON (e.g. empty body or error HTML). handle robustly.
        try:
            data = resp.json()
        except ValueError:
            text_body = resp.text.strip()
            if resp.status_code not in (200, 201):
                return JSONResponse(status_code=resp.status_code, content={
                    "error": "Vapi did not return valid JSON",
                    "body": text_body or "(empty response)",
                })
            return JSONResponse(status_code=500, content={
                "error": "Vapi returned invalid JSON",
                "body": text_body or "(empty response)",
            })

        if resp.status_code not in (200, 201):
            return JSONResponse(status_code=resp.status_code, content=data)

        call_id = data.get("id", "unknown")
        save_call(call_id, {
            "call_id": call_id,
            "customer_number": req.customer_number,
            "status": "initiated",
            "full_name": req.full_name,
            "claim_type": req.claim_type,
            "vapi_response": data,
        })

        return JSONResponse({
            "message": "Call initiated",
            "call_id": call_id,
            "status": data.get("status", "queued"),
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/vapi/webhook")
async def vapi_webhook(request: Request):
    """
    Receives server-sent events from Vapi:
    - call-started, call-ended, transcript, recording, analysis
    Saves artifacts to local call records.
    """
    try:
        event = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    event_type = event.get("message", {}).get("type") or event.get("type", "unknown")
    call       = event.get("message", {}).get("call") or event.get("call", {})
    call_id    = call.get("id", "unknown")

    if event_type == "end-of-call-report":
        artifact  = event.get("message", {}).get("artifact", {})
        analysis  = event.get("message", {}).get("analysis", {})
        save_call(call_id, {
            "status":        "completed",
            "transcript":    artifact.get("transcript"),
            "recording_url": artifact.get("recordingUrl"),
            "messages":      artifact.get("messages", []),
            "summary":       analysis.get("summary"),
            "success_eval":  analysis.get("successEvaluation"),
            "duration":      call.get("endedAt"),
        })

    elif event_type == "transcript":
        transcript = event.get("message", {}).get("transcript", "")
        save_call(call_id, {"live_transcript": transcript})

    elif event_type in ("call-started", "call-ended"):
        save_call(call_id, {"status": event_type})

    return JSONResponse({"ok": True, "received": event_type})


@app.get("/calls")
def list_all_calls():
    return list_calls()


@app.get("/calls/{call_id}")
def get_single_call(call_id: str):
    data = get_call(call_id)
    if not data:
        return JSONResponse(status_code=404, content={"error": "Call not found"})
    return data


@app.get("/health")
def health():
    return {"status": "healthy", "service": "VetClaim VA Caller Agent (Vapi)"}


# ── Legacy /call endpoint so existing frontend still works ────────────────

class LegacyCallRequest(BaseModel):
    to: str

@app.post("/call")
async def legacy_call(req: LegacyCallRequest):
    sr = StartCallRequest(customer_number=req.to)
    return await start_va_call(sr)
