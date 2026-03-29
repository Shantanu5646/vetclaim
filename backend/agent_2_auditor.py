"""
Agent 2: AI legal auditor — analyzes VAClaimParser output and may download/fill VA Form 20-0996.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

_BACKEND_DIR = Path(__file__).resolve().parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from agents.filer_agent import VAFormFiler
from agents.va_claim_parser import (
    DBQ_NAME,
    DECISION_NAME,
    STATEMENT_NAME,
    VAClaimParser,
)


def _claim_pdf_dir(backend: Path) -> Path:
    """
    Use the first directory that contains all three claim PDFs:
    ``user_uploads``, then backend root, then ``agents`` (dev layout).
    """
    names = (STATEMENT_NAME, DECISION_NAME, DBQ_NAME)
    candidates = [
        os.path.join(str(backend), "user_uploads"),
        str(backend),
        os.path.join(str(backend), "agents"),
    ]
    for d in candidates:
        if all(os.path.isfile(os.path.join(d, n)) for n in names):
            return Path(d)
    return backend


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

    @staticmethod
    def _critical_report() -> str:
        return (
            "🚨 **CRITICAL VA RATING ERROR DETECTED** 🚨\n"
            "   - **Medical Evidence:** DBQ explicitly notes 'Staggering/Unsteady gait'. \n"
            "   - **Current Rating:** The Decision Letter incorrectly assigns a 0% rating.\n"
            "   - **Legal Precedent:** Under 38 CFR § 4.87, Diagnostic Code 6204, 'occasional staggering' legally warrants a minimum 30% rating.\n"
            "   - **Action Taken:** Downloaded official VA Form 20-0996, auto-filled data, and saved as `output/james_miller_ready_to_file_appeal.pdf`."
        )

    def analyze_claim(self, parsed_json_data: dict[str, Any]) -> str:
        gait = self._gait_evidence_detected(parsed_json_data)
        zero_pct = self._decision_letter_shows_zero_percent(parsed_json_data)

        if gait and zero_pct:
            filer = VAFormFiler(backend_dir=os.path.normpath(str(self.backend_dir)))
            vet_data = {
                "first_name": "James",
                "last_name": "Miller",
                "issue": "0% Vestibular discrepancy found",
                "ssn_1": "123",
                "ssn_2": "45",
                "ssn_3": "6789",
                "dob_month": "01",
                "dob_day": "15",
                "dob_year": "1980",
                "phone_area": "555",
                "phone_mid": "123",
                "phone_last": "4567",
                "address_street": "123 Hackathon Way",
                "address_city": "Tampa",
                "address_state": "FL",
                "address_zip": "33602",
                "date_month": "01",
                "date_day": "15",
                "date_year": "2026",
            }
            filer.download_and_fill_hlr(vet_data)
            return self._critical_report()
        return "✅ All clear. Ratings match medical evidence."


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass

    backend = os.path.normpath(str(_BACKEND_DIR))
    os.makedirs(os.path.join(backend, "user_uploads"), exist_ok=True)
    os.makedirs(os.path.join(backend, "output"), exist_ok=True)

    pdf_dir = _claim_pdf_dir(_BACKEND_DIR)
    parser = VAClaimParser(pdf_dir=pdf_dir)
    data = parser.extract_all()
    auditor = VAClaimAuditor(backend_dir=_BACKEND_DIR)
    print(auditor.analyze_claim(data))


if __name__ == "__main__":
    main()
