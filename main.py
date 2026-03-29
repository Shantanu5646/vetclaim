"""
VA Caller Agent — Twilio voice server
--------------------------------------
Handles:
  POST /start-call       — place the outbound call to the veteran's phone
  POST /outbound         — TwiML: consent disclosure + bridge to VA
  POST /recording-status — Twilio webhook when recording is ready
  GET  /calls            — list logged calls
  GET  /calls/{call_sid} — get a single call's transcript + summary
"""

import os
import re
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Optional
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Dial
from dotenv import load_dotenv

from backend.recording import handle_recording_webhook
from backend.storage import save_call, get_call, list_calls

load_dotenv()

ACCOUNT_SID   = os.getenv("TWILIO_ACCOUNT_SID",  "YOUR_TWILIO_ACCOUNT_SID")
AUTH_TOKEN    = os.getenv("TWILIO_AUTH_TOKEN",    "YOUR_TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER",  "+1YOUR_TWILIO_NUMBER")
YOUR_NUMBER   = os.getenv("YOUR_PHONE_NUMBER",    "+1YOUR_PERSONAL_NUMBER")
VA_NUMBER     = os.getenv("VA_NUMBER",            "+18008271000")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL",    "https://your-ngrok-url.ngrok-free.app")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

app = FastAPI(title="VetClaim VA Caller Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _clean(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        digits = "1" + digits
    return "+" + digits


# ── Models ──────────────────────────────────────────────────────────────

class StartCallRequest(BaseModel):
    veteran_phone: Optional[str] = None   # defaults to YOUR_NUMBER if omitted
    full_name:     Optional[str] = None
    last_four_ssn: Optional[str] = None
    va_file_number: Optional[str] = None
    claim_date:    Optional[str] = None
    claim_type:    Optional[str] = None


# ── Endpoints ────────────────────────────────────────────────────────────

@app.get("/")
def home():
    return {
        "service": "VetClaim VA Caller Agent",
        "status": "running",
        "twilio_configured": ACCOUNT_SID != "YOUR_TWILIO_ACCOUNT_SID",
    }


@app.post("/start-call")
async def start_call(req: StartCallRequest):
    """
    Places an outbound call to the veteran (or YOUR_NUMBER).
    When the veteran answers they hear the consent notice, then get bridged to the VA.
    """
    if ACCOUNT_SID == "YOUR_TWILIO_ACCOUNT_SID":
        return JSONResponse(status_code=400, content={
            "error": "Twilio credentials not configured",
            "message": "Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER in .env",
        })

    target = _clean(req.veteran_phone) if req.veteran_phone else YOUR_NUMBER

    # Pass claim details as query params to /outbound so TwiML can use them
    params = []
    if req.full_name:      params.append(f"full_name={req.full_name.replace(' ', '+')}")
    if req.last_four_ssn:  params.append(f"last_four_ssn={req.last_four_ssn}")
    if req.va_file_number: params.append(f"va_file_number={req.va_file_number.replace(' ', '+')}")
    if req.claim_date:     params.append(f"claim_date={req.claim_date.replace('/', '-')}")
    if req.claim_type:     params.append(f"claim_type={req.claim_type.replace(' ', '+')}")

    outbound_url = f"{PUBLIC_BASE_URL}/outbound"
    if params:
        outbound_url += "?" + "&".join(params)

    try:
        call = client.calls.create(
            to=target,
            from_=TWILIO_NUMBER,
            url=outbound_url,
        )
        # Save initial call record
        save_call(call.sid, {
            "call_sid": call.sid,
            "to": target,
            "status": "initiated",
            "full_name": req.full_name,
            "claim_type": req.claim_type,
        })
        return JSONResponse({"message": "Call initiated", "call_sid": call.sid, "to": target})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.api_route("/outbound", methods=["GET", "POST"])
async def outbound(request: Request):
    """
    TwiML webhook:
    1. Reads consent disclosure to the veteran
    2. Dials the VA and records the bridged call
    3. On hang-up, triggers /recording-status
    """
    params = dict(request.query_params)

    # Rebuild claim info from query params
    full_name    = params.get("full_name",    "").replace("+", " ") or None
    last_four    = params.get("last_four_ssn") or None
    va_file      = params.get("va_file_number", "").replace("+", " ") or None
    claim_date   = params.get("claim_date", "").replace("-", "/") or None
    claim_type   = params.get("claim_type", "").replace("+", " ") or "disability claim"

    name_phrase  = f"for {full_name}" if full_name else ""
    ssn_phrase   = f"Last 4 S S N: {last_four}." if last_four else ""
    file_phrase  = f"V A file number: {va_file}." if va_file else ""
    date_phrase  = f"Claim submitted: {claim_date}." if claim_date else ""

    status_msg = (
        f"Hello. I am requesting a status update on my V A {claim_type} {name_phrase}. "
        f"{ssn_phrase} {file_phrase} {date_phrase} "
        "Please tell me the current status, whether additional evidence is needed, "
        "and any pending actions required from me. Thank you."
    ).strip()

    response = VoiceResponse()

    # ── Consent disclosure (required for all-party consent states) ──────
    response.say(
        "This call will be recorded for note-taking and documentation purposes. "
        "By staying on the line, you consent to the recording. "
        "Connecting to the V A now.",
        voice="alice",
    )
    response.pause(length=1)

    # ── Bridge to VA with recording ─────────────────────────────────────
    dial = Dial(
        record="record-from-answer-dual",
        recording_status_callback=f"{PUBLIC_BASE_URL}/recording-status",
        recording_status_callback_method="POST",
        action=f"{PUBLIC_BASE_URL}/call-complete",
        timeout=60,
    )
    dial.number(
        VA_NUMBER,
        status_callback=f"{PUBLIC_BASE_URL}/call-complete",
        status_callback_event="completed",
        status_callback_method="POST",
    )
    # Inject the claim status request message after VA answers
    response.say(status_msg, voice="alice", rate="90%")
    response.append(dial)

    return Response(content=str(response), media_type="application/xml")


@app.post("/call-complete")
async def call_complete(request: Request):
    """Called by Twilio when the dialed leg ends."""
    form = await request.form()
    call_sid    = form.get("CallSid", "")
    call_status = form.get("CallStatus", "")
    duration    = form.get("CallDuration", "0")

    save_call(call_sid, {"status": call_status, "duration_seconds": int(duration)})
    return Response(content="<Response/>", media_type="application/xml")


@app.post("/recording-status")
async def recording_status(request: Request):
    """
    Twilio fires this when a recording is ready.
    Downloads the audio, transcribes it, summarizes it, saves everything.
    """
    form = await request.form()
    recording_url = form.get("RecordingUrl", "")
    call_sid      = form.get("CallSid", "")
    recording_sid = form.get("RecordingSid", "")
    duration      = form.get("RecordingDuration", "0")

    if not recording_url:
        return JSONResponse({"error": "No recording URL"}, status_code=400)

    result = await handle_recording_webhook(
        call_sid=call_sid,
        recording_sid=recording_sid,
        recording_url=recording_url,
        duration=int(duration),
        account_sid=ACCOUNT_SID,
        auth_token=AUTH_TOKEN,
    )

    save_call(call_sid, result)
    return JSONResponse({"status": "processed", "call_sid": call_sid})


@app.get("/calls")
def list_all_calls():
    return list_calls()


@app.get("/calls/{call_sid}")
def get_single_call(call_sid: str):
    data = get_call(call_sid)
    if not data:
        return JSONResponse(status_code=404, content={"error": "Call not found"})
    return data


@app.get("/health")
def health():
    return {"status": "healthy", "service": "VetClaim VA Caller Agent"}


# ── Also keep the legacy /call endpoint so the frontend still works ─────

class LegacyCallRequest(BaseModel):
    to: str

@app.post("/call")
async def legacy_call(req: LegacyCallRequest):
    """Legacy endpoint — wraps /start-call for the existing frontend."""
    sr = StartCallRequest(veteran_phone=req.to)
    return await start_call(sr)
