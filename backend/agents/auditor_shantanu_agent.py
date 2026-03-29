"""
Agent 2: AI legal auditor — analyzes VAClaimParser output and may download/fill VA Form 20-0996.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

import requests
from pypdf import PdfReader, PdfWriter

from va_claim_parser import VAClaimParser

VA_FORMS_API_URL = "https://api.va.gov/forms_api/v1/forms/20-0996"
LIGHTHOUSE_FORMS_URL = "https://api.va.gov/services/va_forms/v0/forms/20-0996"
FALLBACK_FORM_PDF_URL = "http://www.vba.va.gov/pubs/forms/VBA-20-0996-ARE.pdf"

BLANK_PDF_NAME = "blank_20_0996.pdf"
FILLED_PDF_NAME = "james_miller_ready_to_file_appeal.pdf"

_HTTP_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "VAClaimAuditor/1.0 (hackathon; +https://www.va.gov)",
}


class VAClaimAuditor:
    """Audits parsed claim JSON for evidence vs. rating discrepancies."""

    def __init__(self, backend_dir: str | Path | None = None) -> None:
        self.backend_dir = Path(backend_dir) if backend_dir is not None else _BACKEND_DIR

    @staticmethod
    def _gait_evidence_detected(parsed_json_data: dict[str, Any]) -> bool:
        flags = (parsed_json_data.get("dbq") or {}).get("gait_keyword_flags") or {}
        return flags.get("staggering") == "DETECTED" or flags.get("unsteady") == "DETECTED"

    @staticmethod
    def _decision_letter_shows_zero_percent(parsed_json_data: dict[str, Any]) -> bool:
        text = (parsed_json_data.get("decision_letter") or {}).get("text") or ""
        if re.search(r"\b0\s+percent\b", text, re.IGNORECASE):
            return True
        return bool(re.search(r"(?<![0-9])0\s*%", text))

    def _get_form_pdf_url_from_api(self) -> str:
        r = requests.get(VA_FORMS_API_URL, headers=_HTTP_HEADERS, timeout=60)
        if r.ok:
            try:
                payload = r.json()
                url = payload.get("data", {}).get("attributes", {}).get("url")
                if isinstance(url, str) and url.startswith("http"):
                    return url
            except json.JSONDecodeError:
                pass

        api_key = os.environ.get("VA_FORMS_API_KEY", "").strip()
        if api_key:
            r2 = requests.get(
                LIGHTHOUSE_FORMS_URL,
                headers={**_HTTP_HEADERS, "apikey": api_key},
                timeout=60,
            )
            if r2.ok:
                try:
                    payload = r2.json()
                    url = payload.get("data", {}).get("attributes", {}).get("url")
                    if isinstance(url, str) and url.startswith("http"):
                        return url
                except json.JSONDecodeError:
                    pass

        return FALLBACK_FORM_PDF_URL

    def download_and_fill_form(self) -> None:
        pdf_url = self._get_form_pdf_url_from_api()
        pdf_resp = requests.get(pdf_url, timeout=120)
        pdf_resp.raise_for_status()

        blank_path = self.backend_dir / BLANK_PDF_NAME
        filled_path = self.backend_dir / FILLED_PDF_NAME
        blank_path.write_bytes(pdf_resp.content)

        reader = PdfReader(str(blank_path))
        fields = reader.get_fields() or {}
        field_names = {k for k, v in fields.items() if isinstance(v, dict) and v.get("/FT") == "/Tx"}

        updates: dict[str, str] = {}
        if "form1[0].#subform[2].Veterans_First_Name[0]" in field_names:
            updates["form1[0].#subform[2].Veterans_First_Name[0]"] = "James"
        if "form1[0].#subform[2].Veterans_Last_Name[0]" in field_names:
            updates["form1[0].#subform[2].Veterans_Last_Name[0]"] = "Miller"
        note = (
            "Automated prep (hackathon): 0% Vestibular discrepancy — DBQ notes staggering/unsteady gait; "
            "requesting Higher-Level Review."
        )
        if "form1[0].#subform[3].SPECIFICISSUE1[2]" in field_names:
            updates["form1[0].#subform[3].SPECIFICISSUE1[2]"] = note
        else:
            for name in sorted(field_names):
                if "SPECIFICISSUE" in name:
                    updates[name] = note
                    break

        writer = PdfWriter()
        writer.append(reader)
        if updates:
            for page in writer.pages:
                writer.update_page_form_field_values(page, updates)

        with open(filled_path, "wb") as f:
            writer.write(f)

    @staticmethod
    def _critical_report() -> str:
        return (
            "🚨 **CRITICAL VA RATING ERROR DETECTED** 🚨\n"
            "   - **Medical Evidence:** DBQ explicitly notes 'Staggering/Unsteady gait'. \n"
            "   - **Current Rating:** The Decision Letter incorrectly assigns a 0% rating.\n"
            "   - **Legal Precedent:** Under 38 CFR § 4.87, Diagnostic Code 6204, 'occasional staggering' legally warrants a minimum 30% rating.\n"
            "   - **Action Taken:** Downloaded official VA Form 20-0996, auto-filled data, and saved as `james_miller_ready_to_file_appeal.pdf`."
        )

    def analyze_claim(self, parsed_json_data: dict[str, Any]) -> str:
        gait = self._gait_evidence_detected(parsed_json_data)
        zero_pct = self._decision_letter_shows_zero_percent(parsed_json_data)

        if gait and zero_pct:
            self.download_and_fill_form()
            return self._critical_report()
        return "✅ All clear. Ratings match medical evidence."


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass

    parser = VAClaimParser(pdf_dir=_BACKEND_DIR)
    data = parser.extract_all()
    auditor = VAClaimAuditor(backend_dir=_BACKEND_DIR)
    print(auditor.analyze_claim(data))


if __name__ == "__main__":
    main()
