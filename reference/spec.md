# SHA Claims Intelligence Platform — v0.1 Spec

## 1. Problem Statement
Since Kenya's shift from NHIF to SHA, facilities are seeing claim rejections and delayed
reimbursements. Finance officers currently find out a claim is bad *after* submission —
when it's too late to fix cheaply. This tool catches likely-rejected claims **before**
submission and gives finance officers a live view of claim health.

## 2. Users
- **Primary:** Facility finance/claims officer (submits and tracks claims)
- **Secondary:** Facility administrator / medical records officer (owns data quality upstream)

## 3. Scope (MVP)
In scope:
- Ingest a batch of claims (CSV/Excel export from KenyaEMR, or manual entry)
- Run 3 rejection-risk rules against each claim
- Flag high-risk claims with a reason, before submission
- Dashboard: claim volume, rejection-risk rate, breakdown by rejection reason, trend over time

Out of scope (v0.1):
- Live/real-time API integration with KenyaEMR (batch upload only, for now)
- Actually submitting claims to SHA (this is a pre-check tool, not a submission tool)
- Multi-facility / multi-tenant billing — single facility first

## 4. Input Data Model (synthetic, pending real KenyaEMR export)
One row = one claim. Proposed fields, grouped by what each rule needs:

| Field | Type | Used by rule |
|---|---|---|
| `claim_id` | string | — (identifier) |
| `patient_id` | string | Rule 2 |
| `patient_full_name` | string | Rule 2 |
| `patient_dob` | date | Rule 2 |
| `patient_sha_number` | string | Rule 2 |
| `patient_phone` | string | Rule 2 |
| `visit_date` | date | — |
| `service_type` | enum (outpatient/inpatient) | Rule 1 |
| `preauth_required` | boolean | Rule 1 |
| `preauth_number` | string (nullable) | Rule 1 |
| `preauth_status` | enum (approved/pending/none) | Rule 1 |
| `diagnosis_code` | ICD-10 string | Rule 3 |
| `procedure_code` | SHA benefit package code | Rule 3 |
| `claim_amount` | number | — |
| `submission_date` | date | — |

**Synthetic sample:** I'll generate ~30–50 rows of realistic dummy claims covering clean
claims and each of the 3 failure modes, so we can build and test the rule engine without
waiting on a real export. We swap in the real KenyaEMR schema once you have one — field
names may shift, but the rule engine logic below shouldn't need to change.

## 5. Rule Engine (v0.1 — 3 rules, deterministic, explainable)

**Rule 1 — Missing pre-authorization**
Flag if `service_type` requires pre-auth AND (`preauth_status` != "approved" OR
`preauth_number` is empty).
→ Reason shown to user: *"Pre-authorization missing or not approved."*

**Rule 2 — Incomplete patient/bio-data**
Flag if any of `patient_full_name`, `patient_dob`, `patient_sha_number`, `patient_phone`
is empty, or `patient_sha_number` fails a basic format check.
→ Reason shown to user: *"Incomplete patient bio-data: [missing fields]."*

**Rule 3 — Coding mismatch**
Flag if `diagnosis_code` and `procedure_code` combination isn't in a known-valid
diagnosis↔procedure mapping table (a lookup we build from SHA benefit package rules).
→ Reason shown to user: *"Diagnosis and procedure code combination not recognized."*

Each claim gets a **risk status**: Clean / At Risk (1 flag) / High Risk (2+ flags).

## 6. Output / Dashboard (Tableau, fed by Python backend)
- **Summary cards:** total claims, % at risk, % high risk, estimated KES at risk
- **Breakdown by rejection reason** (bar chart)
- **Trend over time** (are we improving week over week?)
- **Claims table** — filterable, drill into any flagged claim to see the reason(s)

## 7. Architecture (proposed)
```
KenyaEMR export (CSV) → Python ingestion/cleaning script → Rule engine (Python)
→ Output table (CSV/DB) → Tableau dashboard (reads output table)
```
- Python: pandas for the rule engine, straightforward and testable
- Storage: start with flat files/SQLite; move to a real DB only if needed
- Tableau: connects directly to the output table, refreshed on each batch run

## 8. Open Questions (to resolve as we go, not blockers)
- Exact KenyaEMR export field names/format — confirm once you have a real export
- Where the diagnosis↔procedure valid-combination table comes from — SHA benefit
  package documentation, or built up from observed patterns in historical claims?
- Single-facility MVP vs. building multi-tenant from day one

## 9. Build Order
1. Generate synthetic claims sample (~30–50 rows, mix of clean + each failure mode)
2. Build rule engine against synthetic data, unit-test each rule
3. Wire up output table
4. Build Tableau dashboard against output table
5. Swap in real KenyaEMR data once available; adjust field mapping only
