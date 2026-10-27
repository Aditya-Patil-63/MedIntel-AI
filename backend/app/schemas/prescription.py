"""
MedIntel AI — Prescription & Medicine Explainer Schemas.

Objective 2: Helping patients understand what the doctor has prescribed,
including the medicines, their purpose, and how they should be taken.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

MANDATORY_PRESCRIPTION_DISCLAIMER = (
    "This explanation is for educational and informational purposes only. "
    "Gemini-generated information must NOT override your doctor's prescribed instructions. "
    "If any medicine name or dosage cannot be confidently identified, it is flagged for confirmation "
    "by a pharmacist or doctor rather than guessing. Always follow your prescribing physician's guidance."
)


class PrescribedMedicineItem(BaseModel):
    """Structured breakdown of an individual prescribed medication matching Objective 2 table."""

    name: str = Field(..., description="Trade or brand name of medicine, including strength if present")
    medicine_name: Optional[str] = Field(None, description="Direct alias for medicine name in the table")
    generic_name: Optional[str] = Field(None, description="Active chemical or generic drug molecule")
    dosage: Optional[str] = Field(None, description="Prescribed dose, such as '2 ml', '1 tablet', or '500 mg'")
    purpose: str = Field(..., description="Simple explanation of what the medicine is used for")
    when_to_take: Optional[str] = Field(None, description="Prescribed timing, such as 'Before meals', 'After meals', or 'At bedtime'")
    schedule: str = Field("", description="Clear timing schedule (Morning/Afternoon/Night, Before or After meals)")
    instructions: str = Field("", description="Practical instructions on how it should be taken")
    precautions: Optional[str] = Field(None, description="Crucial precautions and side-effect awareness")
    needs_confirmation: bool = Field(
        False,
        description="Flagged True if handwriting recognition or extraction cannot confidently identify the medicine or dosage",
    )
    confidence_note: Optional[str] = Field(
        None,
        description="Safety advice prompting confirmation by a pharmacist or doctor rather than guessing",
    )

    def __init__(self, **data):
        if "medicine_name" in data and "name" not in data:
            data["name"] = data["medicine_name"]
        elif "name" in data and "medicine_name" not in data:
            data["medicine_name"] = data["name"]
        if "when_to_take" in data and not data.get("schedule"):
            data["schedule"] = data["when_to_take"]
        elif "schedule" in data and not data.get("when_to_take"):
            data["when_to_take"] = data["schedule"]
        super().__init__(**data)


class PrescriptionExplainRequest(BaseModel):
    """Request payload for explaining a medical prescription."""

    prescription_text: Optional[str] = Field(
        None,
        description="Raw or OCR extracted text from a printed or handwritten prescription",
    )
    medicines: Optional[List[str]] = Field(
        None,
        description="Optional list of medicine names or lines if entered directly by patient",
    )
    language: str = Field(
        "english",
        description="Preferred language for output: english, hindi, marathi, gujarati",
    )
    is_user_verified: bool = Field(
        True,
        description="User verification confirmation before clinical interpretation",
    )


class PrescriptionExplainResponse(BaseModel):
    """Complete patient-friendly prescription interpretation response."""

    doctor_notes: Optional[str] = Field(None, description="General diagnosis notes or instructions if mentioned")
    medicines: List[PrescribedMedicineItem] = Field(
        default_factory=list,
        description="List of explained medications with purpose, schedule, and how to take",
    )
    general_guidance: str = Field(..., description="Overall wellness and safety guidance for this prescription")
    questions_for_doctor: List[str] = Field(
        default_factory=list,
        description="Recommended questions for the patient to ask their doctor or pharmacist",
    )
    language: str = Field(..., description="Language of this explanation")
    disclaimer: str = Field(
        default=MANDATORY_PRESCRIPTION_DISCLAIMER,
        description="Mandatory medical and pharmaceutical disclaimer",
    )
