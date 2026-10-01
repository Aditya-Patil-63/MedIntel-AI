"""
MedIntel AI — Phase 10: Performance, Concurrency & Memory Benchmark Runner.

Executes automated latency, throughput, concurrency, and memory audits across all
core backend endpoints and ML inference engines.
"""

import asyncio
import gc
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Tuple
from unittest.mock import patch

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.main import app
from app.services.ml_risk_service import ml_risk_service


def get_process_memory_mb() -> float:
    """Return current process Resident Set Size (RSS) in Megabytes."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        return 0.0


def benchmark_endpoint(
    client: TestClient,
    method: str,
    path: str,
    payload: Any = None,
    concurrency: int = 20,
    total_requests: int = 100,
) -> Dict[str, Any]:
    """Benchmark an endpoint under concurrent simulated load."""
    latencies_ms: List[float] = []
    errors: int = 0

    def single_request() -> Tuple[bool, float]:
        t0 = time.perf_counter()
        try:
            if method.upper() == "GET":
                resp = client.get(path)
            else:
                resp = client.post(path, json=payload)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            ok = (resp.status_code == 200)
            return ok, elapsed_ms
        except Exception:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return False, elapsed_ms

    start_total = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(single_request) for _ in range(total_requests)]
        for f in futures:
            success, lat = f.result()
            latencies_ms.append(lat)
            if not success:
                errors += 1

    total_time_sec = time.perf_counter() - start_total
    latencies_ms.sort()

    mean_ms = sum(latencies_ms) / len(latencies_ms)
    p50_ms = latencies_ms[int(len(latencies_ms) * 0.50)]
    p95_ms = latencies_ms[int(len(latencies_ms) * 0.95)]
    p99_ms = latencies_ms[min(int(len(latencies_ms) * 0.99), len(latencies_ms) - 1)]
    min_ms = latencies_ms[0]
    max_ms = latencies_ms[-1]
    rps = total_requests / total_time_sec if total_time_sec > 0 else 0.0

    return {
        "endpoint": path,
        "method": method.upper(),
        "total_requests": total_requests,
        "concurrency": concurrency,
        "total_time_sec": total_time_sec,
        "mean_ms": mean_ms,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "p99_ms": p99_ms,
        "min_ms": min_ms,
        "max_ms": max_ms,
        "rps": rps,
        "errors": errors,
        "error_rate": (errors / total_requests) * 100.0,
    }


def main():
    print("=" * 80)
    print("  MEDINTEL AI — PHASE 10: PERFORMANCE, CONCURRENCY & MEMORY BENCHMARK")
    print("=" * 80)

    # Pre-warm environment
    gc.collect()
    mem_initial = get_process_memory_mb()
    print(f"Initial Process Memory (RSS): {mem_initial:.2f} MB")

    test_endpoints = [
        {
            "name": "Health Check Liveness",
            "method": "GET",
            "path": "/health",
            "payload": None,
        },
        {
            "name": "Deterministic Reference Analysis (Batch of 5)",
            "method": "POST",
            "path": "/api/v1/reference/analyze",
            "payload": {
                "measurements": [
                    {"test_name": "Glucose", "value": 92.0, "unit": "mg/dL", "is_user_verified": True},
                    {"test_name": "Hemoglobin", "value": 14.2, "unit": "g/dL", "is_user_verified": True},
                    {"test_name": "Serum Potassium", "value": 4.1, "unit": "mEq/L", "is_user_verified": True},
                    {"test_name": "Platelets", "value": 250000, "unit": "/uL", "is_user_verified": True},
                    {"test_name": "Creatinine", "value": 0.9, "unit": "mg/dL", "is_user_verified": True},
                ],
                "persist": False,
            },
        },
        {
            "name": "Unstructured Text Parse & Analyze",
            "method": "POST",
            "path": "/api/v1/reference/parse-and-analyze",
            "payload": {
                "text": (
                    "Patient Lab Report:\n"
                    "Fasting Blood Sugar: 98 mg/dL\n"
                    "Serum Creatinine: 0.9 mg/dL\n"
                    "Hemoglobin: 14.5 g/dL\n"
                    "Platelet Count: 230,000 /uL\n"
                ),
                "include_unrecognized": False,
            },
        },
        {
            "name": "Diabetes Risk ML Inference (Pima RF)",
            "method": "POST",
            "path": "/api/v1/ml/diabetes-risk",
            "payload": {
                "Pregnancies": 2,
                "Glucose": 115,
                "BloodPressure": 70,
                "SkinThickness": 25,
                "Insulin": 90,
                "BMI": 26.5,
                "DiabetesPedigreeFunction": 0.35,
                "Age": 38,
                "is_user_verified": True,
            },
        },
        {
            "name": "Heart Disease Risk ML Inference (Cleveland LogReg)",
            "method": "POST",
            "path": "/api/v1/ml/heart-risk",
            "payload": {
                "age": 52,
                "sex": 1,
                "cp": 2,
                "trestbps": 128,
                "chol": 210,
                "fbs": 0,
                "restecg": 1,
                "thalach": 155,
                "exang": 0,
                "oldpeak": 0.8,
                "slope": 2,
                "ca": 0,
                "thal": 3,
                "is_user_verified": True,
            },
        },
        {
            "name": "Kidney Disease Risk ML Inference (Apollo LogReg)",
            "method": "POST",
            "path": "/api/v1/ml/kidney-risk",
            "payload": {
                "age": 48,
                "bp": 70,
                "sg": 1.020,
                "al": 0,
                "su": 0,
                "rbc": "normal",
                "pc": "normal",
                "pcc": "notpresent",
                "ba": "notpresent",
                "bgr": 105,
                "bu": 32,
                "sc": 0.9,
                "sod": 140,
                "pot": 4.2,
                "hemo": 15.2,
                "pcv": 45,
                "wc": 7200,
                "rc": 5.1,
                "htn": "no",
                "dm": "no",
                "cad": "no",
                "appet": "good",
                "pe": "no",
                "ane": "no",
                "is_user_verified": True,
            },
        },
        {
            "name": "GenAI Educational Explanation (Offline Mock)",
            "method": "POST",
            "path": "/api/v1/genai/explain",
            "payload": {
                "is_user_verified": True,
                "language": "en",
                "analytes": [
                    {"test_name": "Glucose", "value": 98.0, "unit": "mg/dL", "classification": "NORMAL"},
                    {"test_name": "Hemoglobin", "value": 14.5, "unit": "g/dL", "classification": "NORMAL"},
                ],
                "ml_risks": [
                    {"condition": "diabetes", "risk_probability": 0.18, "risk_band": "LOW"},
                ],
            },
        },
    ]

    results = []

    with patch.object(settings, "GENAI_PROVIDER", "mock"):
        with TestClient(app) as client:
            # Warm-up call for each
            for ep in test_endpoints:
                if ep["method"] == "GET":
                    client.get(ep["path"])
                else:
                    client.post(ep["path"], json=ep["payload"])

            print("\nStarting concurrent load benchmarks (100 requests per endpoint, concurrency=20)...")
            print("-" * 80)
            print(f"{'Endpoint':<35} | {'Mean (ms)':<9} | {'P50 (ms)':<8} | {'P95 (ms)':<8} | {'P99 (ms)':<8} | {'RPS':<8} | {'Errors'}")
            print("-" * 80)

            for ep in test_endpoints:
                stats = benchmark_endpoint(
                    client=client,
                    method=ep["method"],
                    path=ep["path"],
                    payload=ep["payload"],
                    concurrency=20,
                    total_requests=100,
                )
                stats["name"] = ep["name"]
                results.append(stats)
                print(
                    f"{stats['endpoint']:<35} | "
                    f"{stats['mean_ms']:>8.2f}  | "
                    f"{stats['p50_ms']:>7.2f}  | "
                    f"{stats['p95_ms']:>7.2f}  | "
                    f"{stats['p99_ms']:>7.2f}  | "
                    f"{stats['rps']:>7.1f}  | "
                    f"{stats['errors']} ({stats['error_rate']:.1f}%)"
                )

    gc.collect()
    mem_final = get_process_memory_mb()
    mem_delta = mem_final - mem_initial
    print("-" * 80)
    print(f"Final Process Memory (RSS): {mem_final:.2f} MB (Delta: {mem_delta:+.2f} MB)")
    print("=" * 80)

    # Model caching audit
    print("\n[ML MODEL CACHE AUDIT]")
    for cond in ["diabetes", "heart_disease", "kidney_disease"]:
        p1 = ml_risk_service.get_predictor(cond)
        p2 = ml_risk_service.get_predictor(cond)
        is_cached = (p1 is p2)
        print(f" - {cond:<15}: in-memory singleton cache = {is_cached} (id={hex(id(p1))})")

    return results


if __name__ == "__main__":
    main()
