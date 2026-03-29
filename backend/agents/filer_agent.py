"""
VA Form 20-0996 (HLR) download and PDF fill — isolated from the auditor agent.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
from pypdf import PdfReader, PdfWriter

from agents.mapping_agent import VAMappingAgent

_BACKEND_DIR = Path(__file__).resolve().parent.parent

VA_FORMS_API_URL = "https://api.va.gov/forms_api/v1/forms/20-0996"
LIGHTHOUSE_FORMS_URL = "https://api.va.gov/services/va_forms/v0/forms/20-0996"
FALLBACK_FORM_PDF_URL = "http://www.vba.va.gov/pubs/forms/VBA-20-0996-ARE.pdf"

BLANK_PDF_NAME = "blank_20_0996.pdf"
FILLED_PDF_NAME = "james_miller_ready_to_file_appeal.pdf"

# Keys sent to Gemini; ``veteran_data`` must supply a value for each (or .get defaults).
HLR_TARGET_FIELDS: list[str] = [
    "first_name",
    "last_name",
    "issue",
    "ssn_1",
    "ssn_2",
    "ssn_3",
    "dob_month",
    "dob_day",
    "dob_year",
    "phone_area",
    "phone_mid",
    "phone_last",
    "address_street",
    "address_city",
    "address_state",
    "address_zip",
    "date_month",
    "date_day",
    "date_year",
]

_HTTP_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "VAClaimAuditor/1.0 (hackathon; +https://www.va.gov)",
}


class VAFormFiler:
    """Download VA Form 20-0996 and fill fields with pypdf."""

    def __init__(self, backend_dir: str | Path | os.PathLike[str] | None = None) -> None:
        self.backend_dir = os.path.normpath(
            str(backend_dir) if backend_dir is not None else str(_BACKEND_DIR)
        )

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

    def debug_print_all_pdf_field_names(self, pdf_path: str | Path | os.PathLike[str]) -> None:
        """Print every internal field name (and /FT) so XFA-style names can be mapped."""
        path = os.path.normpath(str(pdf_path))
        reader = PdfReader(path)
        fields = reader.get_fields() or {}
        print(f"--- PDF form fields ({len(fields)} total): {path} ---")
        for name in sorted(fields.keys()):
            meta = fields[name]
            ft = meta.get("/FT") if isinstance(meta, dict) else None
            print(f"  {name!r}  /FT={ft!r}")

    def download_and_fill_hlr(self, veteran_data: dict[str, Any]) -> None:
        """Download blank 20-0996, map fields via Gemini, fill, save under ``output/``."""
        pdf_url = self._get_form_pdf_url_from_api()
        pdf_resp = requests.get(pdf_url, timeout=120)
        pdf_resp.raise_for_status()

        blank_path = os.path.join(self.backend_dir, BLANK_PDF_NAME)
        out_dir = os.path.join(self.backend_dir, "output")
        os.makedirs(out_dir, exist_ok=True)
        filled_path = os.path.join(out_dir, FILLED_PDF_NAME)

        with open(blank_path, "wb") as f:
            f.write(pdf_resp.content)
        self.debug_print_all_pdf_field_names(blank_path)

        mapper = VAMappingAgent(backend_dir=self.backend_dir)
        field_map = mapper.get_field_mapping(blank_path, HLR_TARGET_FIELDS)

        reader = PdfReader(blank_path)
        fields = reader.get_fields() or {}
        present = set(fields.keys())

        updates: dict[str, str] = {}
        for data_key in HLR_TARGET_FIELDS:
            pdf_name = field_map.get(data_key)
            if not pdf_name or pdf_name not in present:
                continue
            val = veteran_data.get(data_key, "")
            updates[pdf_name] = str(val)

        writer = PdfWriter()
        writer.append(reader)
        # Government PDFs / XFA: viewers need NeedAppearances so filled text renders visibly.
        writer.set_need_appearances_writer(True)

        if updates:
            for page in writer.pages:
                writer.update_page_form_field_values(page, updates)

        with open(filled_path, "wb") as f:
            writer.write(f)
