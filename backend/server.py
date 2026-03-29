"""
VetClaim Backend Server — Flask API on port 5001.

Routes:
  POST /api/upload          — accept PDFs, start pipeline, return job_id
  GET  /api/stream/<job_id> — SSE stream of pipeline progress
  GET  /api/result/<job_id> — return completed audit JSON
  GET  /api/download        — serve a filled PDF by ?path= query param
  GET  /api/status          — health check
"""

from __future__ import annotations

import json
import os
import queue
import sys
import tempfile
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
import requests
from flask import jsonify
from dotenv import load_dotenv
# ---------------------------------------------------------------------------
# sys.path — ensure project root is importable so agent modules resolve
# ---------------------------------------------------------------------------

load_dotenv()

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
# Also insert backend dir so `from schemas import ...` works inside agents
_BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_BACKEND_DIR))

from flask import Flask, Response, jsonify, request, send_file, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

_OUTPUT_DIR = _BACKEND_DIR / "output"
_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# ---------------------------------------------------------------------------
# Job store
# ---------------------------------------------------------------------------

@dataclass
class JobRecord:
    job_id: str
    status: Literal["running", "complete", "error"]
    upload_dir: Path
    result: dict | None = None
    error: str | None = None
    events: queue.Queue = field(default_factory=queue.Queue)


jobs: dict[str, JobRecord] = {}

# ---------------------------------------------------------------------------
# Pipeline thread
# ---------------------------------------------------------------------------

def _run_pipeline(job: JobRecord) -> None:
    """Background thread: parse → audit → fill forms, emitting SSE events."""

    def emit(step: str, status: str) -> None:
        payload = json.dumps({"step": step, "status": status})
        job.events.put(payload)

    try:
        # Step 1 — Parse documents
        emit("parsing_documents", "Parsing uploaded documents...")
        from agents.parser_agent import VAClaimParser
        parser = VAClaimParser(pdf_dir=str(job.upload_dir))
        parsed_claim = parser.extract_all()

        # Step 2 — Run audit (LLM + rule-based)
        emit("running_audit", "Running AI audit on your claim...")
        from agents.auditor_agent import run_full_audit
        result = run_full_audit(parsed_claim)

        # Step 3 — Form filling happens inside run_full_audit; emit milestone
        emit("filling_forms", "Filling VA forms...")

        # Step 4 — Complete
        job.result = result
        job.status = "complete"
        emit("complete", "Audit complete. Redirecting to results...")

    except Exception as exc:  # noqa: BLE001
        job.status = "error"
        job.error = str(exc)
        payload = json.dumps({"step": "error", "status": f"Pipeline error: {exc}"})
        job.events.put(payload)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/upload", methods=["POST"])
def upload():
    """Accept PDF files, start pipeline, return job_id with 202."""
    files = request.files.getlist("files")

    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "No files provided"}), 400

    # Validate sizes before saving anything
    for f in files:
        f.stream.seek(0, 2)  # seek to end
        size = f.stream.tell()
        f.stream.seek(0)     # reset
        if size > _MAX_FILE_SIZE:
            return jsonify({"error": "File too large"}), 413

    # Create per-job temp directory
    job_id = str(uuid.uuid4())
    upload_dir = Path(tempfile.mkdtemp(prefix=f"vetclaim_{job_id}_"))

    # Save only PDF files
    saved = 0
    for f in files:
        if f.filename and f.filename.lower().endswith(".pdf"):
            filename = secure_filename(f.filename)
            f.save(str(upload_dir / filename))
            saved += 1

    if saved == 0:
        return jsonify({"error": "No valid PDF files provided"}), 400

    # Create job record and start pipeline thread
    job = JobRecord(job_id=job_id, status="running", upload_dir=upload_dir)
    jobs[job_id] = job

    thread = threading.Thread(target=_run_pipeline, args=(job,), daemon=True)
    thread.start()

    return jsonify({"job_id": job_id}), 202


@app.route("/api/stream/<job_id>", methods=["GET"])
def stream(job_id: str):
    """SSE stream of pipeline progress for a given job."""
    job = jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404

    def generate():
        while True:
            try:
                payload = job.events.get(timeout=30)
                yield f"data: {payload}\n\n"
                data = json.loads(payload)
                if data.get("step") in ("complete", "error"):
                    break
            except queue.Empty:
                # Send a keep-alive comment so the connection stays open
                yield ": keep-alive\n\n"
                # If job is done but queue is empty, close
                if job.status in ("complete", "error"):
                    break

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.route("/api/result/<job_id>", methods=["GET"])
def result(job_id: str):
    """Return audit result JSON, or 202 if still running, or 404 if unknown."""
    job = jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404

    if job.status == "running":
        return jsonify({"status": "processing"}), 202

    if job.status == "error":
        return jsonify({"error": job.error or "Pipeline failed"}), 500

    return jsonify(job.result), 200


@app.route("/api/download", methods=["GET"])
def download():
    """Serve a filled PDF by ?path= query param; reject path traversal."""
    file_path = request.args.get("path", "")
    if not file_path:
        abort(400)

    abs_path = os.path.realpath(file_path)
    output_dir = os.path.realpath(str(_OUTPUT_DIR))

    if not abs_path.startswith(output_dir + os.sep) and abs_path != output_dir:
        abort(403)

    if not os.path.isfile(abs_path):
        abort(404)

    return send_file(abs_path, as_attachment=True, download_name=os.path.basename(abs_path))


@app.route("/api/status", methods=["GET"])
def status():
    """Health check endpoint."""
    return jsonify({"status": "OK", "service": "VetClaim Backend"}), 200


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
@app.route('/api/call-va', methods=['POST'])
def call_va_rep():
    url = "https://api.vapi.ai/call/phone"
    headers = {
        "Authorization": f"Bearer {os.getenv('VAPI_PRIVATE_KEY')}",
        "Content-Type": "application/json"
    }
    payload = {
        "assistantId": "efe9791d-f257-40d3-8760-715fdeb669f0",
        "phoneNumberId": "4882efe5-5767-44ef-bb42-4aaf3752dda4",
        "customer": {"number": "+18133409551"}, # Your actual cell number here
        "assistantOverrides": {
            "variableValues": {"veteran_name": "Arina Kiera"}
        }
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        return jsonify({"status": "success", "data": response.json()}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/get-transcript', methods=['GET'])
def get_transcript():
    # This fetches your most recent call from Vapi
    url = "https://api.vapi.ai/call?limit=1"
    headers = {"Authorization": f"Bearer {os.getenv('VAPI_PRIVATE_KEY')}"}
    
    try:
        response = requests.get(url, headers=headers)
        calls = response.json()
        if calls:
            # Returns the text transcript if available
            return jsonify({"transcript": calls[0].get("transcript", "Transcript is still processing...")}), 200
        return jsonify({"transcript": "No calls found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)