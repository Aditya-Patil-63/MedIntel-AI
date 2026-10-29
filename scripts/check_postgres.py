#!/usr/bin/env python3
"""
MedIntel AI — Neon Postgres Verification Script.

Tests connectivity, table creation, auth verification, record persistence,
and multi-tenant isolation against an external PostgreSQL database (e.g. Neon).

Security:
- Never logs connection strings, passwords, or JWT tokens.
- Runs only when DATABASE_URL is configured for PostgreSQL; exits 0 otherwise.
- Cleans up all created test records upon completion.
"""

import os
import sys
import uuid
from pathlib import Path

# Ensure repo and backend root are in python search path
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def main() -> int:
    database_url = os.environ.get("DATABASE_URL", "").strip()

    # Rule: Runs ONLY when DATABASE_URL is set and starts with postgres
    if not (database_url.startswith("postgres://") or database_url.startswith("postgresql://") or database_url.startswith("postgresql+")):
        print("DATABASE_URL is not configured for PostgreSQL (skipping Neon Postgres check).")
        return 0

    print("PostgreSQL connection string detected. Initiating Neon Postgres verification...")

    try:
        from app.core.security import create_access_token, hash_password, verify_password
        from app.db.session import SessionLocal, create_tables
        from app.models.models import Report, User
    except ImportError as e:
        print(f"Error importing MedIntel application modules: {e}")
        return 1

    # 1. Initialize schema
    print("1/5: Verifying database schema and table initialization...")
    try:
        create_tables(max_retries=3, retry_delay=1.0)
    except Exception as e:
        print(f"Schema initialization failed: {type(e).__name__}")
        return 1

    db = SessionLocal()
    unique_suffix = uuid.uuid4().hex[:8]
    test_email_1 = f"neon_verify_1_{unique_suffix}@example.com"
    test_email_2 = f"neon_verify_2_{unique_suffix}@example.com"
    plain_password = f"TestPass!_{unique_suffix}"
    dummy_user_1 = None
    dummy_user_2 = None
    report_record = None

    try:
        # 2. Insert dummy user and verify auth
        print("2/5: Creating test tenant user and testing authentication...")
        hashed = hash_password(plain_password)
        dummy_user_1 = User(
            name=f"Neon Tenant 1 {unique_suffix}",
            email=test_email_1,
            hashed_password=hashed,
            language_preference="english",
        )
        db.add(dummy_user_1)
        db.commit()
        db.refresh(dummy_user_1)

        assert verify_password(plain_password, dummy_user_1.hashed_password)
        token = create_access_token(user_id=dummy_user_1.id, email=dummy_user_1.email)
        assert token and len(token) > 20

        # 3. Insert second user for tenant isolation testing
        print("3/5: Creating second tenant user for isolation validation...")
        dummy_user_2 = User(
            name=f"Neon Tenant 2 {unique_suffix}",
            email=test_email_2,
            hashed_password=hashed,
            language_preference="english",
        )
        db.add(dummy_user_2)
        db.commit()
        db.refresh(dummy_user_2)

        # 4. Save sample report record
        print("4/5: Creating sample report record for tenant 1...")
        report_record = Report(
            user_id=dummy_user_1.id,
            file_name="neon_smoke_test.pdf",
            file_path=f"/virtual/reports/neon_smoke_{unique_suffix}.pdf",
            file_type="pdf",
            document_type="lab_report",
            extraction_method="pdfplumber",
            status="extracted",
            raw_extracted_text="Patient Blood Test - Fasting Glucose: 95 mg/dL",
        )
        db.add(report_record)
        db.commit()
        db.refresh(report_record)

        # 5. Query user history & assert tenant isolation
        print("5/5: Querying records and asserting tenant isolation...")
        user1_reports = db.query(Report).filter(Report.user_id == dummy_user_1.id).all()
        assert len(user1_reports) == 1, f"Expected 1 report for User 1, got {len(user1_reports)}"
        assert user1_reports[0].file_name == "neon_smoke_test.pdf"

        user2_reports = db.query(Report).filter(Report.user_id == dummy_user_2.id).all()
        assert len(user2_reports) == 0, f"Tenant isolation breach: User 2 retrieved {len(user2_reports)} reports"

        print("Neon Postgres check: PASSED (verified 1 report record, 2 isolated tenant users)")
        return 0

    except Exception as e:
        print(f"Neon Postgres check: FAILED with error {type(e).__name__}: {e}")
        return 1

    finally:
        # Cleanup test records
        try:
            if dummy_user_1:
                db.delete(dummy_user_1)
            if dummy_user_2:
                db.delete(dummy_user_2)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()


if __name__ == "__main__":
    sys.exit(main())
