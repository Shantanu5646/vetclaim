# VetClaim AI — Mock VA Portal

Mock VA eBenefits portal for the VetClaim AI demo (HackUSF 2026). Simulates the "before and after" of an automated appeal submission.

> "77% of VA claims are denied on first submission. VetClaim AI audits your claim in 60 seconds and generates your appeal letter."

---

## What This Is

Two-page demo portal + Flask backend:

- `index.html` — veteran dashboard showing denied claims (the "before")
- `confirmation.html` — appeal received confirmation page (the "after")
- `server.py` — Flask backend that receives PDFs from the VetClaim AI app

---

## Quick Start

```bash
cd ~/vetclaim/vetclaim
pip install flask flask-cors
/opt/anaconda3/bin/python3 mock_va_portal/server.py
# → http://localhost:5050
```

> If you get `No module named 'flask'`, use `/opt/anaconda3/bin/python3` instead of `python3`.

Then open `http://localhost:5050` in a browser.

---

## Demo Flow

1. Open `http://localhost:5050` — veteran sees their rating with denied conditions
2. Switch to the VetClaim AI app — it audits the claim and POSTs the NOD appeal PDF
3. Switch back to the portal — green notification banner appears within 3 seconds
4. Click "View Submission →" — confirmation page shows the PDF, report number, and VA Forms API badge

### Simulate without the VetClaim app

```bash
echo "%PDF-1.4 test" > /tmp/appeal.pdf

curl -X POST http://localhost:5050/submit-appeal \
  -F "file=@/tmp/appeal.pdf" \
  -F "veteran_name=James T. Milner" \
  -F "conditions=PTSD (DC 9411), Ear Condition (DC 6260)"
```

Switch back to the browser — the green banner appears within 3 seconds.

---

## Veteran Profiles

Click the signed-in name in the top-right nav to toggle between three real test case veterans:

| Profile | Branch | Rating | Denied Conditions |
|---|---|---|---|
| James T. Milner | U.S. Marine Corps | 100% (ALS) | PTSD, Ear Condition |
| Robert Garza | U.S. Army | 60% | PTSD, TBI |
| James R. Wilson | U.S. Army | 30% | Sleep Apnea, Burn Pit Exposure |

Test case documents are in `testcase/james_millner/` and `testcase/robert-graza/`.

---

## Getting to the Confirmation Page

After submitting via curl or the VetClaim app, navigate to:

```
http://localhost:5050/confirmation.html
```

No query param needed — it auto-loads the most recent submission. Or use a specific ID:

```
http://localhost:5050/confirmation.html?id=VA-2026-NOD-XXXXXX
```

---

## Sending a PDF from the VetClaim App

```python
import requests

with open("appeal.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:5050/submit-appeal",
        files={"file": ("appeal.pdf", f, "application/pdf")},
        data={
            "veteran_name": "James T. Milner",
            "conditions": "PTSD (DC 9411), Ear Condition (DC 6260)"
        }
    )

print(response.json()["confirmation_number"])  # e.g. VA-2026-NOD-048821
```

---

## API Keys

Keys are injected via `<meta>` tags in `index.html` — never hardcoded in JS.

| Key | Where to get it |
|---|---|
| `VA_API_KEY` | [VA Benefits Reference Data API sandbox](https://developer.va.gov/explore/api/benefits-reference-data/sandbox-access) |
| `VA_FORMS_API_KEY` | [VA Forms API sandbox](https://developer.va.gov/explore/api/va-forms/sandbox-access) |

---

## Running Tests

```bash
# Python tests (from repo root)
pip install pytest hypothesis
pytest mock_va_portal/tests/ -v

# JS tests (from mock_va_portal/)
cd mock_va_portal
npm install
npx vitest --run
```

---

## Project Structure

```
mock_va_portal/
├── index.html          # Veteran dashboard
├── confirmation.html   # Appeal confirmation page
├── style.css           # Shared stylesheet (USWDS-inspired, no CDN)
├── va_api.js           # VA API calls + submission polling
├── confirmation.js     # Confirmation page logic
├── profiles.js         # 3 demo veteran profiles + nav switcher
├── server.py           # Flask backend (POST /submit-appeal, GET /submissions)
└── tests/              # pytest + vitest test suite (34 tests)

testcase/
├── james_millner/      # James T. Milner — PTSD DBQ, ALS DBQ, Ear DBQ, Decision Letter
└── robert-graza/       # Robert Garza — PTSD DBQ, Arthritis DBQ, Amputation DBQ

backend/
├── agents/             # Parser, Auditor agents
├── tools/              # CFR lookup, PACT Act check, TDIU check, combined rating
└── data/               # CFR Title 38 Part 4, VA pay rates, PACT Act conditions
```

---

## Disclaimer

Demo mock portal — VetClaim AI HackUSF 2026. Not affiliated with the U.S. Department of Veterans Affairs. This tool is informational only and does not constitute legal advice.
