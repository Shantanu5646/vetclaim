"""
Form Filler Agent - VetClaim AI

Fetches a blank VA form PDF from the VA Lighthouse Forms API, reads all
AcroForm fields from it, then uses Gemini to intelligently map the veteran's
parsed claim data to each field and writes the filled PDF.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import requests
from pypdf import PdfReader, PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import google.generativeai as genai
from schemas import ParsedClaim


# ---------------------------------------------------------------------------
# VA Lighthouse Forms API
# ---------------------------------------------------------------------------

# Public endpoint — no API key required for read-only form metadata
LIGHTHOUSE_FORMS_API = "https://api.va.gov/services/va_forms/v0/forms/{form_name}"

FALLBACK_FORM_URLS: dict[str, str] = {
    "20-0996":  "https://www.vba.va.gov/pubs/forms/VBA-20-0996-ARE.pdf",
    "20-0995":  "https://www.vba.va.gov/pubs/forms/VBA-20-0995-ARE.pdf",
    "21-526EZ": "https://www.vba.va.gov/pubs/forms/VBA-21-526EZ-ARE.pdf",
    "21-8940":  "https://www.vba.va.gov/pubs/forms/VBA-21-8940-ARE.pdf",
}

_HTTP_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "VAClaimAuditor/1.0 (hackathon)",
}

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


# ---------------------------------------------------------------------------
# Step 1 — Fetch form PDF URL from VA Lighthouse API
# ---------------------------------------------------------------------------

def fetch_form_url_from_va_api(form_number: str) -> str:
    """
    Call the VA Lighthouse Forms API to get the latest PDF URL for a form.
    Falls back to hardcoded URLs if the API is unavailable.

    Returns the PDF download URL as a string.
    """
    api_key = os.getenv("VA_FORMS_API_KEY", "")
    headers = _HTTP_HEADERS.copy()
    if api_key:
        headers["apikey"] = api_key

    url = LIGHTHOUSE_FORMS_API.format(form_name=form_number)
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # Lighthouse returns: {"data": {"attributes": {"url": "..."}}}
        pdf_url = (
            data.get("data", {}).get("attributes", {}).get("url")
            or data.get("url")
        )
        if pdf_url:
            return pdf_url
    except Exception:
        pass

    return FALLBACK_FORM_URLS.get(form_number, FALLBACK_FORM_URLS["20-0996"])


# ---------------------------------------------------------------------------
# Step 2 — Download the blank PDF and extract all AcroForm field names
# ---------------------------------------------------------------------------

def download_blank_form(form_number: str, output_dir: Path) -> tuple[Path, dict[str, str]]:
    """
    Download the blank VA form PDF and return (local_path, field_dict).
    field_dict maps each field name to its current value (empty string for blank fields).
    """
    pdf_url = fetch_form_url_from_va_api(form_number)
    resp = requests.get(pdf_url, timeout=30)
    resp.raise_for_status()

    output_dir.mkdir(parents=True, exist_ok=True)
    blank_path = output_dir / f"blank_{form_number.replace('-', '_')}.pdf"
    blank_path.write_bytes(resp.content)

    reader = PdfReader(str(blank_path))
    fields = reader.get_fields() or {}
    # Normalise: just keep field name → current value
    field_dict = {
        name: (field.value if hasattr(field, "value") else "")
        for name, field in fields.items()
    }
    return blank_path, field_dict


# ---------------------------------------------------------------------------
# Step 3 — Use Gemini to map claim data → form fields
# ---------------------------------------------------------------------------

FILLER_SYSTEM_PROMPT = """You are a VA form-filling assistant.
You will be given:
1. A list of AcroForm field names from a VA PDF form.
2. A veteran's structured claim data (name, claim number, conditions, ratings, etc.).

Your job: return a JSON object mapping ONLY the field names you can confidently fill
to the values they should contain, based on the claim data provided.

Rules:
- Use exact field names as given — do not invent or rename them.
- Leave fields out of the JSON if you are not sure what value to use.
- Dates should be in MM/DD/YYYY format.
- Checkboxes: use "Yes" or "No".
- Rating percentages: use digits only (e.g. "30", not "30%").
- Return raw JSON only — no markdown fences, no explanation.
"""


def llm_map_fields(
    form_number: str,
    field_names: list[str],
    parsed_claim: ParsedClaim,
) -> dict[str, str]:
    """
    Ask Gemini to map claim data to form field names.
    Returns a dict of {field_name: value_to_fill}.
    """
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {}

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=FILLER_SYSTEM_PROMPT,
    )

    claim_summary = json.dumps(parsed_claim.model_dump(), indent=2, default=str)
    user_prompt = (
        f"VA Form: {form_number}\n\n"
        f"Form field names:\n{json.dumps(field_names, indent=2)}\n\n"
        f"Veteran claim data:\n{claim_summary}"
    )

    try:
        response = model.generate_content(user_prompt)
        raw = response.text.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```[a-zA-Z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw.strip())
        return json.loads(raw)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Step 4 — Write filled PDF
# ---------------------------------------------------------------------------

def fill_pdf(blank_path: Path, field_values: dict[str, str], output_path: Path) -> Path:
    """
    Clone the blank PDF and fill in the provided field values.
    Returns the path to the filled PDF.
    """
    reader = PdfReader(str(blank_path))
    writer = PdfWriter(clone_from=reader)

    if field_values:
        # update_page_form_field_values works per-page; apply to all pages
        for page in writer.pages:
            writer.update_page_form_field_values(page, field_values)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def fill_va_form(
    form_number: str,
    parsed_claim: ParsedClaim,
    output_dir: Path | str | None = None,
) -> dict:
    """
    Full pipeline: fetch form from VA API → extract fields → LLM maps claim
    data → write filled PDF.

    Returns:
        {
            "form_number": str,
            "pdf_url": str,          # URL the blank was fetched from
            "fields_found": int,     # total AcroForm fields in the blank
            "fields_filled": int,    # fields the LLM filled
            "filled_path": str,      # local path to the filled PDF
            "field_mapping": dict,   # field_name → value
        }
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR
    output_dir = Path(output_dir)

    # 1. Download blank form and get field names
    pdf_url = fetch_form_url_from_va_api(form_number)
    blank_path, existing_fields = download_blank_form(form_number, output_dir)
    field_names = list(existing_fields.keys())

    # 2. LLM maps claim data to fields
    field_mapping = llm_map_fields(form_number, field_names, parsed_claim)

    # 3. Fill PDF
    veteran_slug = (parsed_claim.veteran_name or "veteran").replace(" ", "_").lower()
    filled_filename = f"{veteran_slug}_{form_number.replace('-', '_')}_filled.pdf"
    filled_path = output_dir / filled_filename
    fill_pdf(blank_path, field_mapping, filled_path)

    return {
        "form_number": form_number,
        "pdf_url": pdf_url,
        "fields_found": len(field_names),
        "fields_filled": len(field_mapping),
        "filled_path": str(filled_path),
        "field_mapping": field_mapping,
    }
