import os
import json
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

def evaluate_claims(input_csv_path: str, output_csv_path: str) -> str:
    """Evaluates a batch of SHA claims from an input CSV file and writes the results to an output CSV.
    Each claim is run through pre-authorization, patient bio-data, and coding mismatch checks.
    The output CSV includes additional columns for risk_status, flag_reasons, and flagged_rule_ids.

    Args:
        input_csv_path (str): The absolute path to the input CSV file containing claims.
        output_csv_path (str): The absolute path to the output CSV file to write the results.

    Returns:
        str: A JSON string containing summary statistics of the evaluation.
    """
    if not os.path.exists(input_csv_path):
        return json.dumps({"error": f"Input file not found: {input_csv_path}"})

    try:
        df = pd.read_csv(input_csv_path, dtype=str)
        # Cast preauth_required back to bool-like for evaluation
        df["preauth_required"] = df["preauth_required"].apply(lambda x: str(x).strip().lower() == "true")

        results = df.apply(evaluate_claim, axis=1, result_type="expand")
        results.columns = ["risk_status", "flag_reasons", "flagged_rule_ids"]
        out = pd.concat([df, results], axis=1)

        # Make sure parent directory of output path exists
        out_dir = os.path.dirname(output_csv_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir)

        out.to_csv(output_csv_path, index=False)

        # Build summary statistics
        counts = out["risk_status"].value_counts().to_dict()
        summary = {
            "status": "success",
            "total_claims": len(out),
            "distribution": counts
        }
        return json.dumps(summary)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate SHA rejection-risk rules on a claims CSV export.")
    parser.add_argument("input_csv", help="Path to input claims CSV")
    parser.add_argument("output_csv", help="Path to output evaluated claims CSV")
    args = parser.parse_args()

    res = evaluate_claims(args.input_csv, args.output_csv)
    print(res)
