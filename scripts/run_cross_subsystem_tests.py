"""
MedIntel AI — Phase 10: Cross-Subsystem End-to-End Test Runner.

Executes and aggregates test suites across the complete MedIntel AI ecosystem:
1. Backend Test Suites (FastAPI, Extraction, Reference Engine, ML Models, GenAI Service, SQLite Persistence)
2. Phase 10 End-to-End Integration Suite (Pipeline Unification & Verification Safety Gates)
3. Flutter Mobile Client Test Suites (Cubit state machines, UI Widgets, End-to-End Flow)
"""

import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXE = REPO_ROOT / "backend" / "venv" / "Scripts" / "python.exe"
MOBILE_DIR = REPO_ROOT / "mobile"


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def run_backend_tests():
    print_banner("1. BACKEND & SUBSYSTEM TEST SUITE (PYTEST)")
    start_time = time.time()

    cmd = [str(PYTHON_EXE), "-m", "pytest", "-q"]
    env = os.environ.copy()

    print(f"Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env, capture_output=True, text=True)

    elapsed = time.time() - start_time
    output = result.stdout.strip()
    if result.stderr:
        output += "\n" + result.stderr.strip()

    print(output)
    print(f"\nExecution time: {elapsed:.2f}s")
    success = (result.returncode == 0)
    print(f"Result: {'PASS' if success else 'FAIL'}")
    return success, elapsed, output


def run_flutter_tests():
    print_banner("2. FLUTTER MOBILE CLIENT TEST SUITE")
    start_time = time.time()

    cmd = ["flutter", "test"]
    print(f"Executing: {' '.join(cmd)} in {MOBILE_DIR}")
    result = subprocess.run(cmd, cwd=str(MOBILE_DIR), shell=True, capture_output=True, text=True)

    elapsed = time.time() - start_time
    output = result.stdout.strip()
    if result.stderr:
        output += "\n" + result.stderr.strip()

    print(output)
    print(f"\nExecution time: {elapsed:.2f}s")
    success = (result.returncode == 0)
    print(f"Result: {'PASS' if success else 'FAIL'}")
    return success, elapsed, output


def main():
    print_banner("MEDINTEL AI — PHASE 10 CROSS-SUBSYSTEM TEST RUNNER")
    print(f"Repository Root : {REPO_ROOT}")
    print(f"Python Executable: {PYTHON_EXE}")

    backend_ok, backend_time, _ = run_backend_tests()
    flutter_ok, flutter_time, _ = run_flutter_tests()

    print_banner("PHASE 10 TEST SUMMARY")
    print(f"Backend & Integration Tests : {'PASSED' if backend_ok else 'FAILED'} ({backend_time:.2f}s)")
    print(f"Flutter Mobile Tests        : {'PASSED' if flutter_ok else 'FAILED'} ({flutter_time:.2f}s)")

    all_passed = backend_ok and flutter_ok
    print(f"\nOVERALL RESULT: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
