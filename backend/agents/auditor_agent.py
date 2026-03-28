"""
Auditor Agent - VetClaim AI

Receives parsed VA document text, extracts structured claim data via Gemini,
audits each condition against CFR Title 38 Part 4, PACT Act, TDIU criteria,
and combined rating math. Outputs an AuditResult with flags for the Advocate.

Uses Google ADK (google-adk) LlmAgent.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure backend root is on path for sibling imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google.adk.agents import LlmAgent

from tools.cfr_lookup import cfr_lookup, cfr_compare_rating
from tools.pact_act_check import pact_act_check
from tools.tdiu_check import tdiu_check
from tools.va_pay_lookup import va_pay_lookup, calculate_pay_impact
from tools.combined_rating import calculate_combined_rating, check_combined_rating_error


# ---------------------------------------------------------------------------
# Tool wrappers
# All tools exposed to the LLM must be plain Python callables.
# ADK passes the LLM's arguments directly as keyword args.
# ---------------------------------------------------------------------------

def tool_cfr_lookup(diagnostic_code: str) -> str:
    """
    Look up a VA diagnostic code in CFR Title 38 Part 4.
    Returns the condition name, CFR section, rating criteria at every percentage
    level, and the maximum possible rating.

    Args:
        diagnostic_code: VA diagnostic code string, e.g. '9411', '8045', '6260'.
    """
    result = cfr_lookup(diagnostic_code)
    return json.dumps(result, indent=2)


def tool_cfr_compare_rating(
    diagnostic_code: str,
    assigned_rating: int,
    symptom_description: str,
) -> str:
    """
    Compare the VA's assigned rating for a condition against CFR criteria.
    Returns the next higher rating level and its criteria so you can determine
    if the condition is UNDER_RATED.

    Args:
        diagnostic_code: VA diagnostic code, e.g. '9411'.
        assigned_rating: Rating percentage the VA currently assigns (integer).
        symptom_description: Description of the veteran's symptoms from records.
    """
    result = cfr_compare_rating(diagnostic_code, assigned_rating, symptom_description)
    return json.dumps(result, indent=2)


def tool_pact_act_check(
    condition_name: str,
    deployment_locations: list[str],
    service_era: str | None = None,
) -> str:
    """
    Check whether a condition qualifies as a PACT Act presumptive based on
    the veteran's deployment locations and service era. If eligible, no nexus
    letter is required - service connection is presumed by law.

    Args:
        condition_name: Name of the medical condition to check.
        deployment_locations: List of deployment locations, e.g. ['Iraq', 'Afghanistan'].
        service_era: Optional era string, e.g. 'post-9/11', 'Vietnam'.
    """
    result = pact_act_check(condition_name, deployment_locations, service_era)
    return json.dumps(result, indent=2)


def tool_tdiu_check(ratings: list[int], veteran_employed: bool = False) -> str:
    """
    Check whether the veteran qualifies for Total Disability Individual
    Unemployability (TDIU) under 38 CFR §4.16. TDIU pays at the 100% rate.

    Args:
        ratings: List of all individual disability ratings as integers, e.g. [50, 30, 10].
        veteran_employed: True if veteran is currently working full-time.
    """
    result = tdiu_check(ratings, veteran_employed)
    return json.dumps(result, indent=2)


def tool_combined_rating(ratings: list[int]) -> str:
    """
    Calculate the correct VA combined disability rating using whole-person math
    (38 CFR Part 4). The VA does NOT add ratings directly.
    Formula: combined = 1 - ((1-r1) * (1-r2) * ... * (1-rN)), rounded to nearest 10.

    Args:
        ratings: List of individual ratings as integers, e.g. [50, 30, 10].
    """
    result = calculate_combined_rating(ratings)
    return json.dumps(result, indent=2)


def tool_check_combined_rating_error(
    assigned_combined: int,
    individual_ratings: list[int],
) -> str:
    """
    Check whether the VA's stated combined rating in the decision letter is
    mathematically correct. Flags COMBINED_RATING_ERROR if discrepancy found.

    Args:
        assigned_combined: Combined rating stated in the VA decision letter.
        individual_ratings: List of individual condition ratings.
    """
    result = check_combined_rating_error(assigned_combined, individual_ratings)
    return json.dumps(result, indent=2)


def tool_va_pay_lookup(combined_rating: int, dependent_status: str = "alone") -> str:
    """
    Look up the monthly VA disability pay for a given combined rating.

    Args:
        combined_rating: Combined disability rating (10, 20, 30 ... 100).
        dependent_status: One of: 'alone', 'spouse', 'spouse_one_child',
                          'spouse_two_children', 'one_child'.
    """
    result = va_pay_lookup(combined_rating, dependent_status)
    return json.dumps(result, indent=2)


def tool_calculate_pay_impact(
    current_rating: int,
    potential_rating: int,
    dependent_status: str = "alone",
) -> str:
    """
    Calculate the monthly and annual dollar impact of a rating increase.

    Args:
        current_rating: Veteran's current combined rating.
        potential_rating: Potential combined rating after successful appeal.
        dependent_status: Veteran's dependent status (see tool_va_pay_lookup).
    """
    result = calculate_pay_impact(current_rating, potential_rating, dependent_status)
    return json.dumps(result, indent=2)


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
For EVERY condition, call tool_cfr_compare_rating with:
- The diagnostic code
- The assigned rating
- The symptom description from the records

Determine if symptoms described match higher rating criteria.

### Step 3 - Check PACT Act eligibility
For each condition AND for the veteran's deployment history overall:
- Call tool_pact_act_check for every condition
- Check if any denied conditions would be presumptive under PACT Act

### Step 4 - Check TDIU
Call tool_tdiu_check with ALL individual ratings.

### Step 5 - Verify combined rating math
Call tool_check_combined_rating_error with the stated combined rating and
all individual ratings.

### Step 6 - Calculate pay impact
Call tool_calculate_pay_impact comparing current vs. corrected rating.

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
Respond with a structured JSON audit result:

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
# Agent factory
# ---------------------------------------------------------------------------

def create_auditor_agent() -> LlmAgent:
    """Create and return the configured Auditor LlmAgent."""
    return LlmAgent(
        name="auditor_agent",
        model="gemini-2.0-flash",
        description=(
            "Audits VA disability claims against CFR Title 38 Part 4. "
            "Identifies under-ratings, wrong codes, PACT Act eligibility, "
            "TDIU eligibility, and combined rating errors."
        ),
        instruction=AUDITOR_INSTRUCTION,
        tools=[
            tool_cfr_lookup,
            tool_cfr_compare_rating,
            tool_pact_act_check,
            tool_tdiu_check,
            tool_combined_rating,
            tool_check_combined_rating_error,
            tool_va_pay_lookup,
            tool_calculate_pay_impact,
        ],
    )


# Singleton for import by orchestrator
auditor_agent = create_auditor_agent()
