import pandas as pd

VALID_DIAG_PROC_PAIRS = {
    ("A09", "OPD-CONSULT-01"),
    ("J18.9", "OPD-CONSULT-01"),
    ("O80", "MAT-DELIVERY-02"),
    ("S72.0", "SURG-ORTHO-04"),
    ("K35.8", "SURG-GEN-03"),
    ("N18.9", "DIAL-SESSION-05"),
    ("E11.9", "OPD-CHRONIC-06"),
    ("I10", "OPD-CHRONIC-06"),
}

REQUIRED_BIODATA_FIELDS = [
    "patient_full_name", "patient_dob", "patient_sha_number", "patient_phone"
]

def is_blank(val):
    return pd.isna(val) or str(val).strip() == ""

def check_preauth(row):
    if row.get("preauth_required") and str(row.get("preauth_required")).lower() in ("true", "1"):
        status = str(row.get("preauth_status", "")).lower()
        number = row.get("preauth_number", "")
        if status != "approved" or is_blank(number):
            return "Pre-authorization missing or not approved."
    return None

def check_biodata(row):
    missing = [f for f in REQUIRED_BIODATA_FIELDS if is_blank(row.get(f))]
    if missing:
        return f"Incomplete patient bio-data: missing {', '.join(missing)}."
    return None

def check_coding(row):
    pair = (row.get("diagnosis_code"), row.get("procedure_code"))
    if pair not in VALID_DIAG_PROC_PAIRS:
        return "Diagnosis and procedure code combination not recognized."
    return None

RULES = [
    ("preauth", check_preauth),
    ("biodata", check_biodata),
    ("coding", check_coding),
]

def evaluate_claim(row):
    reasons = []
    modes = []
    for mode, rule_fn in RULES:
        reason = rule_fn(row)
        if reason:
            reasons.append(reason)
            modes.append(mode)
    if len(reasons) == 0:
        risk = "Clean"
    elif len(reasons) == 1:
        risk = "At Risk"
    else:
        risk = "High Risk"
    return risk, "; ".join(reasons), ",".join(modes)

def run(input_csv, output_csv):
    df = pd.read_csv(input_csv, dtype=str)
    # cast preauth_required back to bool-like for the check
    df["preauth_required"] = df["preauth_required"].apply(lambda x: str(x).strip().lower() == "true")

    results = df.apply(evaluate_claim, axis=1, result_type="expand")
    results.columns = ["risk_status", "flag_reasons", "flagged_rule_ids"]
    out = pd.concat([df, results], axis=1)
    out.to_csv(output_csv, index=False)
    return out

if __name__ == "__main__":
    out = run("synthetic_sha_claims.csv", "claims_with_risk_output.csv")

    print("=== Risk status distribution ===")
    print(out["risk_status"].value_counts())
    print()

    # QA against ground truth _synthetic_failure_mode
    print("=== QA against ground truth ===")
    correct = 0
    mismatches = []
    for _, row in out.iterrows():
        truth = row["_synthetic_failure_mode"]
        detected_modes = set(row["flagged_rule_ids"].split(",")) if row["flagged_rule_ids"] else set()
        if truth == "clean":
            ok = len(detected_modes) == 0
        else:
            ok = truth in detected_modes
        if ok:
            correct += 1
        else:
            mismatches.append((row["claim_id"], truth, row["flagged_rule_ids"]))

    print(f"{correct}/{len(out)} claims correctly classified vs ground truth")
    if mismatches:
        print("Mismatches:")
        for m in mismatches:
            print(" ", m)
