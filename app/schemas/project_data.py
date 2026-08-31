from pydantic import BaseModel, Field


# ============================================================
# EXTRACTION CONFIDENCE
# ============================================================

class ExtractionConfidence(BaseModel):
    """
    Confidence scores for extracted information.
    Values must be between 0 and 1.
    """

    overall: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0
    )

    metadata: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0
    )

    activities: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0
    )


# ============================================================
# EXTRACTION METADATA
# ============================================================

class ExtractionMetadata(BaseModel):
    """
    Metadata describing how the information was extracted.
    """

    source_type: str | None = None

    processing_method: str | None = None

    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0
    )


# ============================================================
# EXTRACTION EVIDENCE
# ============================================================

class ExtractionEvidence(BaseModel):
    """
    Original text supporting extracted activity fields.
    """

    progress: str | None = None

    quantity: str | None = None

    status: str | None = None

    delay: str | None = None


# ============================================================
# ACTIVITY PROGRESS
# ============================================================

class ActivityProgress(BaseModel):

    activity_name: str

    quantity_completed: float | None = None

    unit: str | None = None

    progress_percentage: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0
    )

    status: str | None = None

    issues: list[str] = Field(
        default_factory=list
    )

    delay_reason: str | None = None

    delay_duration_hours: float | None = None

    # Evidence from original document
    evidence: ExtractionEvidence | None = None

    # Confidence for extracted fields
    confidence: ExtractionConfidence | None = None


# ============================================================
# AI ACTIVITY EXTRACTION
# ============================================================

class AIActivityExtraction(BaseModel):

    activities: list[ActivityProgress] = Field(
        default_factory=list
    )

    general_issues: list[str] = Field(
        default_factory=list
    )


# ============================================================
# PROGRESS REPORT
# ============================================================

class ProgressReport(BaseModel):

    report_date: str | None = None

    project_name: str | None = None

    contractor: str | None = None

    location: str | None = None

    activities: list[ActivityProgress] = Field(
        default_factory=list
    )

    general_issues: list[str] = Field(
        default_factory=list
    )

    extraction_metadata: ExtractionMetadata | None = None