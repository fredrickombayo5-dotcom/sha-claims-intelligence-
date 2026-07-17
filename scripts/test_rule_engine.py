import os
import json
import pandas as pd
import pytest
from rule_engine import evaluate_claims, evaluate_claim

def test_rule_engine_qa():
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    input_csv = os.path.join(project_dir, "reference", "sample_claims.csv")
    output_csv = os.path.join(script_dir, "test_output_claims.csv")

    # Clean previous test output if exists
    if os.path.exists(output_csv):
        os.remove(output_csv)

    # Run batch evaluation
    res_str = evaluate_claims(input_csv, output_csv)
    res_json = json.loads(res_str)

    assert res_json["status"] == "success"
    assert res_json["total_claims"] == 40
    assert os.path.exists(output_csv)

    # Read evaluated output
    out = pd.read_csv(output_csv, dtype=str)

    # QA against ground truth _synthetic_failure_mode
    correct = 0
    mismatches = []
    for _, row in out.iterrows():
        truth = row["_synthetic_failure_mode"]
        detected_modes = set(row["flagged_rule_ids"].split(",")) if pd.notna(row["flagged_rule_ids"]) and row["flagged_rule_ids"] else set()
        
        if truth == "clean":
            ok = len(detected_modes) == 0
        else:
            ok = truth in detected_modes
        
        if ok:
            correct += 1
        else:
            mismatches.append((row["claim_id"], truth, row["flagged_rule_ids"]))

    # Assert 40/40 correct
    assert correct == 40, f"Mismatches found: {mismatches}"

    # Clean up test output file
    if os.path.exists(output_csv):
        os.remove(output_csv)
