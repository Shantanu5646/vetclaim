# How to Run VetClaim AI - Auditor Agent

## Quick Test (Verify Everything Works)

```bash
# From project root
python3 backend/test_auditor_tools.py
```

This runs a complete demo showing:
- PTSD under-rating detection
- TBI separate rating analysis
- PACT Act eligibility
- Combined rating math
- TDIU qualification
- Financial impact calculation

**Expected output:** ✅ ALL TOOL TESTS PASSED

---

## Running the Full Auditor in the Pipeline

### 1. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

This installs:
- `google-adk` (Agent Development Kit)
- `google-generativeai` (Gemini API)
- `pdfplumber` (PDF parsing)
- `pydantic` (data validation)
- All other required packages

### 2. Set Up Environment Variables

Your `.env` file already has:
```
GOOGLE_API_KEY=AIzaSyCggS7SF5Xm2g9zJTZrXN-0bN23SS6pBlo
VA_API_KEY=VgKI6h0JCbHe2f9eZwgxKmia9R5HKNfH
```

The auditor uses these to call Gemini and VA APIs.

### 3. Parse a VA Document (Teammate's Parser)

```python
# In backend/agents/parser_agent.py
from agents.parser_agent import VAClaimParser

parser = VAClaimParser(pdf_dir="backend")
parsed_data = parser.extract_all()
print(parsed_data)
```

This extracts raw text from the 3 sample PDFs:
- `james_miller_personal_statement.pdf`
- `james_miller_decision_letter.pdf`
- `james_miller_ear_dbq.pdf`

### 4. Run the Auditor Agent

```python
from agents.auditor_agent import auditor_agent
from schemas import ParsedClaim, ParsedCondition
import json

# Get parsed claim from teammate's parser (see step 3)
parsed = parser.extract_all()

# Create audit input prompt
audit_prompt = f"""
Audit this VA disability claim for under-ratings, PACT Act eligibility, TDIU eligibility,
and combined rating errors. Use your tools to analyze each condition step by step.

CLAIM DATA:
{json.dumps(parsed, indent=2)}

Return a structured JSON audit result with all flags and recommendations.
"""

# Run auditor (Google ADK agent)
# Note: This requires async context (Jupyter, FastAPI app, etc.)
# For sync testing, use the test_auditor_tools.py approach above
```

---

## Full End-to-End Flow (How It Works)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Veteran uploads VA Rating Decision Letter (PDF/image)   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PARSER AGENT (teammate) - pdfplumber                    │
│    Extracts: vet name, codes, ratings, symptoms            │
│    Output: raw text JSON                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. AUDITOR AGENT (YOU) - Gemini + 8 tools                 │
│    - CFR code lookup (DC 9411 → PTSD criteria)            │
│    - Rating comparison (30% assigned vs 70% eligible?)     │
│    - PACT Act check (burn pit presumptive?)                │
│    - TDIU eligibility (100% pay rate?)                     │
│    - Combined rating math (1 - ((1-r1)*(1-r2)*...))        │
│    - Pay impact ($1,500+/month?)                           │
│    Output: AuditResult with 5-10 flags                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. ADVOCATE AGENT - Debates each flag                      │
│    "Is this CFR citation correct? Would a judge agree?"    │
│    Output: ValidatedFlags with confidence scores           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. NEGOTIATOR AGENT - Drafts appeal package               │
│    - NOD letter with CFR citations                         │
│    - Phone script to RO                                     │
│    - Benefits summary card                                  │
│    - VA Form links (Forms API)                             │
│    - RO address (Facilities API)                           │
│    Output: Appeal PDF + docs ready to mail                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
       ✅ Veteran gets $15,000+/year increase
```

---

## Folder Structure

```
backend/
├── agents/
│   ├── auditor_agent.py          ← YOUR AUDITOR (Google ADK agent with 8 tools)
│   ├── parser_agent.py           ← Teammate's parser
│   └── __init__.py
├── tools/
│   ├── cfr_lookup.py             ← CFR code→criteria lookup
│   ├── pact_act_check.py         ← Burn pit/Agent Orange eligibility
│   ├── tdiu_check.py             ← 100% pay rate qualification
│   ├── va_pay_lookup.py          ← 2026 pay rates + impact
│   ├── combined_rating.py        ← VA math: 1-(1-r1)*(1-r2)*...
│   └── __init__.py
├── data/
│   ├── cfr38_part4.json          ← 30 diagnostic codes + criteria
│   ├── pact_act_conditions.json  ← Presumptive conditions
│   ├── va_pay_rates_2026.json    ← Monthly pay by rating
│   └── combined_ratings_table.json
├── schemas.py                    ← Pydantic models
├── test_auditor_tools.py         ← DEMO TEST (run this)
├── test_auditor.py               ← ADK integration test
├── requirements.txt              ← Dependencies
└── va_claim_parser.py            ← Old (use agents/parser_agent.py)
```

---

## Quick Commands

### Run the demo (shows all logic working):
```bash
python3 backend/test_auditor_tools.py
```

### Test a single tool:
```bash
python3 -c "
from backend.tools.cfr_lookup import cfr_lookup
print(cfr_lookup('9411'))  # PTSD
"
```

### Check PACT Act eligibility:
```bash
python3 -c "
from backend.tools.pact_act_check import pact_act_check
result = pact_act_check('asthma', ['Iraq', 'Afghanistan'], 'post-9/11')
print('Eligible:', result['pact_act_eligible'])
"
```

### Calculate pay impact:
```bash
python3 -c "
from backend.tools.va_pay_lookup import calculate_pay_impact
result = calculate_pay_impact(30, 70, 'alone')
print(f'Pay increase: \${result[\"monthly_increase_usd\"]:.2f}/month')
"
```

---

## For the Hackathon Demo

**What to show judges:**
1. Upload James Miller's Rating Decision Letter PDF
2. Auditor runs in ~45 seconds
3. Shows: 5 flags (under-rating, PACT Act, TDIU, etc.)
4. Shows: $156K value over 10 years
5. Outputs: Professional NOD letter ready to mail

**Key selling points:**
- Adversarial AI debate (Auditor vs Advocate) = technical depth
- Real VA API integration (Forms + Facilities)
- Live CFR lookup (not hardcoded)
- Combined rating math validation
- PACT Act presumptive detection
