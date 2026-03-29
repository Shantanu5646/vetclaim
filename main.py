import os
import re
from fastapi import FastAPI, Request
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

app = FastAPI(title="VetClaim Calling Agent")

# Put your real Twilio credentials here or use environment variables
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "YOUR_TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "YOUR_TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "+1YOUR_TWILIO_NUMBER")

# This must be your public URL later, like ngrok
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://your-public-url.ngrok-free.app")

client = Client(ACCOUNT_SID, AUTH_TOKEN)


class CallRequest(BaseModel):
    to: str  # Phone number to call


def format_phone_number(phone_str: str) -> str:
    """Format phone number to E.164 format (+1234567890)"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone_str)
    
    # If it's 10 digits, assume US and add +1
    if len(digits) == 10:
        digits = '1' + digits
    
    # If it's 11 digits starting with 1, keep as is
    if len(digits) == 11 and digits.startswith('1'):
        pass
    elif len(digits) == 11:
        # If 11 digits but doesn't start with 1, assume first digit is country code
        pass
    
    return '+' + digits


@app.get("/")
def home():
    return {
        "status": "running",
        "service": "VetClaim Calling Agent",
        "twilio_configured": ACCOUNT_SID != "YOUR_TWILIO_ACCOUNT_SID"
    }


@app.post("/call")
async def make_call(call_request: CallRequest):
    """Initiate an outbound call to the specified phone number"""
    
    try:
        # Format the phone number
        target_number = format_phone_number(call_request.to)
        
        # Validate phone number has enough digits
        digits_only = re.sub(r'\D', '', target_number)
        if len(digits_only) < 10:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid phone number - must be at least 10 digits"}
            )
        
        # Check if Twilio credentials are configured
        if ACCOUNT_SID == "YOUR_TWILIO_ACCOUNT_SID":
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Twilio credentials not configured",
                    "message": "Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER environment variables",
                    "call_sid": f"mock-call-{digits_only}",
                    "to": target_number,
                    "status": "mock"
                }
            )
        
        # Make the actual call
        call = client.calls.create(
            to=target_number,
            from_=TWILIO_NUMBER,
            url=f"{PUBLIC_BASE_URL}/voice"
        )
        
        return JSONResponse({
            "message": "Call initiated successfully",
            "call_sid": call.sid,
            "to": target_number,
            "from_": TWILIO_NUMBER,
            "status": "initiated"
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Failed to initiate call: {str(e)}",
                "details": "Make sure Twilio credentials are valid and ngrok is running"
            }
        )

@app.api_route("/voice", methods=["GET", "POST"])
async def voice_webhook(request: Request):
    """TwiML voice webhook - handles the actual voice response during a call"""
    response = VoiceResponse()
    response.say(
        "Hello. This is an automated message from VetClaim. "
        "Your VA benefits documents may need review. "
        "Please visit our website to track your claim status. Thank you.",
        voice="alice"
    )
    response.hangup()
    return Response(content=str(response), media_type="application/xml")


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "VetClaim Calling Agent API"
    }