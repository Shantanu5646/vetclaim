import os
import base64
import json
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import anthropic
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="VetClaim AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

VA_SYSTEM_PROMPT = """You are a VA benefits intake assistant helping veterans submit their disability claim documents for review and preparation.

Your job is to collect the following three documents from the veteran, one at a time:

1. C&P EXAM (Compensation & Pension Examination)
   - This is the medical exam report from their VA or contracted examiner
   - It may be titled "Disability Benefits Questionnaire" or "DBQ"
   - Ask them to upload the PDF or paste the key findings

2. DBQ (Disability Benefits Questionnaire)
   - This is the condition-specific form completed by their doctor
   - Examples: PTSD DBQ, Ear Conditions DBQ, Back/Spine DBQ
   - Ask for all DBQs if they have multiple conditions

3. RATING DECISION / DENIAL LETTER
   - This is the official VA decision letter
   - It shows what was granted, denied, and at what percentage
   - It includes the "Reasons for Decision" section

INSTRUCTIONS FOR HOW TO ASK:

Step 1 — Greet the veteran warmly. Ask for their name and the condition(s) they are claiming.

Step 2 — Ask them to upload or describe their C&P exam results. If they don't have it, explain how to request it through MyHealtheVet or a FOIA request.

Step 3 — Ask them to upload or describe their DBQ. If they don't have one, explain that their treating doctor can complete a DBQ and submit it privately.

Step 4 — Ask them to upload or describe their VA Rating Decision or Denial Letter. If they haven't received one yet, note that one is pending and move forward with what they have.

Step 5 — Once all documents are collected, summarize what you received, identify any gaps or missing nexus information, and ask how you can help them next (appeal, new claim, increase request, etc.)

TONE:
- Warm, patient, and professional
- Use plain language — avoid jargon unless the veteran uses it first
- Never make medical or legal conclusions
- Always encourage the veteran to work with an accredited VSO, attorney, or claims agent"""


class Message(BaseModel):
    role: str
    content: str | list


class ChatRequest(BaseModel):
    messages: list[Message]
    stream: Optional[bool] = True


def stream_chat(messages: list[dict]):
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=VA_SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield f"data: {json.dumps({'text': text})}\n\n"
    yield "data: [DONE]\n\n"


@app.post("/chat")
async def chat(request: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    return StreamingResponse(
        stream_chat(messages),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    b64 = base64.standard_b64encode(contents).decode("utf-8")

    document_block = {
        "type": "document",
        "source": {
            "type": "base64",
            "media_type": "application/pdf",
            "data": b64,
        },
        "title": file.filename,
    }

    return {"document_block": document_block, "filename": file.filename}


@app.get("/health")
async def health():
    return {"status": "ok"}
