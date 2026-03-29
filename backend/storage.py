"""
storage.py
----------
Simple JSON-file-based storage for call records.
Each call is stored as calls/<call_sid>.json.
Replace with a real database for production.
"""

import os
import json
from pathlib import Path

CALLS_DIR = Path(__file__).parent.parent / "calls"
CALLS_DIR.mkdir(exist_ok=True)


def _path(call_sid: str) -> Path:
    return CALLS_DIR / f"{call_sid}.json"


def save_call(call_sid: str, data: dict) -> None:
    """Create or merge data into the call record."""
    p = _path(call_sid)
    existing = {}
    if p.exists():
        try:
            existing = json.loads(p.read_text())
        except Exception:
            pass
    existing.update({k: v for k, v in data.items() if v is not None})
    p.write_text(json.dumps(existing, indent=2))


def get_call(call_sid: str) -> dict | None:
    p = _path(call_sid)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def list_calls() -> list[dict]:
    records = []
    for f in sorted(CALLS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            records.append(json.loads(f.read_text()))
        except Exception:
            pass
    return records
