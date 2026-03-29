"""
mock_va_portal/server.py — Mock VA Portal Backend

A minimal Flask server that acts as the VA's document intake system.
The VetClaim AI app POSTs the generated NOD appeal PDF here, and the
mock VA portal frontend polls this server to show the submission status.

Endpoints:
  POST /submit-appeal   — VetClaim app sends the PDF here
  GET  /submissions     — Frontend polls this to check for new submissions
  GET  /submissions/<id>/pdf  — Serves the stored PDF for inline display

Run with:
  python3 server.py

The server runs on http://localhost:5050 by default.
"""

import os
import json
import random
import string
from datetime import datetime

from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS  # allows the VetClaim app (different port) to POST here

app = Flask(__name__, static_folder=".", static_url_path="")

# Allow cross-origin requests from any localhost port so the VetClaim app
# (which runs on a different port) can POST to this server during the demo.
CORS(app)

# Directory where uploaded PDFs are stored during the demo session.
# This folder is created automatically if it doesn't exist.
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "submissions")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory store for submission metadata.
# We use a simple list instead of a database — this is a demo, not production.
# Data is lost when the server restarts, which is fine for a hackathon.
submissions = []


def generate_confirmation_number() -> str:
    """
    Generate a realistic-looking VA confirmation number.
    Format: VA-YYYY-NOD-XXXXXX (e.g. VA-2026-NOD-048821)
    The random suffix makes each demo submission look unique.
    """
    year = datetime.now().year
    suffix = "".join(random.choices(string.digits, k=6))
    return f"VA-{year}-NOD-{suffix}"


@app.route("/submit-appeal", methods=["POST"])
def submit_appeal():
    """
    Receive a NOD appeal PDF from the VetClaim AI application.

    Expected: multipart/form-data with:
      - file: the PDF file (required)
      - veteran_name: string (optional, defaults to "James R. Wilson")
      - conditions: comma-separated list of condition names (optional)

    Returns JSON with the confirmation number and submission ID.
    The VetClaim app should display this confirmation number to the veteran.
    """
    # Validate that a file was actually sent
    if "file" not in request.files:
        return jsonify({"error": "No file provided. Send the PDF as 'file' in form-data."}), 400

    pdf_file = request.files["file"]

    if pdf_file.filename == "":
        return jsonify({"error": "Empty filename. Attach a valid PDF."}), 400

    # Generate a unique confirmation number for this submission
    confirmation_number = generate_confirmation_number()

    # Save the PDF to disk using the confirmation number as the filename
    # so we can serve it back to the confirmation page later
    safe_filename = f"{confirmation_number}.pdf"
    save_path = os.path.join(UPLOAD_DIR, safe_filename)
    pdf_file.save(save_path)

    # Build the submission metadata record
    submission = {
        "id": confirmation_number,
        "confirmation_number": confirmation_number,
        "veteran_name": request.form.get("veteran_name", "James R. Wilson"),
        "conditions": request.form.get("conditions", "PTSD (DC 9411), Respiratory Condition (DC 6604), TBI (DC 8045)"),
        "submitted_at": datetime.now().strftime("%B %d, %Y at %I:%M %p EST"),
        "pdf_filename": safe_filename,
        "documents": [
            {"name": "Notice of Disagreement (NOD)", "form": "Form 10182", "pages": 4},
            {"name": "Supporting Evidence Summary", "form": "CFR Title 38 analysis", "pages": 6},
            {"name": "CFR Title 38 Legal Citations Brief", "form": "38 CFR § 4.130, § 3.309(e)", "pages": 3},
        ]
    }

    # Store in memory so the frontend can poll for it
    submissions.append(submission)

    print(f"[VA Portal] Received appeal submission: {confirmation_number}")

    return jsonify({
        "success": True,
        "confirmation_number": confirmation_number,
        "message": f"Appeal documents received. Confirmation: {confirmation_number}"
    }), 201


@app.route("/submissions", methods=["GET"])
def get_submissions():
    """
    Return all stored submissions as JSON.
    The mock VA portal frontend polls this endpoint to check if a new
    submission has arrived from the VetClaim app.
    Returns the most recent submission first.
    """
    return jsonify(list(reversed(submissions)))


@app.route("/submissions/<submission_id>/pdf", methods=["GET"])
def get_submission_pdf(submission_id):
    """
    Serve the stored PDF for a given submission ID.
    Used by confirmation.html to embed the PDF inline via an <iframe>.
    """
    # Find the submission record
    submission = next((s for s in submissions if s["id"] == submission_id), None)

    if not submission:
        abort(404)

    pdf_path = os.path.join(UPLOAD_DIR, submission["pdf_filename"])

    if not os.path.exists(pdf_path):
        abort(404)

    # Send the PDF with inline disposition so the browser displays it
    # rather than triggering a download
    return send_file(pdf_path, mimetype="application/pdf", as_attachment=False)


@app.route("/")
def index():
    """Serve the mock VA portal homepage."""
    return send_file("index.html")


@app.route("/testcase/<veteran>/<filename>")
def serve_testcase_pdf(veteran: str, filename: str):
    """
    Serve a PDF from the testcase/ folder so the dashboard can link to
    real claim documents for the demo veterans.

    WHY: The testcase PDFs live outside mock_va_portal/ so Flask's static
    file serving doesn't reach them. This route bridges that gap without
    moving the files or changing the project structure.

    Example: GET /testcase/james_millner/james_miller_decision_letter.pdf
    """
    # Build the path relative to this file: ../testcase/<veteran>/<filename>
    testcase_dir = os.path.join(os.path.dirname(__file__), "..", "testcase")
    pdf_path = os.path.realpath(os.path.join(testcase_dir, veteran, filename))

    # Security: ensure the resolved path stays inside the testcase directory.
    # This prevents path traversal attacks (e.g. ../../etc/passwd).
    safe_root = os.path.realpath(testcase_dir)
    if not pdf_path.startswith(safe_root):
        abort(403)

    if not os.path.exists(pdf_path):
        abort(404)

    return send_file(pdf_path, mimetype="application/pdf", as_attachment=False)


if __name__ == "__main__":
    print("=" * 50)
    print("Mock VA Portal server running at http://localhost:5050")
    print("VetClaim app should POST PDFs to: http://localhost:5050/submit-appeal")
    print("=" * 50)
    # debug=True gives helpful error messages during the hackathon
    app.run(host="0.0.0.0", port=5050, debug=True)
