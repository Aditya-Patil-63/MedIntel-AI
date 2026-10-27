"""
MedIntel AI — Prescription & Medicine Explainer Router.

Objective 2: Helping patients understand what the doctor has prescribed,
including the medicines, their purpose, and how they should be taken.
"""

import logging
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

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
