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

_BACKEND_DIR = Path(__file__).resolve().parent.parent

VA_FORMS_API_URL = "https://api.va.gov/forms_api/v1/forms/20-0996"
LIGHTHOUSE_FORMS_URL = "https://api.va.gov/services/va_forms/v0/forms/20-0996"
FALLBACK_FORM_PDF_URL = "http://www.vba.va.gov/pubs/forms/VBA-20-0996-ARE.pdf"

BLANK_PDF_NAME = "blank_20_0996.pdf"
FILLED_PDF_NAME = "james_miller_ready_to_file_appeal.pdf"

_HTTP_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "VAClaimAuditor/1.0 (hackathon; +https://www.va.gov)",
}


class VAFormFiler:
    """Download VA Form 20-0996 and fill fields with pypdf."""

    def __init__(self, backend_dir: str | Path | None = None) -> None:
        self.backend_dir = Path(backend_dir) if backend_dir is not None else _BACKEND_DIR

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

    def debug_print_all_pdf_field_names(self, pdf_path: str | Path) -> None:
        """Print every internal field name (and /FT) so XFA-style names can be mapped."""
        path = Path(pdf_path)
        reader = PdfReader(str(path))
        fields = reader.get_fields() or {}
        print(f"--- PDF form fields ({len(fields)} total): {path} ---")
        for name in sorted(fields.keys()):
            meta = fields[name]
            ft = meta.get("/FT") if isinstance(meta, dict) else None
            print(f"  {name!r}  /FT={ft!r}")

    def download_and_fill_hlr(self, veteran_data: dict[str, Any]) -> None:
        """Download blank 20-0996, fill HLR form fields from ``veteran_data``, save under backend/."""
        pdf_url = self._get_form_pdf_url_from_api()
        pdf_resp = requests.get(pdf_url, timeout=120)
        pdf_resp.raise_for_status()

        blank_path = self.backend_dir / BLANK_PDF_NAME
        filled_path = self.backend_dir / FILLED_PDF_NAME
        blank_path.write_bytes(pdf_resp.content)
        self.debug_print_all_pdf_field_names(blank_path)

        reader = PdfReader(str(blank_path))
        fields = reader.get_fields() or {}
        present = set(fields.keys())

        mapped: dict[str, str] = {
            "form1[0].#subform[2].Veterans_First_Name[0]": str(
                veteran_data.get("first_name", "")
            ),
            "form1[0].#subform[2].Veterans_Last_Name[0]": str(veteran_data.get("last_name", "")),
            "form1[0].#subform[2].Veterans_SocialSecurityNumber_FirstThreeNumbers[0]": "123",
            "form1[0].#subform[2].Veterans_SocialSecurityNumber_SecondTwoNumbers[0]": "45",
            "form1[0].#subform[2].Veterans_SocialSecurityNumber_LastFourNumbers[0]": "6789",
            "form1[0].#subform[2].DOBmonth[0]": "01",
            "form1[0].#subform[2].DOBday[0]": "15",
            "form1[0].#subform[2].DOByear[0]": "1980",
            "form1[0].#subform[2].Telephone_Number_Area_Code[0]": "555",
            "form1[0].#subform[2].Telephone_Middle_Three_Numbers[0]": "123",
            "form1[0].#subform[2].Telephone_Last_Four_Numbers[0]": "4567",
            "form1[0].#subform[2].CurrentMailingAddress_NumberAndStreet[0]": "123 Hackathon Way",
            "form1[0].#subform[2].CurrentMailingAddress_City[0]": "Tampa",
            "form1[0].#subform[2].CurrentMailingAddress_StateOrProvince[0]": "FL",
            "form1[0].#subform[2].CurrentMailingAddress_ZIPOrPostalCode_FirstFiveNumbers[0]": "33602",
            "form1[0].#subform[3].SPECIFICISSUE1[1]": str(veteran_data["issue"]),
            "form1[0].#subform[3].Date_Month[2]": "01",
            "form1[0].#subform[3].Date_Day[2]": "15",
            "form1[0].#subform[3].Date_Year[2]": "2026",
        }
        updates = {k: v for k, v in mapped.items() if k in present}

        writer = PdfWriter()
        writer.append(reader)
        # Government PDFs / XFA: viewers need NeedAppearances so filled text renders visibly.
        writer.set_need_appearances_writer(True)

        if updates:
            for page in writer.pages:
                writer.update_page_form_field_values(page, updates)

        with open(filled_path, "wb") as f:
            writer.write(f)
