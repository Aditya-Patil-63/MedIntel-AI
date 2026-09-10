"""
MedIntel AI — SQLAlchemy ORM Models.

Defines the database schema for the MedIntel AI application.
Phase 2 establishes the foundational schema. Later phases will
extend these models as OCR, ML, and GenAI features are added.

Tables:
    - users: Application users
    - reports: Uploaded medical reports / prescriptions
    - test_results: Extracted medical test values
    - predictions: ML risk prediction outputs
    - prescriptions: Extracted prescription information
    - medicines: Individual medicines from prescriptions
    - summaries: Generated health summary documents
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    """Return the current UTC timestamp (timezone-aware)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class User(Base):
    """Application user.

    Each user can upload multiple reports and receive predictions
    and summaries tied to their account.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    language_preference = Column(
        String(20), nullable=False, default="english",
        comment="Preferred language: english, hindi, marathi, gujarati",
    )
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    # Relationships
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="user", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class Report(Base):
    """Uploaded medical report or prescription document.

    Tracks the original file, its type, processing status,
    and extraction method used.
    """

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(
        Enum("pdf", "image", "scan", name="report_file_type"),
        nullable=False,
        comment="Type of uploaded file",
    )
    document_type = Column(
        Enum("lab_report", "prescription", "discharge_summary", "other", name="report_document_type"),
        nullable=False,
        default="lab_report",
        comment="Category of medical document",
    )
    extraction_method = Column(
        Enum("pdfplumber", "easyocr", "tesseract", "trocr", "manual", name="extraction_method_type"),
        nullable=True,
        comment="OCR / extraction method used (set during processing)",
    )
    status = Column(
        Enum("uploaded", "processing", "extracted", "verified", "analyzed", "failed", name="report_status_type"),
        nullable=False,
        default="uploaded",
    )
    raw_extracted_text = Column(Text, nullable=True, comment="Raw text output from extraction")
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="reports")
    test_results = relationship("TestResult", back_populates="report", cascade="all, delete-orphan")
    prescriptions = relationship("Prescription", back_populates="report", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="report", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="report", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Test Results (extracted medical values)
# ---------------------------------------------------------------------------

class TestResult(Base):
    """Individual medical test value extracted from a report.

    Each row represents one test (e.g., 'Blood Glucose', 'Creatinine')
    with its value, unit, and reference-range classification.
    Classification uses deterministic reference ranges — NOT ML.
    """

    __tablename__ = "test_results"
    __test__ = False

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    test_name = Column(String(255), nullable=False, comment="Name of the medical test")
    test_value = Column(Float, nullable=True, comment="Numeric value of the test result")
    test_value_text = Column(String(255), nullable=True, comment="Original text value (for non-numeric results)")
    unit = Column(String(50), nullable=True, comment="Unit of measurement (e.g., mg/dL, mmol/L)")
    reference_range_low = Column(Float, nullable=True, comment="Lower bound of normal reference range")
    reference_range_high = Column(Float, nullable=True, comment="Upper bound of normal reference range")
    classification = Column(
        Enum("low", "normal", "high", "critical", name="classification_type"),
        nullable=True,
        comment="Deterministic classification based on reference ranges",
    )
    is_user_verified = Column(Integer, nullable=False, default=0, comment="1 if user has verified this value")
    canonical_name = Column(String(255), nullable=True, comment="Canonical medical name of the analyte")
    reference_source = Column(String(255), nullable=True, comment="Authoritative reference source citation")
    analysis_status = Column(String(50), nullable=True, comment="Operational status code from reference analyzer")
    created_at = Column(DateTime, nullable=False, default=_utcnow)

    # Relationships
    report = relationship("Report", back_populates="test_results")


# ---------------------------------------------------------------------------
# Predictions (ML risk scores)
# ---------------------------------------------------------------------------

class Prediction(Base):
    """ML-generated risk prediction for a specific condition.

    These are probability scores for risk estimation — NOT diagnoses.
    Every prediction must include the mandatory safety disclaimer.
    """

    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    condition = Column(
        Enum("diabetes", "heart_disease", "kidney_disease", name="condition_type"),
        nullable=False,
        comment="Medical condition being assessed",
    )
    risk_score = Column(Float, nullable=False, comment="Probability score (0.0 to 1.0)")
    risk_level = Column(
        Enum("low", "moderate", "high", name="risk_level_type"),
        nullable=True,
        comment="Human-readable risk level derived from score",
    )
    model_name = Column(String(100), nullable=True, comment="Name of the ML model used")
    model_version = Column(String(50), nullable=True, comment="Version of the ML model")
    disclaimer = Column(
        Text,
        nullable=False,
        default=(
            "This is not a medical diagnosis. "
            "Please consult a qualified healthcare professional."
        ),
        comment="Mandatory safety disclaimer — required on every prediction",
    )
    created_at = Column(DateTime, nullable=False, default=_utcnow)

    # Relationships
    report = relationship("Report", back_populates="predictions")


# ---------------------------------------------------------------------------
# Prescriptions
# ---------------------------------------------------------------------------

class Prescription(Base):
    """Prescription information extracted from a document.

    Links to individual medicines prescribed within this prescription.
    """

    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_name = Column(String(255), nullable=True)
    hospital_name = Column(String(500), nullable=True)
    prescription_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True, comment="Additional notes from the prescription")
    is_user_verified = Column(Integer, nullable=False, default=0, comment="1 if user has verified this data")
    created_at = Column(DateTime, nullable=False, default=_utcnow)

    # Relationships
    report = relationship("Report", back_populates="prescriptions")
    medicines = relationship("Medicine", back_populates="prescription", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Medicines
# ---------------------------------------------------------------------------

class Medicine(Base):
    """Individual medicine entry within a prescription."""

    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prescription_id = Column(
        Integer, ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    medicine_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=True, comment="e.g., 500mg, 10ml")
    frequency = Column(String(100), nullable=True, comment="e.g., twice daily, as needed")
    duration = Column(String(100), nullable=True, comment="e.g., 7 days, 2 weeks")
    instructions = Column(Text, nullable=True, comment="Additional instructions")
    created_at = Column(DateTime, nullable=False, default=_utcnow)

    # Relationships
    prescription = relationship("Prescription", back_populates="medicines")


# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------

class Summary(Base):
    """Generated health summary document.

    Contains the GenAI-generated explanation, translated text,
    and a reference to the downloadable PDF if generated.
    """

    __tablename__ = "summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(
        String(20), nullable=False, default="english",
        comment="Language of this summary: english, hindi, marathi, gujarati",
    )
    summary_text = Column(Text, nullable=True, comment="Generated plain-language summary")
    pdf_path = Column(String(1000), nullable=True, comment="Path to downloadable PDF summary")
    disclaimer = Column(
        Text,
        nullable=False,
        default=(
            "This is not a medical diagnosis. "
            "Please consult a qualified healthcare professional."
        ),
        comment="Mandatory safety disclaimer",
    )
    created_at = Column(DateTime, nullable=False, default=_utcnow)
    updated_at = Column(DateTime, nullable=False, default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="summaries")
    report = relationship("Report", back_populates="summaries")
