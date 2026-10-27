"""
MedIntel AI — User Reports API Endpoints.

Provides user-scoped persistent storage and retrieval of medical report analyses.
Every operation is strictly partitioned by the authenticated user's ID.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.models import Report, TestResult, User

logger = logging.getLogger("medintel.reports")

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.get(
    "",
    response_model=List[Dict[str, Any]],
    summary="Get all medical reports for the current user",
)
def get_user_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Retrieve all saved analysis records belonging exclusively to the authenticated user."""
    reports = (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .all()
    )

    results: List[Dict[str, Any]] = []
    for rep in reports:
        if rep.raw_extracted_text:
            try:
                data = json.loads(rep.raw_extracted_text)
                # Ensure the report ID in the item matches or links
                if "id" not in data or not data["id"]:
                    data["id"] = f"rep_{rep.id}"
                results.append(data)
                continue
            except json.JSONDecodeError:
                pass

        # Fallback if raw text wasn't JSON
        results.append({
            "id": f"rep_{rep.id}",
            "created_at": rep.created_at.isoformat() if rep.created_at else datetime.now(timezone.utc).isoformat(),
            "document_name": rep.file_name or "Medical Report",
            "verified_measurement_count": 0,
            "reference_results": [],
            "total_classified": 0,
            "disclaimer": "This is not a medical diagnosis. Please consult a qualified healthcare professional.",
        })

    return results


@router.post(
    "",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Save a medical report analysis for the current user",
)
def save_user_report(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Store an immutable analysis snapshot linked to the authenticated user."""
    doc_name = payload.get("document_name", "Medical Report")
    report_id_str = str(payload.get("id", "")).strip()

    # Create new database record strictly linked to this user
    report = Report(
        user_id=current_user.id,
        file_name=doc_name,
        file_path="client_snapshot",
        file_type="pdf",
        document_type="lab_report",
        status="analyzed",
        raw_extracted_text=json.dumps(payload),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # If payload didn't specify an ID, assign the generated DB ID
    if not report_id_str:
        payload["id"] = f"rep_{report.id}"
        report.raw_extracted_text = json.dumps(payload)
        db.commit()

    # Also insert normalized test results into the test_results table if present
    ref_results = payload.get("reference_results", [])
    if isinstance(ref_results, list):
        for res in ref_results:
            if isinstance(res, dict) and "test_name" in res:
                tr = TestResult(
                    report_id=report.id,
                    test_name=str(res.get("test_name", "Unknown")),
                    test_value=float(res.get("value")) if res.get("value") is not None else None,
                    unit=str(res.get("unit", "")) if res.get("unit") else None,
                    reference_range_low=float(res.get("reference_low")) if res.get("reference_low") is not None else None,
                    reference_range_high=float(res.get("reference_high")) if res.get("reference_high") is not None else None,
                    classification=str(res.get("classification", "")).lower() or None,
                    is_user_verified=1,
                )
                db.add(tr)
        db.commit()

    logger.info(
        "Saved analysis report: db_id=%d, client_id=%s, user_id=%d, doc_name=%s",
        report.id,
        payload.get("id"),
        current_user.id,
        doc_name,
    )
    return payload


@router.get(
    "/trends",
    response_model=Dict[str, Any],
    summary="Get longitudinal health metrics and trends across user reports",
)
def get_user_health_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Aggregate analyte measurements across historical reports to track changes over time."""
    reports = (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .order_by(Report.created_at.asc())
        .all()
    )

    trends_map: Dict[str, List[Dict[str, Any]]] = {}

    for rep in reports:
        report_date = rep.created_at.strftime("%Y-%m-%d") if rep.created_at else "Unknown"
        report_id_str = f"rep_{rep.id}"

        # 1. Inspect raw_extracted_text JSON
        if rep.raw_extracted_text:
            try:
                data = json.loads(rep.raw_extracted_text)
                if data.get("id"):
                    report_id_str = data["id"]
                ref_results = data.get("reference_results", [])
                for res in ref_results:
                    if isinstance(res, dict) and "test_name" in res:
                        t_name = str(res.get("canonical_name") or res.get("test_name")).strip()
                        val = res.get("numeric_value") or res.get("value")
                        if val is not None:
                            try:
                                num_val = float(val)
                                if t_name not in trends_map:
                                    trends_map[t_name] = []
                                trends_map[t_name].append({
                                    "report_id": report_id_str,
                                    "date": report_date,
                                    "value": num_val,
                                    "unit": res.get("unit") or res.get("normalized_unit") or "",
                                    "classification": str(res.get("classification") or "NORMAL").upper(),
                                })
                            except (ValueError, TypeError):
                                pass
            except Exception:
                pass

        # 2. Also inspect DB test_results if trends_map is empty for this report
        test_records = db.query(TestResult).filter(TestResult.report_id == rep.id).all()
        for tr in test_records:
            t_name = tr.canonical_name or tr.test_name
            if tr.test_value is not None:
                # Avoid duplicate insertion if already in trends_map for this report
                existing = trends_map.get(t_name, [])
                if not any(item["report_id"] == report_id_str for item in existing):
                    if t_name not in trends_map:
                        trends_map[t_name] = []
                    trends_map[t_name].append({
                        "report_id": report_id_str,
                        "date": report_date,
                        "value": float(tr.test_value),
                        "unit": tr.unit or "",
                        "classification": (tr.classification or "NORMAL").upper(),
                    })

    return {
        "total_reports": len(reports),
        "tracked_metrics_count": len(trends_map),
        "trends": trends_map,
        "disclaimer": "This is not a medical diagnosis. Please consult a qualified healthcare professional.",
    }


@router.delete(
    "/{report_id}",
    summary="Delete a medical report belonging to the current user",
)
def delete_user_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Delete a report only if it belongs to the authenticated user."""
    # Try finding by numeric DB ID or by matching client ID inside JSON
    target_report: Optional[Report] = None

    if report_id.startswith("rep_"):
        try:
            numeric_id = int(report_id.replace("rep_", ""))
            target_report = (
                db.query(Report)
                .filter(Report.id == numeric_id, Report.user_id == current_user.id)
                .first()
            )
        except ValueError:
            pass

    if not target_report and report_id.isdigit():
        target_report = (
            db.query(Report)
            .filter(Report.id == int(report_id), Report.user_id == current_user.id)
            .first()
        )

    if not target_report:
        # Search by JSON payload id
        all_user_reports = (
            db.query(Report).filter(Report.user_id == current_user.id).all()
        )
        for rep in all_user_reports:
            if rep.raw_extracted_text:
                try:
                    data = json.loads(rep.raw_extracted_text)
                    if data.get("id") == report_id:
                        target_report = rep
                        break
                except Exception:
                    pass

    if not target_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or does not belong to your account.",
        )

    db.delete(target_report)
    db.commit()
    logger.info("Deleted report id=%d for user_id=%d", target_report.id, current_user.id)
    return {"status": "success", "message": "Report deleted successfully"}
