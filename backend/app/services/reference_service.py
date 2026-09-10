"""
MedIntel AI — Phase 6: Reference Service Layer.

Orchestrates deterministic reference-range analysis, medical value parsing,
and optional database persistence into the SQLite test_results schema.

Safety Guarantees:
    - Zero disease predictions or clinical diagnostic declarations.
    - Zero duplication of reference-range evaluation logic (uses reference/ module).
    - Enforces verification safety gate (distinguishes raw extractions from user-verified data).
    - Preserves audit citations on every persisted record and response.
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

# Ensure repo root is on sys.path so reference module is accessible
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from reference.analyzer import ReferenceAnalyzer
from reference.models import (
    AnalysisResult,
    AnalysisStatus,
    Classification,
    ParsedMeasurement,
    ParserStatus,
    PatientContext,
    TestMeasurement,
)
from reference.parser import MedicalValueParser
from reference.ranges import ReferenceRangeRegistry, get_default_registry

from app.models.models import Report, TestResult
from app.schemas.reference import (
    AnalysisResultSchema,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    MeasurementInputSchema,
    ParseAndAnalyzeRequest,
    ParseAndAnalyzeResponse,
    ParsedAndAnalyzedItemSchema,
    PatientContextSchema,
    ReferenceRangeSummarySchema,
)

logger = logging.getLogger("medintel.reference")


class ReferenceService:
    """
    Bridge service connecting FastAPI endpoints to the core deterministic
    ReferenceAnalyzer and MedicalValueParser subsystems.
    """

    def __init__(
        self,
        registry: Optional[ReferenceRangeRegistry] = None,
        analyzer: Optional[ReferenceAnalyzer] = None,
        parser: Optional[MedicalValueParser] = None,
    ) -> None:
        """Initialize service with singleton parser and analyzer instances."""
        self.registry = registry or get_default_registry()
        self.analyzer = analyzer or ReferenceAnalyzer(registry=self.registry)
        self.parser = parser or MedicalValueParser(registry=self.registry)

    @staticmethod
    def _to_patient_context(
        ctx_schema: Optional[PatientContextSchema],
    ) -> Optional[PatientContext]:
        """Convert Pydantic PatientContextSchema to internal PatientContext model."""
        if not ctx_schema:
            return None
        return PatientContext(age=ctx_schema.age, sex=ctx_schema.sex)

    @staticmethod
    def _to_analysis_schema(
        analysis: AnalysisResult,
        is_user_verified: bool = False,
        persisted_id: Optional[int] = None,
    ) -> AnalysisResultSchema:
        """Convert internal AnalysisResult to API response schema."""
        ref_summary: Optional[ReferenceRangeSummarySchema] = None
        if analysis.reference_range:
            ref = analysis.reference_range
            ref_summary = ReferenceRangeSummarySchema(
                canonical_name=ref.canonical_name,
                unit=ref.unit,
                normal_low=ref.normal_low,
                normal_high=ref.normal_high,
                critical_low=ref.critical_low,
                critical_high=ref.critical_high,
                source=ref.source,
                citation=ref.citation,
                reference_type=ref.reference_type.value if hasattr(ref.reference_type, "value") else str(ref.reference_type),
                verification_status=ref.verification_status.value if hasattr(ref.verification_status, "value") else str(ref.verification_status),
            )

        return AnalysisResultSchema(
            original_test_name=analysis.original_test_name,
            canonical_name=analysis.canonical_name,
            numeric_value=analysis.numeric_value,
            original_value_text=analysis.original_value_text,
            unit=analysis.unit,
            normalized_unit=analysis.normalized_unit,
            classification=analysis.classification.value if analysis.classification else None,
            analysis_status=analysis.status.value,
            reference_range=ref_summary,
            reference_source=analysis.reference_source,
            is_user_verified=is_user_verified,
            persisted_test_result_id=persisted_id,
            warnings=analysis.warnings,
            disclaimer=analysis.disclaimer,
        )

    def analyze_batch(
        self,
        request: BatchAnalysisRequest,
        db: Optional[Session] = None,
    ) -> BatchAnalysisResponse:
        """
        Evaluate a batch of structured medical measurements.
        Optionally persists results if persist=True and a valid report_id is provided.
        """
        # Validate report existence if persistence is requested
        if request.persist:
            if db is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session required for persistence.",
                )
            if request.report_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="report_id is required when persist=True.",
                )
            report = db.query(Report).filter(Report.id == request.report_id).first()
            if not report:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report with id {request.report_id} not found.",
                )

        shared_ctx = self._to_patient_context(request.patient_context)
        results: List[AnalysisResultSchema] = []
        classified_count = 0

        for m in request.measurements:
            effective_ctx = self._to_patient_context(m.context) or shared_ctx
            test_meas = TestMeasurement(
                test_name=m.test_name,
                value=m.value if m.value is not None else m.test_value_text,
                unit=m.unit,
                context=effective_ctx,
            )

            # Core deterministic reference evaluation
            analysis_outcome = self.analyzer.analyze(test_meas)

            persisted_id: Optional[int] = None
            if request.persist and db is not None:
                # Map deterministic classification to DB enum
                db_class = (
                    analysis_outcome.classification.value.lower()
                    if analysis_outcome.classification
                    else None
                )
                db_record = TestResult(
                    report_id=request.report_id,
                    test_name=m.test_name,
                    canonical_name=analysis_outcome.canonical_name,
                    test_value=analysis_outcome.numeric_value,
                    test_value_text=str(m.value) if m.value is not None else m.test_value_text,
                    unit=analysis_outcome.normalized_unit or m.unit,
                    reference_range_low=(
                        analysis_outcome.reference_range.normal_low
                        if analysis_outcome.reference_range
                        else None
                    ),
                    reference_range_high=(
                        analysis_outcome.reference_range.normal_high
                        if analysis_outcome.reference_range
                        else None
                    ),
                    classification=db_class,
                    reference_source=analysis_outcome.reference_source,
                    analysis_status=analysis_outcome.status.value,
                    is_user_verified=1 if m.is_user_verified else 0,
                )
                db.add(db_record)
                db.flush()
                persisted_id = db_record.id

            if analysis_outcome.classification:
                classified_count += 1

            results.append(
                self._to_analysis_schema(
                    analysis_outcome,
                    is_user_verified=m.is_user_verified,
                    persisted_id=persisted_id,
                )
            )

        if request.persist and db is not None:
            db.commit()

        # Privacy-conscious logging (counts and metadata only, NEVER clinical values)
        logger.info(
            "Reference batch analysis completed: submitted=%d, classified=%d, persisted=%s",
            len(request.measurements),
            classified_count,
            request.persist,
        )

        return BatchAnalysisResponse(
            success=True,
            total_submitted=len(request.measurements),
            total_classified=classified_count,
            report_id=request.report_id,
            results=results,
        )

    def parse_and_analyze_text(
        self,
        request: ParseAndAnalyzeRequest,
        db: Optional[Session] = None,
    ) -> ParseAndAnalyzeResponse:
        """
        Parse raw document or OCR text and evaluate extracted measurements.
        Enforces user verification safety gate (defaults to is_user_verified=False).
        """
        # Validate report existence if persistence is requested
        if request.persist:
            if db is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session required for persistence.",
                )
            if request.report_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="report_id is required when persist=True.",
                )
            report = db.query(Report).filter(Report.id == request.report_id).first()
            if not report:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report with id {request.report_id} not found.",
                )

        shared_ctx = self._to_patient_context(request.patient_context)
        parsed_items = self.parser.parse_text(
            request.text,
            include_unrecognized=request.include_unrecognized,
        )

        output_items: List[ParsedAndAnalyzedItemSchema] = []
        analyzed_count = 0

        for parsed in parsed_items:
            analysis_schema: Optional[AnalysisResultSchema] = None

            # Only analyze recognized or candidate measurement items
            if parsed.status != ParserStatus.UNRECOGNIZED_ANALYTE:
                test_meas = parsed.to_test_measurement(context=shared_ctx)
                analysis_outcome = self.analyzer.analyze(test_meas)

                persisted_id: Optional[int] = None
                if request.persist and db is not None:
                    db_class = (
                        analysis_outcome.classification.value.lower()
                        if analysis_outcome.classification
                        else None
                    )
                    db_record = TestResult(
                        report_id=request.report_id,
                        test_name=parsed.raw_analyte or "Unknown",
                        canonical_name=analysis_outcome.canonical_name,
                        test_value=analysis_outcome.numeric_value,
                        test_value_text=parsed.value_text,
                        unit=analysis_outcome.normalized_unit or parsed.unit,
                        reference_range_low=(
                            analysis_outcome.reference_range.normal_low
                            if analysis_outcome.reference_range
                            else None
                        ),
                        reference_range_high=(
                            analysis_outcome.reference_range.normal_high
                            if analysis_outcome.reference_range
                            else None
                        ),
                        classification=db_class,
                        reference_source=analysis_outcome.reference_source,
                        analysis_status=analysis_outcome.status.value,
                        is_user_verified=1 if request.is_user_verified else 0,
                    )
                    db.add(db_record)
                    db.flush()
                    persisted_id = db_record.id

                analyzed_count += 1
                analysis_schema = self._to_analysis_schema(
                    analysis_outcome,
                    is_user_verified=request.is_user_verified,
                    persisted_id=persisted_id,
                )

            output_items.append(
                ParsedAndAnalyzedItemSchema(
                    parsed_line=parsed.raw_line,
                    parsed_analyte=parsed.raw_analyte,
                    canonical_name=parsed.canonical_name,
                    parser_status=parsed.status.value,
                    extracted_reference_range=parsed.extracted_reference_range,
                    extraction_confidence=parsed.extraction_confidence,
                    analysis=analysis_schema,
                )
            )

        if request.persist and db is not None:
            db.commit()

        logger.info(
            "Parse-and-analyze completed: lines=%d, measurements_analyzed=%d, persisted=%s",
            len(output_items),
            analyzed_count,
            request.persist,
        )

        return ParseAndAnalyzeResponse(
            success=True,
            total_lines_parsed=len(output_items),
            total_measurements_analyzed=analyzed_count,
            report_id=request.report_id,
            items=output_items,
        )


# Module-level singleton service instance
reference_service = ReferenceService()
