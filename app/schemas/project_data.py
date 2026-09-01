from typing import Literal

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


# ============================================================
# PROGRESS INTELLIGENCE (PHASE 2)
# ============================================================

TrendClassification = Literal[
    "improving",
    "stalled",
    "declining",
    "insufficient_data",
]


class ActivitySnapshot(BaseModel):
    """
    A point-in-time record of one activity from a single report.
    """

    report_date: str | None = None

    submission_order: int = Field(
        ge=1,
        description=(
            "Monotonic order of report ingestion when dates "
            "are missing or unparseable."
        ),
    )

    progress_percentage: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    quantity_completed: float | None = None

    unit: str | None = None

    status: str | None = None

    issues: list[str] = Field(
        default_factory=list
    )

    delay_reason: str | None = None

    delay_duration_hours: float | None = None


class ActivityHistory(BaseModel):
    """
    Chronological progress history for one activity within a project.
    """

    project_name: str

    activity_name: str

    snapshots: list[ActivitySnapshot] = Field(
        default_factory=list
    )


class TrendResult(BaseModel):
    """
    Deterministic trend analysis for one activity history.
    """

    project_name: str

    activity_name: str

    trend: TrendClassification

    snapshot_count: int = Field(ge=0)

    progress_deltas: list[float] = Field(
        default_factory=list
    )

    average_progress_delta: float | None = None

    average_velocity_per_day: float | None = None

    first_progress: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    last_progress: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )


RiskLevel = Literal[
    "low",
    "medium",
    "high",
    "insufficient_data",
]


class RiskResult(BaseModel):
    """
    Deterministic observed-risk assessment for one activity.

    The risk score is a rule-based signal score, not a probability and
    not a prediction of completion date.
    """

    project_name: str

    activity_name: str

    risk_level: RiskLevel

    risk_score: int = Field(
        ge=0,
        le=100,
        description="Rule-based observed-risk score, not a probability.",
    )

    risk_signals: list[str] = Field(
        default_factory=list
    )

    repeated_delays: list[str] = Field(
        default_factory=list
    )

    repeated_issues: list[str] = Field(
        default_factory=list
    )

    trend: TrendClassification

    average_velocity_per_day: float | None = None

    progress_deltas: list[float] = Field(
        default_factory=list
    )

    snapshot_count: int = Field(ge=0)


InsightStatus = Literal[
    "available",
    "insufficient_data",
]

InsightType = Literal[
    "declining_progress",
    "stalled_activity",
    "low_velocity",
    "repeated_delay",
    "repeated_issue",
]

InsightPriority = Literal[
    "low",
    "medium",
    "high",
]


class InsightFinding(BaseModel):
    """Deterministic explanation of one observed project signal."""

    finding_type: InsightType

    priority: InsightPriority

    title: str

    explanation: str

    factual_evidence: list[str] = Field(
        default_factory=list
    )

    recommendation: str | None = None


class ActivityInsight(BaseModel):
    """Human-readable deterministic insight for one activity."""

    project_name: str

    activity_name: str

    status: InsightStatus

    risk_level: RiskLevel

    risk_score: int = Field(
        ge=0,
        le=100,
    )

    trend: TrendClassification

    findings: list[InsightFinding] = Field(
        default_factory=list
    )

    data_note: str | None = None


class ProjectInsight(BaseModel):
    """Human-readable deterministic insights for one project."""

    project_name: str

    activities: list[ActivityInsight] = Field(
        default_factory=list
    )
