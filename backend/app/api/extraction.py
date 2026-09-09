"""
MedIntel AI — Document Extraction API Endpoint.

Exposes POST /api/v1/extract for document ingestion and text extraction.
Phase 4: PDF & OCR Pipeline.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

# Ensure repository root is on sys.path for importing root modules (ocr, ml)
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ocr.document_processor import DocumentProcessor
from ocr.models import DocumentExtractionResult
from ocr.ocr_engine import (
    DocumentSizeExceededError,
    InvalidDocumentError,
    OCREngineUnavailableError,
)
from app.core.config import settings

logger = logging.getLogger("medintel.extraction")

router = APIRouter(prefix="/api/v1", tags=["Extraction"])

# Module-level singleton processor initialized with settings
processor = DocumentProcessor(
    default_ocr_engine=settings.DEFAULT_OCR_ENGINE,
    max_file_size_bytes=settings.MAX_UPLOAD_SIZE_BYTES,
)


@router.post(
    "/extract",
    response_model=DocumentExtractionResult,
    summary="Extract text from medical PDF or image",
    description=(
        "Uploads a medical report or prescription document (PDF or image) and extracts "
        "raw text with page-level confidence scores. This endpoint strictly performs "
        "document text extraction and does NOT perform medical diagnosis or classification."
    ),
)
async def extract_document(
    file: UploadFile = File(..., description="Medical report PDF or image file"),
    engine: Optional[str] = Query(
        None,
        description="Optional OCR engine preference: 'tesseract' or 'easyocr'",
    ),
) -> DocumentExtractionResult:
    """
    Handle document upload, validate file attributes, and invoke extraction pipeline.
    """
    filename = file.filename or "unknown_document"

    try:
        # Read file contents
        content = await file.read()
        file_size = len(content)

        # Privacy guardrail: Log only metadata, NEVER extracted clinical text
        logger.info(
            "Received document extraction request: filename=%s, size_bytes=%d, engine_pref=%s",
            filename,
            file_size,
            engine,
        )

        result = processor.process_document(
            file_bytes=content,
            filename=filename,
            engine_name=engine,
        )

        logger.info(
            "Extraction completed: filename=%s, extractor=%s, pages=%d, confidence=%.3f",
            filename,
            result.extractor,
            result.total_pages,
            result.confidence,
        )

        return result

    except DocumentSizeExceededError as e:
        logger.warning("Upload size exceeded: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except InvalidDocumentError as e:
        logger.warning("Invalid document submitted (%s): %s", filename, str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except OCREngineUnavailableError as e:
        logger.error("Requested OCR engine unavailable: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.exception("Unexpected error during document extraction: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during extraction: {str(e)}",
        ) from e
