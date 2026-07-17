---
name: sha-claims-intelligence
description: Build and extend the SHA Claims Intelligence Platform — a tool that ingests
  a Kenyan health facility's SHA claims data, flags likely-rejected claims before
  submission using a 3-rule risk engine, and surfaces results on a finance-officer
  dashboard. Load this skill when working on claim ingestion, the rejection-risk
  rule engine, the output data model, or the dashboard for this project.
---

# SHA Claims Intelligence Agent

## What this agent does
Takes a batch of SHA claims (from a KenyaEMR export), evaluates each claim against
3 rejection-risk rules, and produces a risk-scored output table that feeds a
finance-officer dashboard. This is a **pre-submission check**, not a claim
submission tool.

## Ground truth for this domain
From real facility experience (Bristol Park Hospital, Mama Lucy Kibaki Hospital),
in order of frequency, SHA claim rejections happen because of:
1. Missing or unapproved pre-authorization
2. Incomplete patient/bio-data
3. Coding mismatches (diagnosis code vs. procedure code)

Do not invent additional rejection reasons without confirming them against real
claims data or the user's domain knowledge — these 3 are the validated set for v0.1.

## Full spec
See `reference/spec.md` for the complete design: input data model, exact rule
logic per rejection reason, dashboard fields, and proposed architecture
(Python rule engine → output table → Tableau dashboard). Read this before
generating or modifying code for this project.

## Reference implementation
`reference/rule_engine_reference.py` is a working, tested Python implementation
of the 3-rule engine (pandas-based). It scored 40/40 correct against the
synthetic sample in `reference/sample_claims.csv`. Treat this as a correct
reference for rule logic — if reimplementing in a different language or as an
ADK tool/agent, preserve this exact logic:
- **Pre-auth rule**: flag if `preauth_required` is true AND
  (`preauth_status` != "approved" OR `preauth_number` is blank)
- **Bio-data rule**: flag if any of `patient_full_name`, `patient_dob`,
  `patient_sha_number`, `patient_phone` is blank
- **Coding rule**: flag if the (`diagnosis_code`, `procedure_code`) pair is not
  in the known-valid combination set

## Sample data
`reference/sample_claims.csv` — 40 synthetic claims (16 clean, 24 with exactly
one injected failure mode), including a `_synthetic_failure_mode` column for
QA purposes only. Drop that column before treating data as production-like.
**This is placeholder data** — the user has not yet confirmed the real
KenyaEMR export schema. Field names may need to change once a real export is
available; the rule logic should not need to change.

## What's still open (don't assume these are decided)
- Real KenyaEMR export field names/format
- Where the diagnosis↔procedure valid-combination table should ultimately come
  from (SHA benefit package docs vs. learned from historical claims)
- Single-facility vs. multi-tenant architecture

## ADK Tool & Agent Step: Claims Risk Engine

The rule engine has been implemented as a script tool at [rule_engine.py](file:///c:/Users/hp/Downloads/sha-claims-agent-skill-extracted/sha-claims-agent-skill/scripts/rule_engine.py). This tool is designed to be directly imported or invoked by the agent to process batches of claims.

### Tool Signatures

- **`evaluate_claims(input_csv_path: str, output_csv_path: str) -> str`**
  - **Description**: Ingests a CSV claims export, evaluates each claim against the 3 rejection-risk rules, and writes a risk-scored CSV output.
  - **Returns**: A JSON string containing summary stats (`{"status": "success", "total_claims": 40, "distribution": {"Clean": 16, "At Risk": 20, "High Risk": 4}}`).

- **CLI Usage**:
  You can run the script directly using Python:
  ```powershell
  python scripts/rule_engine.py <input_csv> <output_csv>
  ```

## Suggested next steps for this agent in Antigravity/ADK
1. Add an ingestion step that reads a KenyaEMR CSV export (schema TBD — ask the user for a real sample before hardcoding field names)
2. Wire output to a table Tableau can read directly
3. Keep the rule engine deterministic and explainable — finance officers need to see *why* a claim was flagged, not just a risk score

