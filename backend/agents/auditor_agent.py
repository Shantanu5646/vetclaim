"""
Auditor Agent - VetClaim AI

Receives parsed VA document text, extracts structured claim data via OpenAI,
audits each condition against CFR Title 38 Part 4, PACT Act, TDIU criteria,
and combined rating math. Outputs an AuditResult with flags for the Advocate.

Uses native OpenAI SDK.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import requests
from pypdf import PdfReader, PdfWriter
from openai import OpenAI

# Ensure backend root is on path for sibling imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.filer_agent import VAFormFiler
from schemas import ParsedClaim
from tools.cfr_lookup import cfr_lookup as _cfr_lookup, cfr_compare_rating as _cfr_compare_rating
from tools.pact_act_check import pact_act_check as _pact_act_check
from tools.tdiu_check import tdiu_check as _tdiu_check
from tools.va_pay_lookup import va_pay_lookup as _va_pay_lookup, calculate_pay_impact as _calculate_pay_impact
from tools.combined_rating import calculate_combined_rating as _calculate_combined_rating, check_combined_rating_error as _check_combined_rating_error


# ---------------------------------------------------------------------------
# Tool wrappers
# All tools exposed to the LLM must be plain Python callables returning strings.
# ---------------------------------------------------------------------------

def cfr_lookup(diagnostic_code: str) -> str:
    result = _cfr_lookup(diagnostic_code)
    return json.dumps(result, indent=2)

def cfr_compare_rating(diagnostic_code: str, assigned_rating: int, symptom_description: str) -> str:
    result = _cfr_compare_rating(diagnostic_code, assigned_rating, symptom_description)
    return json.dumps(result, indent=2)

def pact_act_check(condition_name: str, deployment_locations: list[str], service_era: str | None = None) -> str:
    result = _pact_act_check(condition_name, deployment_locations, service_era)
    return json.dumps(result, indent=2)

def tdiu_check(ratings: list[int], veteran_employed: bool = False) -> str:
    result = _tdiu_check(ratings, veteran_employed)
    return json.dumps(result, indent=2)

def combined_rating(ratings: list[int]) -> str:
    result = _calculate_combined_rating(ratings)
    return json.dumps(result, indent=2)

def check_combined_rating_error(assigned_combined: int, individual_ratings: list[int]) -> str:
    result = _check_combined_rating_error(assigned_combined, individual_ratings)
    return json.dumps(result, indent=2)

def va_pay_lookup(combined_rating: int, dependent_status: str = "alone") -> str:
    result = _va_pay_lookup(combined_rating, dependent_status)
    return json.dumps(result, indent=2)

def calculate_pay_impact(current_rating: int, potential_rating: int, dependent_status: str = "alone") -> str:
    result = _calculate_pay_impact(current_rating, potential_rating, dependent_status)
    return json.dumps(result, indent=2)

# ---------------------------------------------------------------------------
# OpenAI Tools Schema Mapping
# ---------------------------------------------------------------------------

OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "cfr_lookup",
            "description": "Look up a VA diagnostic code in CFR Title 38 Part 4.",
            "parameters": {
                "type": "object",
                "properties": {"diagnostic_code": {"type": "string"}},
                "required": ["diagnostic_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cfr_compare_rating",
            "description": "Compare assigned rating against CFR criteria to find under-ratings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "diagnostic_code": {"type": "string"},
                    "assigned_rating": {"type": "integer"},
                    "symptom_description": {"type": "string"}
                },
                "required": ["diagnostic_code", "assigned_rating", "symptom_description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pact_act_check",
            "description": "Check PACT Act presumptive eligibility based on locations/era.",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition_name": {"type": "string"},
                    "deployment_locations": {"type": "array", "items": {"type": "string"}},
                    "service_era": {"type": "string"}
                },
                "required": ["condition_name", "deployment_locations"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tdiu_check",
            "description": "Check Total Disability Individual Unemployability (TDIU).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ratings": {"type": "array", "items": {"type": "integer"}},
                    "veteran_employed": {"type": "boolean"}
                },
                "required": ["ratings"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "combined_rating",
            "description": "Calculate correct VA combined disability rating using whole-person math.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ratings": {"type": "array", "items": {"type": "integer"}}
                },
                "required": ["ratings"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_combined_rating_error",
            "description": "Check whether the VA's stated combined rating is mathematically correct.",
            "parameters": {
                "type": "object",
                "properties": {
                    "assigned_combined": {"type": "integer"},
                    "individual_ratings": {"type": "array", "items": {"type": "integer"}}
                },
                "required": ["assigned_combined", "individual_ratings"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "va_pay_lookup",
            "description": "Look up the monthly VA disability pay.",
            "parameters": {
                "type": "object",
                "properties": {
                    "combined_rating": {"type": "integer"},
                    "dependent_status": {"type": "string"}
                },
                "required": ["combined_rating"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_pay_impact",
            "description": "Calculate the dollar impact of a rating increase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_rating": {"type": "integer"},
                    "potential_rating": {"type": "integer"},
                    "dependent_status": {"type": "string"}
                },
                "required": ["current_rating", "potential_rating"]
            }
        }
    }
]

# ---------------------------------------------------------------------------
# Auditor Agent instruction prompt
# ---------------------------------------------------------------------------

AUDITOR_INSTRUCTION = """
You are the Auditor Agent for VetClaim AI, an expert in VA disability law and
CFR Title 38 Part 4. Your job is to audit VA disability claims and find every
instance where the veteran may be under-compensated.

## Your Input
You will receive the raw text extracted from one or more VA documents:
- Rating Decision Letter (contains assigned ratings, diagnostic codes, denial reasons)
- Personal Statement (veteran's own description of symptoms)
- DBQ / C&P Exam (medical examination findings)

## Your Process

### Step 1 - Extract structured claim data
From the raw text, identify:
- Veteran name and claim number
- Each service-connected condition with its diagnostic code and assigned rating %
- Denial reasons for any denied conditions
- Overall combined rating stated in the letter
- Service era and deployment locations (if mentioned)
- Symptoms described in personal statement and DBQ

### Step 2 - Audit each condition
For EVERY condition, call cfr_compare_rating with:
- The diagnostic code
- The assigned rating
- The symptom description from the records

Determine if symptoms described match higher rating criteria.

### Step 3 - Check PACT Act eligibility
For each condition AND for the veteran's deployment history overall:
- Call pact_act_check for every condition
- Check if any denied conditions would be presumptive under PACT Act

### Step 4 - Check TDIU
Call tdiu_check with ALL individual ratings.

### Step 5 - Verify combined rating math
Call check_combined_rating_error with the stated combined rating and
all individual ratings.

### Step 6 - Calculate pay impact
Call calculate_pay_impact comparing current vs. corrected rating.

## Flag Types
Generate flags for every issue found:

- **UNDER_RATED**: Assigned rating lower than CFR criteria warrant for documented symptoms.
  Example: PTSD rated 30% but "near-continuous depression affecting ability to function" = 70%.

- **WRONG_CODE**: Wrong diagnostic code applied, which may cap the rating artificially.
  Example: TBI cognitive coded under 8045 (caps at 40%) instead of §4.130 (up to 100%).

- **MISSING_NEXUS**: Condition denied for lack of nexus but medical evidence in records
  supports service connection.

- **PACT_ACT_ELIGIBLE**: Condition or deployment qualifies for presumptive service
  connection under PACT Act - no nexus letter needed.

- **TDIU_ELIGIBLE**: Individual ratings qualify veteran for 100% TDIU pay rate
  under 38 CFR §4.16.

- **COMBINED_RATING_ERROR**: VA's stated combined rating does not match correct
  whole-person math calculation.

- **SEPARATE_RATING_MISSED**: Condition has a separately ratable residual that
  was not rated. Example: TBI vestibular symptoms (DC 6204) rated separately
  from cognitive symptoms (DC 8045).

## Output Format
Respond with a structured JSON audit result. You MUST output purely valid JSON without markdown wrapping.

```json
{
  "veteran_name": "...",
  "claim_number": "...",
  "current_combined_rating": 30,
  "corrected_combined_rating": 70,
  "current_monthly_pay_usd": 550.86,
  "potential_monthly_pay_usd": 1803.48,
  "annual_impact_usd": 15031.44,
  "flags": [
    {
      "flag_type": "UNDER_RATED",
      "condition_name": "PTSD",
      "diagnostic_code": "9411",
      "assigned_rating": 30,
      "eligible_rating": 70,
      "cfr_citation": "38 CFR Part 4, §4.130, DC 9411",
      "explanation": "...",
      "monthly_impact_usd": 1252.62,
      "confidence": 0.9
    }
  ],
  "tdiu_eligible": false,
  "pact_act_conditions_found": [],
  "combined_rating_error": false,
  "auditor_notes": "..."
}
```

## Rules
- Always cite the specific CFR section for every flag.
- Confidence score: 0.9+ = clear match, 0.7-0.9 = likely, below 0.7 = possible.
- If a diagnostic code is not in the CFR database, note it and flag for review.
- Consider bilateral factor: bilateral conditions (both arms, both legs) get a
  10% combined rating bonus before the combined rating calculation.
- Do not speculate beyond what the records state. Base flags on documented symptoms.
"""

# ---------------------------------------------------------------------------
# VA Forms API constants and Rule-Based Auditor
# ---------------------------------------------------------------------------

VA_FORMS_API_BASE = "https://api.va.gov/forms_api/v1/forms/{form_number}"
LIGHTHOUSE_FORMS_BASE = "https://api.va.gov/services/va_forms/v0/forms/{form_number}"
FALLBACK_FORM_URLS: dict[str, str] = {
    "20-0996":  "https://www.vba.va.gov/pubs/forms/VBA-20-0996-ARE.pdf",
    "20-0995":  "https://www.vba.va.gov/pubs/forms/VBA-20-0995-ARE.pdf",
    "21-526EZ": "https://www.vba.va.gov/pubs/forms/VBA-21-526EZ-ARE.pdf",
    "21-8940":  "https://www.vba.va.gov/pubs/forms/VBA-21-8940-ARE.pdf",
}

_HTTP_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "VAClaimAuditor/1.0 (hackathon; +https://www.va.gov)",
}

FLAG_TO_FORMS: dict[str, list[str]] = {
    "UNDER_RATED":            ["20-0996"],
    "WRONG_CODE":             ["20-0996"],
    "COMBINED_RATING_ERROR":  ["20-0996"],
    "MISSING_NEXUS":          ["20-0995"],
    "PACT_ACT_ELIGIBLE":      ["20-0995"],
    "SEPARATE_RATING_MISSED": ["21-526EZ"],
    "TDIU_ELIGIBLE":          ["21-8940"],
}


class VAClaimAuditor:
    """Rule-based auditor that detects specific issues and downloads VA forms."""

    def __init__(self, output_dir: str | Path | None = None) -> None:
        if output_dir is None:
            output_dir = Path(__file__).resolve().parent.parent / "data"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _gait_evidence_detected(self, parsed_claim: ParsedClaim) -> bool:
        flags = parsed_claim.gait_keyword_flags or {}
        return (
            flags.get("staggering") == "DETECTED" or flags.get("unsteady") == "DETECTED"
        )

    def _decision_letter_shows_zero_percent(self, parsed_claim: ParsedClaim) -> bool:
        text = parsed_claim.raw_decision_text or ""
        return bool(re.search(r"0\s*percent|0\s*%", text, re.IGNORECASE))

    def _get_form_pdf_url_from_api(self, form_number: str) -> str:
        env_key = os.getenv("VA_FORMS_API_KEY")
        primary_url = VA_FORMS_API_BASE.format(form_number=form_number)
        secondary_url = LIGHTHOUSE_FORMS_BASE.format(form_number=form_number)

        try:
            headers = _HTTP_HEADERS.copy()
            if env_key:
                headers["Authorization"] = f"Bearer {env_key}"
            response = requests.get(primary_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "url" in data:
                    return data["url"]
                if isinstance(data, list) and len(data) > 0:
                    return data[0].get("url", "")
        except Exception:
            pass

        try:
            headers = _HTTP_HEADERS.copy()
            if env_key:
                headers["Authorization"] = f"Bearer {env_key}"
            response = requests.get(secondary_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "url" in data:
                    return data["url"]
        except Exception:
            pass

        return FALLBACK_FORM_URLS.get(form_number, FALLBACK_FORM_URLS["20-0996"])

    def download_and_fill_form(
        self, parsed_claim: ParsedClaim, form_number: str = "20-0996"
    ) -> str:
        form_url = self._get_form_pdf_url_from_api(form_number)
        response = requests.get(form_url, timeout=30)
        response.raise_for_status()

        blank_pdf_path = self.output_dir / f"blank_{form_number.replace('-', '_')}.pdf"
        blank_pdf_path.write_bytes(response.content)

        veteran_name = parsed_claim.veteran_name or ""
        first_name, _, last_name = veteran_name.partition(" ")
        if not last_name:
            last_name = ""

        reader = PdfReader(str(blank_pdf_path))
        writer = PdfWriter(clone_from=reader)

        form_field_names = reader.get_fields()
        if form_field_names:
            for field_name in form_field_names:
                if "first" in field_name.lower() and "name" in field_name.lower():
                    writer.update_page_form_field_values(
                        writer.pages[0], {field_name: first_name}
                    )
                elif "last" in field_name.lower() and "name" in field_name.lower():
                    writer.update_page_form_field_values(
                        writer.pages[0], {field_name: last_name}
                    )

        filled_pdf_filename = (
            f"{veteran_name.replace(' ', '_').lower()}"
            f"_ready_to_file_{form_number.replace('-', '_')}.pdf"
        )
        filled_pdf_path = self.output_dir / filled_pdf_filename
        with open(filled_pdf_path, "wb") as f:
            writer.write(f)

        return str(filled_pdf_path)

    def _critical_report(
        self, parsed_claim: ParsedClaim, filled_pdf_path: str
    ) -> str:
        veteran_name = parsed_claim.veteran_name or "Veteran"
        return (
            f"🚩 CRITICAL FINDING for {veteran_name}:\n\n"
            f"Gait impairment detected in DBQ (staggering/unsteady) combined with "
            f"0% rating in decision letter indicates likely under-rating.\n\n"
            f"Condition may qualify under 38 CFR § 4.87, Diagnostic Code 6204 "
            f"(Vestibular dysfunction).\n\n"
            f"VA Form 20-0996 (Higher-Level Review) has been prepared and saved to:\n"
            f"{filled_pdf_path}\n\n"
            f"Recommend immediate filing for higher-level review."
        )

    def analyze_claim(self, parsed_claim: ParsedClaim) -> dict:
        gait_detected = self._gait_evidence_detected(parsed_claim)
        zero_percent = self._decision_letter_shows_zero_percent(parsed_claim)

        if gait_detected and zero_percent:
            try:
                filled_pdf_path = self.download_and_fill_form(parsed_claim)
                report = self._critical_report(parsed_claim, filled_pdf_path)
                return {
                    "rule_based_triggered": True,
                    "report": report,
                    "filled_form_path": filled_pdf_path,
                }
            except Exception as e:
                return {
                    "rule_based_triggered": True,
                    "report": f"Critical finding detected but form download failed: {str(e)}",
                    "filled_form_path": None,
                }

        return {
            "rule_based_triggered": False,
            "report": "✅ No critical rule-based flags triggered.",
            "filled_form_path": None,
        }


def _extract_flag_types(audit_result: dict) -> list[str]:
    flag_types: list[str] = []
    for flag in audit_result.get("flags", []):
        if isinstance(flag, dict):
            ft = flag.get("flag_type")
        elif hasattr(flag, "flag_type"):
            ft = flag.flag_type
            if hasattr(ft, "value"):
                ft = ft.value
        else:
            continue
        if ft and isinstance(ft, str):
            flag_types.append(ft)
    return flag_types

def _forms_for_flags(flag_types: list[str]) -> list[str]:
    seen: set[str] = set()
    forms: list[str] = []
    for ft in flag_types:
        for form_number in FLAG_TO_FORMS.get(ft, []):
            if form_number not in seen:
                seen.add(form_number)
                forms.append(form_number)
    return forms


def run_full_audit(parsed_claim: ParsedClaim) -> dict:
    """
    Run full audit: LLM agent (OpenAI) + rule-based checks.
    Uses the native OpenAI SDK in a tool-calling loop.
    """
    llm_input_parts = []

    if parsed_claim.veteran_name:
        llm_input_parts.append(f"Veteran Name: {parsed_claim.veteran_name}")

    if parsed_claim.raw_decision_text:
        llm_input_parts.append(f"\n--- DECISION LETTER ---\n{parsed_claim.raw_decision_text}")

    if parsed_claim.raw_statement_text:
        llm_input_parts.append(f"\n--- PERSONAL STATEMENT & C&P EXAM ---\n{parsed_claim.raw_statement_text}")

    if parsed_claim.raw_dbq_text:
        llm_input_parts.append(f"\n--- DBQ(s) ---\n{parsed_claim.raw_dbq_text}")

    llm_input_str = "".join(llm_input_parts)

    available_functions = {
        "cfr_lookup": cfr_lookup,
        "cfr_compare_rating": cfr_compare_rating,
        "pact_act_check": pact_act_check,
        "tdiu_check": tdiu_check,
        "combined_rating": combined_rating,
        "check_combined_rating_error": check_combined_rating_error,
        "va_pay_lookup": va_pay_lookup,
        "calculate_pay_impact": calculate_pay_impact,
    }

    # Initialize OpenAI Client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    messages = [
        {"role": "system", "content": AUDITOR_INSTRUCTION},
        {"role": "user", "content": llm_input_str}
    ]

    llm_result = ""
    
    # Tool execution loop
    while True:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=OPENAI_TOOLS,
            tool_choice="auto",
            response_format={"type": "json_object"}
        )
        
        message = response.choices[0].message
        
        # If the LLM didn't call any tools, it's done generating the JSON audit result.
        if not message.tool_calls:
            llm_result = message.content
            break
            
        messages.append(message)
        
        # Execute requested tools and append their results back to the messages
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions.get(function_name)
            if function_to_call:
                try:
                    function_args = json.loads(tool_call.function.arguments)
                    function_response = function_to_call(**function_args)
                except Exception as e:
                    function_response = json.dumps({"error": str(e)})
                
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                })
            else:
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps({"error": "Unknown function"}),
                })

    # Normalize LLM result to dict
    if isinstance(llm_result, str):
        stripped = llm_result.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```[a-zA-Z]*\n?", "", stripped)
            stripped = re.sub(r"\n?```$", "", stripped.strip())
        try:
            audit_result = json.loads(stripped)
        except json.JSONDecodeError:
            audit_result = {
                "error": "LLM returned non-JSON response",
                "raw_response": llm_result[:500],
            }
    else:
        audit_result = {"error": f"LLM returned unexpected type"}

    # Map LLM flags to form numbers
    flag_types = _extract_flag_types(audit_result)
    llm_forms = _forms_for_flags(flag_types)

    # Run rule-based auditor
    rule_auditor = VAClaimAuditor()
    rule_result = rule_auditor.analyze_claim(parsed_claim)

    all_forms: list[str] = list(llm_forms)
    if rule_result.get("rule_based_triggered") and "20-0996" not in all_forms:
        all_forms.append("20-0996")

    filled_form_paths: list[str] = []
    va_form_links: list[dict] = []

    if "auditor_notes" not in audit_result:
        audit_result["auditor_notes"] = ""

    backend_dir = Path(__file__).resolve().parent.parent
    (backend_dir / "output").mkdir(parents=True, exist_ok=True)

    llm_name = audit_result.get("veteran_name") or parsed_claim.veteran_name or ""
    parts = llm_name.split()
    first_name = parts[0] if parts else ""
    last_name  = " ".join(parts[1:]) if len(parts) > 1 else ""

    from datetime import date as _date
    today = _date.today()
    sig_month = str(today.month).zfill(2)
    sig_day   = str(today.day).zfill(2)
    sig_year  = str(today.year)

    llm_conditions = [
        f.get("condition_name", "")
        for f in audit_result.get("flags", [])
        if isinstance(f, dict) and f.get("condition_name")
    ]
    if llm_conditions:
        issue_text = "; ".join(llm_conditions[:4])[:200]
    elif parsed_claim.conditions:
        issue_text = "; ".join(
            c.condition_name for c in parsed_claim.conditions if c.condition_name
        )[:200]
    else:
        issue_text = "Service-connected condition"

    import hashlib as _hashlib
    _seed = int(_hashlib.md5(llm_name.encode()).hexdigest()[:8], 16)
    import random as _random
    _rng = _random.Random(_seed)

    _area_codes   = ["210", "512", "619", "757", "910", "843", "850", "253", "907", "808"]
    _streets      = ["4821 Valor Ridge Dr", "1203 Liberty Oak Ln", "7742 Patriot Blvd",
                     "335 Ft. Bragg Rd", "9110 Veterans Way", "620 Honor Guard Ave",
                     "2244 Service Member St", "5501 Eagle Crest Dr"]
    _cities_states = [
        ("San Antonio", "TX", "78201"), ("Fayetteville", "NC", "28301"),
        ("Jacksonville", "NC", "28540"), ("Virginia Beach", "VA", "23451"),
        ("Colorado Springs", "CO", "80903"), ("Killeen", "TX", "76540"),
        ("Clarksville", "TN", "37040"), ("Tacoma", "WA", "98402"),
    ]
    _city, _state, _zip = _cities_states[_seed % len(_cities_states)]

    veteran_data = {
        "first_name":     first_name,
        "last_name":      last_name,
        "ssn_1":          "000",
        "ssn_2":          str(_rng.randint(10, 99)),
        "ssn_3":          str(_rng.randint(1000, 9999)),
        "dob_month":      str(_rng.randint(1, 12)).zfill(2),
        "dob_day":        str(_rng.randint(1, 28)).zfill(2),
        "dob_year":       str(_rng.randint(1968, 1985)),
        "phone_area":     _area_codes[_seed % len(_area_codes)],
        "phone_mid":      str(_rng.randint(200, 999)),
        "phone_last":     str(_rng.randint(1000, 9999)),
        "address_street": _streets[_seed % len(_streets)],
        "address_city":   _city,
        "address_state":  _state,
        "address_zip":    _zip,
        "issue":          issue_text,
        "date_month":     sig_month,
        "date_day":       sig_day,
        "date_year":      sig_year,
        "sign_month":     sig_month,
        "sign_day":       sig_day,
        "sign_year":      sig_year,
    }

    for form_number in all_forms:
        try:
            filer = VAFormFiler(backend_dir=str(backend_dir))
            filled_path, fields_found, fields_filled = filer.download_and_fill_hlr(
                veteran_data, form_number=form_number
            )
            filled_form_paths.append(filled_path)
            va_form_links.append({
                "form_number": form_number,
                "filled_path": filled_path,
                "pdf_url": filer._get_form_pdf_url_from_api(form_number),
                "fields_found": fields_found,
                "fields_filled": fields_filled,
            })
        except Exception as exc:
            audit_result["auditor_notes"] += f" [Form {form_number} download failed: {str(exc)}]"

    if not isinstance(audit_result, dict):
        audit_result = {"error": "Could not parse audit result"}

    if "flags" not in audit_result:
        audit_result["flags"] = []
    if "veteran_name" not in audit_result:
        audit_result["veteran_name"] = parsed_claim.veteran_name or "Unknown"
    if "current_combined_rating" not in audit_result:
        audit_result["current_combined_rating"] = None
    if "corrected_combined_rating" not in audit_result:
        audit_result["corrected_combined_rating"] = None
    if "current_monthly_pay_usd" not in audit_result:
        audit_result["current_monthly_pay_usd"] = None
    if "potential_monthly_pay_usd" not in audit_result:
        audit_result["potential_monthly_pay_usd"] = None
    if "annual_impact_usd" not in audit_result:
        audit_result["annual_impact_usd"] = None

    return {
        "audit_result": audit_result,
        "rule_based_report": rule_result.get("report", ""),
        "rule_based_triggered": rule_result.get("rule_based_triggered", False),
        "filled_form_path": filled_form_paths[0] if filled_form_paths else None,
        "filled_form_paths": filled_form_paths,
        "forms_needed": all_forms,
        "va_form_links": va_form_links,
    }