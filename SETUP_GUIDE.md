# VetClaim AI - Setup Guide

## ✅ Completed Setup Steps

### 1️⃣ Project Folder Created
```bash
✓ Folder: vetclaim (at /Users/varunyerram/Desktop/hackathon_VetAI/vetclaim)
```

### 2️⃣ Python Virtual Environment
```bash
✓ Virtual environment created: .venv
✓ Python version: 3.12.3
```

**To activate:**
```bash
source .venv/bin/activate
```

### 3️⃣ Packages Installed
```bash
✓ twilio 9.10.4
✓ fastapi 0.135.2
✓ uvicorn 0.42.0
✓ anthropic (for AI backend)
✓ python-dotenv (for environment variables)
✓ python-multipart
```

**Full requirements:**
```bash
pip install twilio "fastapi[standard]" "uvicorn[standard]" anthropic python-dotenv python-multipart
```

### 4️⃣ Main App File Created
```bash
✓ main.py (root) - Twilio calling agent
✓ backend/main.py - VetClaim AI backend
✓ frontend/ - React/Vite frontend
```

### 5️⃣ Run the Server

**Option A - Calling Agent (Port 8000):**
```bash
source .venv/bin/activate
uvicorn main:app --reload
```

Shows:
```
http://127.0.0.1:8000
```

**Option B - VetClaim Backend (Port 8001):**
```bash
source .venv/bin/activate
cd backend
uvicorn main:app --reload --port 8001
```

**Option C - Frontend (Port 5173):**
```bash
cd frontend
npm run dev
```

### 6️⃣ Test Locally
Open in browser: **http://127.0.0.1:8000**

Should see:
```json
{"status":"running"}
```

Test the calling agent via Swagger UI:
```
http://127.0.0.1:8000/docs
```

Click the `/call` endpoint and execute to trigger a call.

---

## 🔧 Setup Twilio for Outbound Calls

### Step 1: Create a Free Twilio Account
1. Go to https://www.twilio.com/console
2. Sign up for a free account
3. You'll get:
   - **Account SID**
   - **Auth Token**
   - **Twilio Phone Number** (assigned automatically)

### Step 2: Create Your .env File
Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
PUBLIC_BASE_URL=https://your-ngrok-url.ngrok-free.app
```

### Step 3: Expose Your Local Server with ngrok

**Install ngrok** (if not already installed):
```bash
brew install ngrok/ngrok/ngrok
```

**Run ngrok to expose port 8000:**
```bash
ngrok http 8000
```

You'll see output like:
```
Forwarding https://abc123.ngrok-free.app -> http://127.0.0.1:8000
```

Copy the HTTPS URL and update `.env`:
```
PUBLIC_BASE_URL=https://abc123.ngrok-free.app
```

### Step 4: Run the Server with Environment Variables
```bash
source .venv/bin/activate
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_PHONE_NUMBER="+1234567890"
export PUBLIC_BASE_URL="https://abc123.ngrok-free.app"
uvicorn main:app --reload
```

Or if using `.env` file with python-dotenv, just run:
```bash
source .venv/bin/activate
uvicorn main:app --reload
```

### Step 5: Trigger a Test Call

Go to Swagger UI:
```
http://127.0.0.1:8000/docs
```

1. Find the `/call` POST endpoint
2. Click **"Try it out"**
3. Click **"Execute"**

The endpoint will call the phone number specified in `main.py` with your automated message.

---

## 📋 Complete One-Command Setup Summary

```bash
# 1. Create and navigate to folder
mkdir -p ~/Desktop/hackathon_VetAI/vetclaim
cd ~/Desktop/hackathon_VetAI/vetclaim

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install packages
pip install twilio "fastapi[standard]" "uvicorn[standard]" anthropic python-dotenv python-multipart

# 4. Create .env file (copy from .env.example and add credentials)
cp .env.example .env

# 5. Run the server
uvicorn main:app --reload

# 6. In another terminal, expose with ngrok
ngrok http 8000
```

---

## 🎯 What Each Endpoint Does

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check - shows `{"status":"running"}` |
| `/call` | POST | Initiates an outbound call to the target number |
| `/voice` | GET/POST | TwiML webhook - defines what happens during the call |
| `/docs` | GET | Interactive Swagger UI for testing endpoints |

---

## 🚀 Next Steps

1. **Add Twilio Credentials** - Fill in `.env` with your Account SID, Auth Token, and Phone Number
2. **Generate ngrok URL** - Run `ngrok http 8000` and update `PUBLIC_BASE_URL`
3. **Run the Server** - Execute `uvicorn main:app --reload`
4. **Test the Call** - Go to `/docs` and click Execute on `/call` endpoint
5. **Customize Messages** - Edit the `response.say()` text in `/voice` endpoint
6. **Add Interactivity** - Use `Gather` for collecting key presses (see Advanced section below)

---

## 🔊 Advanced: Handle Button Presses

To let the called person press buttons:

```python
from twilio.twiml.voice_response import Gather

@app.api_route("/voice", methods=["GET", "POST"])
async def voice_webhook(request: Request):
    response = VoiceResponse()
    gather = Gather(num_digits=1, action="/handle-key", method="POST")
    gather.say(
        "Press 1 to hear the message again. "
        "Press 2 to end the call."
    )
    response.append(gather)
    response.say("No input received. Goodbye.")
    return Response(content=str(response), media_type="application/xml")

@app.api_route("/handle-key", methods=["GET", "POST"])
async def handle_key(request: Request):
    form = await request.form()
    digit = form.get("Digits")
    
    response = VoiceResponse()
    if digit == "1":
        response.say("Repeating the message...")
    else:
        response.say("Thank you. Goodbye.")
    response.hangup()
    return Response(content=str(response), media_type="application/xml")
```

---

## ⚠️ Important Legal Notes

Automated and prerecorded calls are regulated. For real use:
- ✓ Only call people who have clearly **consented**
- ✓ Only call for **permitted informational/service calls**
- ⚠️ Always comply with local calling regulations
- See [Twilio compliance docs](https://www.twilio.com/guidelines/compliance)

---

## 🐛 Troubleshooting

**"ModuleNotFoundError: No module named 'twilio'"**
```bash
source .venv/bin/activate
pip install twilio
```

**"App not found"**
Make sure you're in the right directory and running:
```bash
uvicorn main:app --reload
```

**"Connection refused" when calling**
1. Make sure ngrok is running: `ngrok http 8000`
2. Update `PUBLIC_BASE_URL` in your code/environment
3. Check Twilio Console for errors

**"Invalid Twilio credentials"**
1. Go to https://www.twilio.com/console
2. Copy your exact Account SID and Auth Token
3. Paste into `.env` or environment variables
4. Restart the server

---

## 📚 Resources

- [Twilio Python Docs](https://www.twilio.com/docs/python/install)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [TwiML Voice Documentation](https://www.twilio.com/docs/voice/twiml)
- [ngrok Docs](https://ngrok.com/docs)
