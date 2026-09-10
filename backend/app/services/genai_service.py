"""
MedIntel AI — Phase 8: GenAI Explanation Service.

Orchestrates Generative AI explanations, provider selection, user verification
safety gating, multilingual translation, and database persistence into SQLite.

Core Safety Invariants:
    - User Verification Gate: Rejects unverified requests without invoking providers.
    - Zero Guessing: Does not invent missing test values or clinical facts.
    - Upstream Invariance: Strictly preserves Phase 6 reference classifications
      and Phase 7 ML probabilities and risk bands.
    - Non-Diagnostic: Never diagnoses diseases or prescribes treatments.
    - Prompt-Injection Defense: All clinical inputs treated strictly as passive data.
    - Zero Key Leaks: Never exposes API keys, paths, or secrets in responses.
"""

import logging
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Report, Summary
from app.schemas.genai import (
    GenAIExplainRequest,
    GenAIExplainResponse,
    GenAIStatus,
    GenAIStatusResponse,
    MANDATORY_GENAI_DISCLAIMER,
    SupportedLanguage,
)
from app.services.genai.base import BaseGenAIProvider
from app.services.genai.mock_provider import MockGenAIProvider

logger = logging.getLogger("medintel.genai_service")


class GenAIExplanationService:
    """Service layer managing GenAI explanation generation and translation."""

    def __init__(self, provider: Optional[BaseGenAIProvider] = None) -> None:
        """Initialize service with optional provider override (useful for testing)."""
        self._provider_override = provider

    def get_provider(self) -> BaseGenAIProvider:
        """Resolve and return the configured GenAI provider.

        Returns:
            Instantiated BaseGenAIProvider.

        Raises:
            HTTPException: 503 if an unconfigured/unimplemented provider is requested,
                           500 if an invalid provider name is configured.
        """
        if self._provider_override is not None:
            return self._provider_override

        provider_setting = getattr(settings, "GENAI_PROVIDER", "mock").strip().lower()

        if provider_setting == "mock":
            return MockGenAIProvider()
        elif provider_setting == "gemini":
            logger.error("Gemini provider configured but not yet implemented in Phase 8 Step 3.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gemini provider is not yet implemented in this release. Please configure GENAI_PROVIDER='mock'.",
            )
        else:
            logger.error("Unknown GENAI_PROVIDER configured: %s", provider_setting)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unsupported GENAI_PROVIDER '{provider_setting}'. Supported: 'mock'.",
            )

    async def explain_findings(
        self,
        request: GenAIExplainRequest,
        db: Optional[Session] = None,
    ) -> GenAIExplainResponse:
        """Generate structured patient explanation from verified clinical findings.

        Args:
            request: Validated GenAIExplainRequest payload.
            db: Optional database session for report audit and summary persistence.

        Returns:
            GenAIExplainResponse.

        Raises:
            HTTPException: 400 if input is invalid or persist is requested without report_id,
                           404 if report_id does not exist,
                           500/503 for provider errors.
        """
        provider = self.get_provider()

        # ------------------------------------------------------------------
        # 1. MANDATORY USER VERIFICATION SAFETY GATE
        # ------------------------------------------------------------------
        if not request.is_user_verified:
            logger.warning("GenAI explanation halted: input findings are not user-verified.")
            return GenAIExplainResponse(
                status=GenAIStatus.VERIFICATION_REQUIRED,
                report_id=request.report_id,
                language=request.language,
                explanation=None,
                translated_summary=None,
                model_provider=provider.provider_name,
                model_name=provider.model_name,
                disclaimer=MANDATORY_GENAI_DISCLAIMER,
                persisted_summary_id=None,
            )

        # ------------------------------------------------------------------
        # 2. Input Completeness Check
        # ------------------------------------------------------------------
        if len(request.analytes) == 0 and len(request.ml_risks) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one verified analyte or ML risk finding is required to generate an explanation.",
            )

        # ------------------------------------------------------------------
        # 3. Report & Persistence Validation
        # ------------------------------------------------------------------
        report: Optional[Report] = None

        if request.persist and request.report_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="report_id is required when persist=True.",
            )

        if request.report_id is not None and db is not None:
            report = db.query(Report).filter(Report.id == request.report_id).first()
            if not report:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report with id {request.report_id} not found.",
                )

        if request.persist and db is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database session required for persistence.",
            )

        # ------------------------------------------------------------------
        # 4. Generate Explanation via Provider
        # ------------------------------------------------------------------
        try:
            base_payload = await provider.generate_explanation(request)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Provider failure during explanation generation: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while generating the educational explanation.",
            ) from exc

        # ------------------------------------------------------------------
        # 5. Multilingual Translation (if non-English)
        # ------------------------------------------------------------------
        translated_summary: Optional[str] = None
        final_payload = base_payload

        if request.language != SupportedLanguage.ENGLISH:
            try:
                final_payload, translated_summary = await provider.translate_explanation(
                    base_payload, request.language
                )
            except HTTPException:
                raise
            except Exception as exc:
                logger.exception("Provider failure during explanation translation: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while translating the educational explanation.",
                ) from exc

        # ------------------------------------------------------------------
        # 6. Database Persistence (if persist=True and report valid)
        # ------------------------------------------------------------------
        persisted_id: Optional[int] = None

        if request.persist and request.report_id is not None and db is not None and report is not None:
            try:
                # Map language enum to DB string
                lang_str = request.language.value
                summary_text_content = translated_summary or final_payload.summary

                summary_record = Summary(
                    user_id=report.user_id,
                    report_id=request.report_id,
                    language=lang_str,
                    summary_text=summary_text_content,
                    disclaimer=MANDATORY_GENAI_DISCLAIMER,
                )
                db.add(summary_record)
                db.commit()
                db.refresh(summary_record)
                persisted_id = summary_record.id
                logger.info("Persisted GenAI summary with id=%s for report_id=%s", persisted_id, request.report_id)
            except Exception as exc:
                db.rollback()
                logger.exception("Failed to persist GenAI summary into database: %s", exc)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to persist generated health summary to database.",
                ) from exc

        return GenAIExplainResponse(
            status=GenAIStatus.SUCCESS,
            report_id=request.report_id,
            language=request.language,
            explanation=final_payload,
            translated_summary=translated_summary,
            model_provider=provider.provider_name,
            model_name=provider.model_name,
            disclaimer=MANDATORY_GENAI_DISCLAIMER,
            persisted_summary_id=persisted_id,
        )

    async def get_service_status(self) -> GenAIStatusResponse:
        """Inspect and report the health and configuration of the GenAI service."""
        provider_setting = getattr(settings, "GENAI_PROVIDER", "mock").strip().lower()

        if provider_setting == "mock":
            provider = MockGenAIProvider()
            health = await provider.check_health()
            return GenAIStatusResponse(
                status="OK",
                provider=provider.provider_name,
                model=provider.model_name,
                available=health.get("available", True),
                mode=health.get("mode", "offline_deterministic_mock"),
                network_required=health.get("network_required", False),
            )
        elif provider_setting == "gemini":
            return GenAIStatusResponse(
                status="DEGRADED",
                provider="gemini",
                model=getattr(settings, "GEMINI_MODEL", "gemini-3.8-flash"),
                available=False,
                mode="unimplemented_in_step_3",
                network_required=True,
            )
        else:
            return GenAIStatusResponse(
                status="ERROR",
                provider=provider_setting,
                model="unknown",
                available=False,
                mode="unsupported_configuration",
                network_required=False,
            )


# Global singleton instance
genai_service = GenAIExplanationService()
