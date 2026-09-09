from typing import Literal

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("progress_percentage", mode="before")
    @classmethod
    def reject_boolean_progress_percentage(cls, value):
        if isinstance(value, bool):
            raise ValueError(
                "progress_percentage must be numeric, not boolean"
            )

        return value

    status: str | None = None

    issues: list[str] = Field(
        default_factory=list
    )

    delay_reason: str | None = None

    delay_duration_hours: float | None = None

    @field_validator("delay_duration_hours", mode="before")
    @classmethod
    def reject_boolean_delay_duration(cls, value):
        if isinstance(value, bool):
            return None

        return value

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

    @field_validator("delay_duration_hours", mode="before")
    @classmethod
    def reject_boolean_delay_duration(cls, value):
        if isinstance(value, bool):
            return None

        return value


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


ForecastStatus = Literal[
    "available",
    "insufficient_data",
    "unavailable",
]


ConfidenceAssessmentStatus = Literal[
    "assessed",
    "not_assessed",
    "not_applicable",
]

ConfidenceLevel = Literal[
    "low",
    "medium",
    "high",
]

VelocityStability = Literal[
    "not_assessable",
    "stable",
    "variable",
    "unstable",
]

DirectionConsistency = Literal[
    "positive",
    "mixed",
    "non_positive",
    "not_assessable",
]

DateQuality = Literal[
    "complete",
    "submission_order_fallback",
    "unusable",
]


class ForecastConfidence(BaseModel):
    """Deterministic quality assessment of forecast evidence."""

    assessment_status: ConfidenceAssessmentStatus

    level: ConfidenceLevel | None = None

    total_snapshot_count: int = Field(ge=0)

    usable_observation_count: int = Field(ge=0)

    missing_progress_count: int = Field(ge=0)

    interval_count: int = Field(ge=0)

    valid_velocity_interval_count: int = Field(ge=0)

    zero_day_gap_count: int = Field(ge=0)

    positive_interval_count: int = Field(ge=0)

    zero_interval_count: int = Field(ge=0)

    negative_interval_count: int = Field(ge=0)

    velocity_stability: VelocityStability

    direction_consistency: DirectionConsistency

    date_quality: DateQuality

    evidence: list[str] = Field(default_factory=list)

    data_note: str | None = None


PredictiveRiskLevel = Literal[
    "low",
    "medium",
    "high",
    "not_assessed",
    "not_applicable",
]


class PredictiveRisk(BaseModel):
    """Deterministic forward-looking trajectory assessment."""

    project_name: str

    activity_name: str

    level: PredictiveRiskLevel

    evidence: list[str] = Field(default_factory=list)

    data_note: str | None = None


DecisionSupportStatus = Literal[
    "supported",
    "review_only",
    "insufficient_evidence",
    "not_applicable",
]

DecisionSupportPriority = Literal[
    "none",
    "low",
    "medium",
    "high",
]

DecisionSupportResponse = Literal[
    "none",
    "monitor",
    "review",
    "investigate",
    "verify_data",
]

DecisionSupportTrigger = Literal[
    "observed_risk",
    "predictive_risk",
    "schedule_impact",
    "issue_evidence",
    "combined_evidence",
    "data_quality",
    "completion",
]


class DecisionSupport(BaseModel):
    """Deterministic, bounded attention guidance for one activity."""

    project_name: str

    activity_name: str

    status: DecisionSupportStatus

    priority: DecisionSupportPriority

    response: DecisionSupportResponse

    trigger: DecisionSupportTrigger

    evidence: list[str] = Field(default_factory=list)

    rationale: str

    limitations: list[str] = Field(default_factory=list)


class ForecastStatusDistribution(BaseModel):
    available: int = Field(default=0, ge=0)

    insufficient_data: int = Field(default=0, ge=0)

    unavailable: int = Field(default=0, ge=0)


class ConfidenceLevelDistribution(BaseModel):
    high: int = Field(default=0, ge=0)

    medium: int = Field(default=0, ge=0)

    low: int = Field(default=0, ge=0)

    not_assessed: int = Field(default=0, ge=0)

    not_applicable: int = Field(default=0, ge=0)


class PredictiveRiskDistribution(BaseModel):
    low: int = Field(default=0, ge=0)

    medium: int = Field(default=0, ge=0)

    high: int = Field(default=0, ge=0)

    not_assessed: int = Field(default=0, ge=0)

    not_applicable: int = Field(default=0, ge=0)


class DecisionSupportStatusDistribution(BaseModel):
    supported: int = Field(default=0, ge=0)

    review_only: int = Field(default=0, ge=0)

    insufficient_evidence: int = Field(default=0, ge=0)

    not_applicable: int = Field(default=0, ge=0)


class DecisionSupportPriorityDistribution(BaseModel):
    none: int = Field(default=0, ge=0)

    low: int = Field(default=0, ge=0)

    medium: int = Field(default=0, ge=0)

    high: int = Field(default=0, ge=0)


class ProjectPredictiveActivity(BaseModel):
    """Compact activity evidence reference used by a project summary."""

    activity_name: str

    forecast_status: ForecastStatus

    confidence_assessment_status: ConfidenceAssessmentStatus

    confidence_level: ConfidenceLevel | None = None

    predictive_risk_level: PredictiveRiskLevel

    decision_support_status: DecisionSupportStatus

    decision_support_priority: DecisionSupportPriority

    decision_support_response: DecisionSupportResponse

    decision_support_trigger: DecisionSupportTrigger

    limitations: list[str] = Field(default_factory=list)


class ProjectPredictiveSummary(BaseModel):
    """Deterministic aggregation of existing activity-level intelligence."""

    project_name: str

    total_activity_count: int = Field(ge=0)

    active_activity_count: int = Field(ge=0)

    completed_activity_count: int = Field(ge=0)

    forecast_status_distribution: ForecastStatusDistribution

    confidence_level_distribution: ConfidenceLevelDistribution

    predictive_risk_distribution: PredictiveRiskDistribution

    decision_support_status_distribution: DecisionSupportStatusDistribution

    decision_support_priority_distribution: DecisionSupportPriorityDistribution

    activities_requiring_attention: list[ProjectPredictiveActivity] = Field(
        default_factory=list
    )

    activities_with_insufficient_evidence: list[ProjectPredictiveActivity] = Field(
        default_factory=list
    )

    evidence_limitations: list[str] = Field(default_factory=list)


class ForecastResult(BaseModel):
    """Deterministic activity completion estimate from observed history."""

    project_name: str

    activity_name: str

    status: ForecastStatus

    current_progress: float | None = None

    remaining_progress: float | None = None

    historical_velocity_per_day: float | None = None

    estimated_days_to_completion: float | None = None

    estimated_completion_date: str | None = None

    observation_count: int = Field(ge=0)

    first_report_date: str | None = None

    latest_report_date: str | None = None

    forecast_method: str

    evidence: list[str] = Field(default_factory=list)

    data_note: str | None = None

    confidence: ForecastConfidence | None = None

    predictive_risk: PredictiveRisk | None = None


class ActivityPredictiveSummary(BaseModel):
    """Unified activity-level predictive product response."""

    project_name: str

    activity_name: str

    forecast: ForecastResult

    decision_support: DecisionSupport


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


class ActivityScheduleImpact(BaseModel):
    """Deterministic summary of explicitly reported delay observations."""

    project_name: str

    activity_name: str

    status: Literal[
        "available",
        "insufficient_data",
    ]

    delay_observation_count: int = Field(ge=0)

    repeated_delay_reasons: list[str] = Field(
        default_factory=list
    )

    latest_delay_hours: float | None = None

    latest_delay_reason: str | None = None

    progress_trend: TrendClassification

    summary: str


class ProjectScheduleImpact(BaseModel):
    """Activity-level observed schedule-impact results for one project."""

    project_name: str

    activities: list[ActivityScheduleImpact] = Field(
        default_factory=list
    )


class ScheduleImpactObservation(BaseModel):
    """One accepted observed delay record."""

    report_date: str | None = None

    delay_hours: float | None = None

    delay_reason: str | None = None

    submission_order: int = Field(ge=1)


class ActivityScheduleImpactHistory(BaseModel):
    """Accepted delay observations for one activity."""

    project_name: str

    activity_name: str

    observations: list[ScheduleImpactObservation] = Field(
        default_factory=list
    )


class ProjectScheduleImpactHistory(BaseModel):
    """Accepted schedule-impact observations for one project."""

    project_name: str

    activities: list[ActivityScheduleImpactHistory] = Field(
        default_factory=list
    )


class IssueObservation(BaseModel):
    """One accepted observed issue record."""

    report_date: str | None = None

    issue: str

    submission_order: int = Field(ge=1)


class ActivityIssueHistory(BaseModel):
    """Accepted issue observations for one activity."""

    project_name: str

    activity_name: str

    observations: list[IssueObservation] = Field(
        default_factory=list
    )


class ProjectIssueHistory(BaseModel):
    """Accepted issue observations for one project."""

    project_name: str

    activities: list[ActivityIssueHistory] = Field(
        default_factory=list
    )
