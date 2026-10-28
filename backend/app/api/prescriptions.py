"""
MedIntel AI — Prescription & Medicine Explainer Router.

Objective 2: Helping patients understand what the doctor has prescribed,
including the medicines, their purpose, and how they should be taken.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.models import Medicine, Prescription, Report, User, _utcnow
from app.schemas.prescription import (
    PrescriptionExplainRequest,
    PrescriptionExplainResponse,
)
from app.services.prescription_service import PrescriptionService
from ocr.document_processor import DocumentProcessor
from app.core.config import settings

logger = logging.getLogger("medintel.prescriptions_api")

router = APIRouter(prefix="/api/v1/prescriptions", tags=["Prescriptions"])

document_processor = DocumentProcessor(
    default_ocr_engine=settings.DEFAULT_OCR_ENGINE,
    max_file_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES,
)


@router.post(
    "/explain",
    response_model=PrescriptionExplainResponse,
    summary="Explain prescription medicines, purpose, and schedule",
    description=(
        "Translates prescription text or medication names into clear patient-friendly "
        "explanations including the purpose of each medicine, dosage schedule (morning/night, "
        "before/after meals), and practical safety precautions in English, Hindi, Marathi, or Gujarati."
    ),
)
async def explain_prescription(request: PrescriptionExplainRequest) -> PrescriptionExplainResponse:
    """Analyze and explain prescribed medications."""
    try:
        response = PrescriptionService.explain_prescription(request)
        return response
    except Exception as e:
        logger.error(f"Error explaining prescription: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explain prescription: {str(e)}",
        )


@router.post(
    "/extract-and-explain",
    response_model=PrescriptionExplainResponse,
    summary="Extract from prescription image/document and explain",
    description="Uploads a prescription document (image or PDF), runs OCR extraction, and returns structured medicine explanations.",
)
async def extract_and_explain_prescription(
    file: UploadFile = File(..., description="Prescription image or document"),
    language: str = Form("english", description="Preferred output language: english, hindi, marathi, gujarati"),
) -> PrescriptionExplainResponse:
    """Extract text from prescription file and generate medicine explanations."""
    filename = file.filename or "prescription_upload"
    file_bytes = await file.read()

    # 1. First attempt direct multimodal vision analysis via Gemini
    try:
        gemini_vision_res = PrescriptionService.explain_image_with_gemini(
            file_bytes=file_bytes,
            filename=filename,
            lang=language,
        )
        if gemini_vision_res is not None and gemini_vision_res.medicines:
            return gemini_vision_res
    except Exception as exc:
        logger.warning(f"Multimodal vision prescription extraction error, falling back to OCR: {exc}")

    try:
        extraction_result = document_processor.process_document(
            file_bytes=file_bytes,
            filename=filename,
        )
        extracted_text = extraction_result.full_text or ""
    except Exception as e:
        logger.warning(f"OCR extraction warning on prescription: {e}")
        extracted_text = ""

    req = PrescriptionExplainRequest(
        prescription_text=extracted_text,
        language=language,
        is_user_verified=True,
    )

    return PrescriptionService.explain_prescription(req)


@router.get(
    "/history",
    response_model=List[Dict[str, Any]],
    summary="Get all prescription history records for the current user",
)
def get_user_prescription_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Retrieve all saved prescription records belonging exclusively to the authenticated user."""
    reports = (
        db.query(Report)
        .filter(Report.user_id == current_user.id, Report.document_type == "prescription")
        .order_by(Report.updated_at.desc(), Report.created_at.desc())
        .all()
    )

    results: List[Dict[str, Any]] = []
    for rep in reports:
        if rep.raw_extracted_text:
            try:
                data = json.loads(rep.raw_extracted_text)
                if "id" not in data or not data["id"]:
                    data["id"] = f"rx_{rep.id}"
                data["type"] = "prescription"
                if "created_at" not in data or not data["created_at"]:
                    data["created_at"] = rep.created_at.isoformat() if rep.created_at else _utcnow().isoformat()
                if "updated_at" not in data or not data["updated_at"]:
                    data["updated_at"] = rep.updated_at.isoformat() if rep.updated_at else data["created_at"]
                results.append(data)
                continue
            except json.JSONDecodeError:
                pass

        results.append({
            "id": f"rx_{rep.id}",
            "type": "prescription",
            "title": rep.file_name or "Prescription",
            "document_name": rep.file_name or "Prescription",
            "created_at": rep.created_at.isoformat() if rep.created_at else _utcnow().isoformat(),
            "updated_at": rep.updated_at.isoformat() if rep.updated_at else _utcnow().isoformat(),
            "medicines": [],
            "disclaimer": "This explanation is for educational purposes only. Always follow your prescribing doctor's instructions.",
        })

    return results


@router.post(
    "/history",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED,
    summary="Save or update a prescription in history for current user",
)
def save_user_prescription(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Store or update a prescription record linked to the authenticated user."""
    doc_name = payload.get("document_name") or payload.get("title") or "Prescription"
    prescription_id_str = str(payload.get("id", "")).strip()

    payload["type"] = "prescription"
    now_iso = _utcnow().isoformat()
    if "created_at" not in payload or not payload["created_at"]:
        payload["created_at"] = now_iso
    payload["updated_at"] = now_iso

    existing_report: Optional[Report] = None
    if prescription_id_str.startswith("rx_"):
        try:
            num_id = int(prescription_id_str.replace("rx_", ""))
            existing_report = (
                db.query(Report)
                .filter(Report.id == num_id, Report.user_id == current_user.id)
                .first()
            )
        except ValueError:
            pass

    if not existing_report and prescription_id_str:
        user_rx_reports = (
            db.query(Report)
            .filter(Report.user_id == current_user.id, Report.document_type == "prescription")
            .all()
        )
        for rep in user_rx_reports:
            if rep.raw_extracted_text:
                try:
                    d = json.loads(rep.raw_extracted_text)
                    if d.get("id") == prescription_id_str:
                        existing_report = rep
                        break
                except Exception:
                    pass

    # Deduplicate by medicine names if id wasn't matched
    if not existing_report:
        user_rx_reports = (
            db.query(Report)
            .filter(Report.user_id == current_user.id, Report.document_type == "prescription")
            .all()
        )
        payload_meds = [
            str(m.get("name") or m.get("medicine_name", "")).strip().lower()
            for m in payload.get("medicines", [])
            if isinstance(m, dict)
        ]
        if payload_meds:
            for rep in user_rx_reports:
                if rep.raw_extracted_text:
                    try:
                        d = json.loads(rep.raw_extracted_text)
                        existing_meds = [
                            str(m.get("name") or m.get("medicine_name", "")).strip().lower()
                            for m in d.get("medicines", [])
                            if isinstance(m, dict)
                        ]
                        if payload_meds == existing_meds and d.get("document_name") == doc_name:
                            existing_report = rep
                            payload["id"] = d.get("id", f"rx_{rep.id}")
                            payload["created_at"] = d.get("created_at", rep.created_at.isoformat())
                            break
                    except Exception:
                        pass

    if existing_report:
        existing_report.updated_at = _utcnow()
        existing_report.raw_extracted_text = json.dumps(payload)
        existing_report.file_name = doc_name
        db.commit()
        db.refresh(existing_report)
        logger.info(
            "Updated existing prescription in history: db_id=%d, client_id=%s, user_id=%d",
            existing_report.id,
            payload.get("id"),
            current_user.id,
        )
        return payload

    # Create new database record
    report = Report(
        user_id=current_user.id,
        file_name=doc_name,
        file_path=payload.get("image_reference") or "client_prescription",
        file_type="image",
        document_type="prescription",
        status="analyzed",
        raw_extracted_text=json.dumps(payload),
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    if not prescription_id_str:
        payload["id"] = f"rx_{report.id}"
        report.raw_extracted_text = json.dumps(payload)
        db.commit()

    # Also persist to prescriptions and medicines relational tables
    try:
        rx_entry = Prescription(
            report_id=report.id,
            doctor_name=payload.get("doctor_name"),
            hospital_name=payload.get("hospital_name"),
            notes=payload.get("doctor_notes") or payload.get("general_guidance"),
            is_user_verified=1,
            created_at=_utcnow(),
        )
        db.add(rx_entry)
        db.commit()
        db.refresh(rx_entry)

        for med in payload.get("medicines", []):
            if isinstance(med, dict):
                m_name = str(med.get("medicine_name") or med.get("name", "Unknown"))
                m_dosage = med.get("dosage")
                m_freq = med.get("when_to_take") or med.get("schedule")
                m_inst = med.get("instructions") or med.get("purpose")
                med_entry = Medicine(
                    prescription_id=rx_entry.id,
                    medicine_name=m_name,
                    dosage=str(m_dosage) if m_dosage else None,
                    frequency=str(m_freq) if m_freq else None,
                    instructions=str(m_inst) if m_inst else None,
                    created_at=_utcnow(),
                )
                db.add(med_entry)
        db.commit()
    except Exception as e:
        logger.warning("Could not persist relational prescription entry: %s", e)

    logger.info(
        "Saved new prescription in history: db_id=%d, client_id=%s, user_id=%d",
        report.id,
        payload.get("id"),
        current_user.id,
    )
    return payload


@router.delete(
    "/history/{prescription_id}",
    summary="Delete a prescription record belonging to current user",
)
def delete_user_prescription(
    prescription_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """Delete a prescription only if it belongs to the authenticated user."""
    target_report: Optional[Report] = None

    if prescription_id.startswith("rx_"):
        try:
            numeric_id = int(prescription_id.replace("rx_", ""))
            target_report = (
                db.query(Report)
                .filter(Report.id == numeric_id, Report.user_id == current_user.id)
                .first()
            )
        except ValueError:
            pass

    if not target_report and prescription_id.isdigit():
        target_report = (
            db.query(Report)
            .filter(Report.id == int(prescription_id), Report.user_id == current_user.id)
            .first()
        )

    if not target_report:
        all_user_rx = (
            db.query(Report)
            .filter(Report.user_id == current_user.id, Report.document_type == "prescription")
            .all()
        )
        for rep in all_user_rx:
            if rep.raw_extracted_text:
                try:
                    data = json.loads(rep.raw_extracted_text)
                    if data.get("id") == prescription_id:
                        target_report = rep
                        break
                except Exception:
                    pass

    if not target_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prescription not found or does not belong to your account.",
        )

    db.delete(target_report)
    db.commit()
    return {"status": "success", "message": "Prescription deleted successfully"}
