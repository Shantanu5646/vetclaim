"""
Extract text from VA claim PDFs (personal statement, decision letter, DBQ)
and emit structured JSON. Requires pdfplumber and pandas.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber


STATEMENT_NAME = "james_miller_personal_statement.pdf"
DECISION_NAME = "james_miller_decision_letter.pdf"
DBQ_NAME = "james_miller_ear_dbq.pdf"


class VAClaimParser:
    """Parse VA disability claim PDFs into structured data."""

    def __init__(self, pdf_dir: str | Path | None = None) -> None:
        self.pdf_dir = Path(pdf_dir) if pdf_dir is not None else Path.cwd()
        self.statement_path = self.pdf_dir / STATEMENT_NAME
        self.decision_path = self.pdf_dir / DECISION_NAME
        self.dbq_path = self.pdf_dir / DBQ_NAME

    def _extract_plain_text(self, pdf_path: Path) -> dict[str, Any]:
        if not pdf_path.is_file():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        parts: list[str] = []
        page_chars: list[int] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                parts.append(t)
                page_chars.append(len(t))
        full = "\n\n".join(parts)
        return {
            "filename": pdf_path.name,
            "path": str(pdf_path.resolve()),
            "page_count": len(parts),
            "text": full,
            "chars_per_page": page_chars,
        }

    def extract_personal_statement(self) -> dict[str, Any]:
        return self._extract_plain_text(self.statement_path)

    def extract_decision_letter(self) -> dict[str, Any]:
        return self._extract_plain_text(self.decision_path)

    def detect_staggering_unsteady_in_layout(self, layout_text: str) -> dict[str, str]:
        """
        Check layout-preserving text for 'Staggering' or 'Unsteady' (word-level, case-insensitive).
        Returns status strings DETECTED / NOT_DETECTED per keyword.
        """
        stagger_re = re.compile(r"\bStaggering\b", re.IGNORECASE)
        unsteady_re = re.compile(r"\bUnsteady\b", re.IGNORECASE)
        return {
            "staggering": "DETECTED" if stagger_re.search(layout_text) else "NOT_DETECTED",
            "unsteady": "DETECTED" if unsteady_re.search(layout_text) else "NOT_DETECTED",
        }

    def extract_dbq(self) -> dict[str, Any]:
        if not self.dbq_path.is_file():
            raise FileNotFoundError(f"PDF not found: {self.dbq_path}")
        layout_parts: list[str] = []
        page_layout_chars: list[int] = []
        with pdfplumber.open(self.dbq_path) as pdf:
            for page in pdf.pages:
                block = page.extract_text(layout=True) or ""
                layout_parts.append(block)
                page_layout_chars.append(len(block))
        layout_full = "\n\n".join(layout_parts)
        flags = self.detect_staggering_unsteady_in_layout(layout_full)
        return {
            "filename": self.dbq_path.name,
            "path": str(self.dbq_path.resolve()),
            "page_count": len(layout_parts),
            "layout_text": layout_full,
            "layout_chars_per_page": page_layout_chars,
            "gait_keyword_flags": flags,
        }

    def _pages_summary_dataframe(self, payload: dict[str, Any]) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []
        for doc_key, per_page_key in (
            ("personal_statement", "chars_per_page"),
            ("decision_letter", "chars_per_page"),
            ("dbq", "layout_chars_per_page"),
        ):
            doc = payload.get(doc_key)
            if not doc or not isinstance(doc, dict):
                continue
            counts = doc.get(per_page_key) or []
            for i, n in enumerate(counts, start=1):
                rows.append({"document": doc_key, "page": i, "char_count": n})
        return pd.DataFrame(rows)

    def extract_all(self) -> dict[str, Any]:
        personal = self.extract_personal_statement()
        decision = self.extract_decision_letter()
        dbq = self.extract_dbq()

        out: dict[str, Any] = {
            "personal_statement": {
                "filename": personal["filename"],
                "path": personal["path"],
                "page_count": personal["page_count"],
                "text": personal["text"],
            },
            "decision_letter": {
                "filename": decision["filename"],
                "path": decision["path"],
                "page_count": decision["page_count"],
                "text": decision["text"],
            },
            "dbq": {
                "filename": dbq["filename"],
                "path": dbq["path"],
                "page_count": dbq["page_count"],
                "layout_text": dbq["layout_text"],
                "gait_keyword_flags": dbq["gait_keyword_flags"],
            },
        }

        df = self._pages_summary_dataframe(
            {
                "personal_statement": personal,
                "decision_letter": decision,
                "dbq": dbq,
            }
        )
        out["pages_summary"] = df.to_dict(orient="records")
        return out

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.extract_all(), indent=indent, ensure_ascii=False)


def main() -> None:
    base = Path(__file__).resolve().parent
    parser = VAClaimParser(pdf_dir=base)
    print(parser.to_json())


if __name__ == "__main__":
    main()
