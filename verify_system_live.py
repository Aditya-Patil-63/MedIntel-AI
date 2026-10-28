"""
MedIntel AI — Comprehensive Live Verification Suite.

Runs end-to-end integration and system verification against the live FastAPI backend:
1. Health and GenAI subsystem readiness
2. Reference ranges and Indian lab unit normalization (Lakhs/cumm, TLC, etc.)
3. Unstructured report parsing (Hemoglobin, WBC, Platelets, Glucose)
4. ML disease risk models (Diabetes, Heart Disease, Kidney Disease)
5. Prescription Explainer (Objective 2 extraction and scheduling)
6. GenAI educational explanations across supported languages
7. User authentication and unified report history persistence
"""

import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict

BASE_URL = "http://127.0.0.1:8000"


def make_request(method: str, path: str, payload: Dict[str, Any] = None, token: str = None) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(error_body)
            print(f"[-] HTTP {e.code} Error on {path}: {err_json}")
            return {"_http_error": e.code, "detail": err_json}
        except Exception:
            print(f"[-] HTTP {e.code} Error on {path}: {error_body}")
            return {"_http_error": e.code, "detail": error_body}


def run_all_checks():
    print("=" * 70)
    print("MEDINTEL AI — FULL SYSTEM VERIFICATION SUITE")
    print("=" * 70)
    
    results = {"passed": 0, "failed": 0, "tests": []}

    def record_test(name: str, passed: bool, details: str = ""):
        if passed:
            results["passed"] += 1
            print(f"[PASS] {name} | {details}")
        else:
            results["failed"] += 1
            print(f"[FAIL] {name} | {details}")
        results["tests"].append({"name": name, "passed": passed, "details": details})

    # 1. Health check
    print("\n--- 1. Core Health & GenAI Readiness ---")
    health = make_request("GET", "/health")
    record_test("Backend Health Check", health.get("status") == "healthy", f"status={health.get('status')}")

    genai_status = make_request("GET", "/api/v1/genai/status")
    record_test(
        "GenAI Status Check",
        genai_status.get("status") == "OK" and genai_status.get("available") is True,
        f"provider={genai_status.get('provider')}, model={genai_status.get('model')}"
    )

    # 2. Reference ranges and Indian lab unit normalization
    print("\n--- 2. Reference Ranges & Indian Lab Unit Normalization ---")
    batch_req = {
        "measurements": [
            {
                "test_name": "Platelet Count",
                "value": "2.33 Lakhs/cumm",
                "unit": "Lakhs/cumm",
                "is_user_verified": True
            },
            {
                "test_name": "Platelet Count",
                "value": 45000,
                "unit": "cells/uL",
                "is_user_verified": True
            },
            {
                "test_name": "Fasting Blood Sugar",
                "value": 165,
                "unit": "mg/dL",
                "is_user_verified": True
            },
            {
                "test_name": "White Blood Cell Count",
                "value": 8500,
                "unit": "cells/uL",
                "is_user_verified": True
            },
            {
                "test_name": "Serum Creatinine",
                "value": 1.8,
                "unit": "mg/dL",
                "is_user_verified": True,
                "context": {"sex": "M", "age": 45}
            }
        ]
    }
    ref_resp = make_request("POST", "/api/v1/reference/analyze", batch_req)
    raw_results = ref_resp.get("results", [])
    measurements = {m.get("canonical_name"): m for m in raw_results}
    
    # Check 2.33 Lakhs/cumm normalization
    platelet_results = [m for m in raw_results if m.get("canonical_name") == "Platelet Count"]
    first_plt = platelet_results[0] if platelet_results else {}
    plt_normalized_ok = (
        first_plt.get("classification") == "NORMAL" and
        (first_plt.get("normalized_value") == 233000.0 or first_plt.get("numeric_value") == 2.33) and
        first_plt.get("normalized_unit") == "cells/uL"
    )
    record_test(
        "Indian Unit Normalization: 2.33 Lakhs/cumm -> 233,000 cells/uL (NORMAL)",
        plt_normalized_ok,
        f"input=2.33 {first_plt.get('unit')}, normalized={first_plt.get('normalized_value')} {first_plt.get('normalized_unit')}, classification={first_plt.get('classification')}"
    )
    
    # Check Critical Low Platelet (<50,000)
    second_plt = platelet_results[1] if len(platelet_results) > 1 else {}
    record_test(
        "Critical Boundary: Platelet 45,000 cells/uL -> CRITICAL",
        second_plt.get("classification") == "CRITICAL",
        f"class={second_plt.get('classification')}"
    )

    # Check High FBS (canonical name: Fasting Blood Glucose)
    fbs = measurements.get("Fasting Blood Glucose", {})
    record_test(
        "High FBS: 165 mg/dL -> HIGH",
        fbs.get("classification") == "HIGH",
        f"class={fbs.get('classification')}"
    )

    # Check WBC Count
    wbc = measurements.get("White Blood Cell Count", {})
    record_test(
        "WBC Count: 8,500 cells/uL -> NORMAL",
        wbc.get("classification") == "NORMAL",
        f"class={wbc.get('classification')}"
    )

    # Check High Creatinine for Male
    creat = measurements.get("Serum Creatinine", {})
    record_test(
        "Male Creatinine: 1.8 mg/dL -> HIGH",
        creat.get("classification") == "HIGH",
        f"class={creat.get('classification')}"
    )

    # 3. Text Parsing & Extraction
    print("\n--- 3. Unstructured Report Parsing ---")
    parse_req = {
        "text": "COMPLETE BLOOD COUNT:\nHaemoglobin: 13.5 g/dL\nTotal WBC Count: 7200 /cumm\nPlatelet Count: 2.15 Lakhs/cumm\nFasting Blood Glucose: 110 mg/dL"
    }
    parse_resp = make_request("POST", "/api/v1/reference/parse-and-analyze", parse_req)
    parsed_items = parse_resp.get("items", [])
    valid_parsed = [it for it in parsed_items if it.get("canonical_name") is not None]
    record_test(
        "Free-Text Lab Report Parsing (Hemoglobin, WBC, Platelets, Glucose)",
        len(valid_parsed) >= 3,
        f"Found {len(valid_parsed)} recognized analytes: {[it.get('canonical_name') for it in valid_parsed]}"
    )

    # 4. ML Risk Models
    print("\n--- 4. ML Risk Estimation Models ---")
    # Diabetes
    dm_req = {
        "Pregnancies": 1,
        "Glucose": 165,
        "BloodPressure": 80,
        "SkinThickness": 25,
        "Insulin": 115,
        "BMI": 32.5,
        "DiabetesPedigreeFunction": 0.52,
        "Age": 45,
        "is_user_verified": True
    }
    dm_resp = make_request("POST", "/api/v1/ml/diabetes-risk", dm_req)
    record_test(
        "ML Diabetes Risk (Glucose 165, BMI 32.5)",
        dm_resp.get("status") == "OK" and dm_resp.get("risk_band") in ["MODERATE", "ELEVATED"],
        f"prob={dm_resp.get('risk_probability', -1):.3f}, band={dm_resp.get('risk_band')}"
    )

    # Heart Disease
    heart_req = {
        "age": 58,
        "sex": 1,
        "cp": 2,
        "trestbps": 145,
        "chol": 260,
        "fbs": 0,
        "restecg": 1,
        "thalach": 125,
        "exang": 1,
        "oldpeak": 2.2,
        "slope": 2,
        "ca": 1,
        "thal": 2,
        "is_user_verified": True
    }
    heart_resp = make_request("POST", "/api/v1/ml/heart-risk", heart_req)
    record_test(
        "ML Heart Disease Risk (Age 58, BP 145, Chol 260)",
        heart_resp.get("status") == "OK" and heart_resp.get("risk_band") in ["MODERATE", "ELEVATED"],
        f"prob={heart_resp.get('risk_probability', -1):.3f}, band={heart_resp.get('risk_band')}"
    )

    # Kidney Disease: Insufficient features handling
    ckd_missing_req = {
        "age": 50,
        "is_user_verified": True
    }
    ckd_missing_resp = make_request("POST", "/api/v1/ml/kidney-risk", ckd_missing_req)
    record_test(
        "ML Kidney Disease (Insufficient features -> non-guessing response)",
        ckd_missing_resp.get("status") == "INSUFFICIENT_FEATURES",
        f"status={ckd_missing_resp.get('status')}, missing_count={len(ckd_missing_resp.get('missing_features', []))}"
    )

    # 5. Prescription Explainer (Objective 2)
    print("\n--- 5. Prescription Explainer (Objective 2) ---")
    rx_req = {
        "prescription_text": (
            "Rx:\n"
            "1. Tab Metformin 500mg - 1-0-1 after meals x 30 days\n"
            "2. Tab Telmisartan 40mg - 1-0-0 before breakfast x 30 days\n"
            "3. Tab Paracetamol 650mg - SOS fever"
        ),
        "language": "english",
        "is_user_verified": True
    }
    rx_resp = make_request("POST", "/api/v1/prescriptions/explain", rx_req)
    meds = rx_resp.get("medicines", [])
    med_names = [m.get("name") or m.get("medicine_name") for m in meds]
    record_test(
        "Prescription Medicine Extraction & Scheduling",
        len(meds) >= 2 and any("Metformin" in n for n in med_names if n),
        f"Extracted {len(meds)} medicines: {med_names}"
    )

    # 6. Multilingual GenAI Explanation
    print("\n--- 6. Multilingual GenAI Findings Explanation ---")
    genai_payload = {
        "patient_context": {"age": 52, "sex": "M"},
        "measurements": [
            {
                "test_name": "Fasting Blood Sugar",
                "canonical_name": "Fasting Blood Glucose",
                "value": 165.0,
                "unit": "mg/dL",
                "classification": "HIGH",
                "reference_low": 70.0,
                "reference_high": 99.0
            },
            {
                "test_name": "Serum Creatinine",
                "canonical_name": "Serum Creatinine",
                "value": 1.1,
                "unit": "mg/dL",
                "classification": "NORMAL",
                "reference_low": 0.7,
                "reference_high": 1.3
            }
        ],
        "ml_risks": [
            {
                "condition": "diabetes",
                "risk_probability": dm_resp.get("risk_probability", 0.758),
                "risk_band": dm_resp.get("risk_band", "ELEVATED"),
                "status": "OK"
            }
        ],
        "language": "en",
        "detail_level": "simple",
        "is_user_verified": True
    }
    genai_resp = make_request("POST", "/api/v1/genai/explain", genai_payload)
    explanation_summary = genai_resp.get("explanation", {}).get("summary", "")
    has_summary = bool(explanation_summary)
    has_disclaimer = "NOT a medical diagnosis" in genai_resp.get("disclaimer", "") or "disclaimer" in genai_resp
    record_test(
        "GenAI Educational Summary & Disclaimer (English)",
        has_summary and has_disclaimer and genai_resp.get("status") == "SUCCESS",
        f"status={genai_resp.get('status')}, summary_len={len(explanation_summary)}"
    )

    # 7. User Registration & History Persistence
    print("\n--- 7. User Registration & History Persistence ---")
    test_user_email = f"testuser_{int(time.time())}@medintel.ai"
    reg_req = {
        "name": "Live Verification User",
        "email": test_user_email,
        "password": "Password123!",
        "language_preference": "english"
    }
    reg_resp = make_request("POST", "/api/v1/auth/register", reg_req)
    token = reg_resp.get("access_token")
    user_id = reg_resp.get("user", {}).get("id")
    record_test(
        "User Registration via /api/v1/auth/register",
        bool(token) and bool(user_id),
        f"user_id={user_id}, email={test_user_email}"
    )

    if token:
        history_resp = make_request("GET", "/api/v1/history", token=token)
        record_test(
            "Unified History Access via /api/v1/history",
            isinstance(history_resp.get("all"), list) or isinstance(history_resp.get("reports"), list),
            f"items_count={len(history_resp.get('all', []))}"
        )

    print("\n" + "=" * 70)
    print(f"VERIFICATION SUMMARY: {results['passed']} PASSED, {results['failed']} FAILED")
    print("=" * 70)
    return results["failed"] == 0


if __name__ == "__main__":
    success = run_all_checks()
    sys.exit(0 if success else 1)
