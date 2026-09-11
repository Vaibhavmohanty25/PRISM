export type ForecastStatus = 'available' | 'insufficient_data' | 'unavailable'
export type ConfidenceAssessmentStatus = 'assessed' | 'not_assessed' | 'not_applicable'
export type ConfidenceLevel = 'low' | 'medium' | 'high'
export type PredictiveRiskLevel = 'low' | 'medium' | 'high' | 'not_assessed' | 'not_applicable'
export type DecisionSupportStatus = 'supported' | 'review_only' | 'insufficient_evidence' | 'not_applicable'
export type DecisionSupportPriority = 'none' | 'low' | 'medium' | 'high'
export type DecisionSupportResponse = 'none' | 'monitor' | 'review' | 'investigate' | 'verify_data'
export type DecisionSupportTrigger = 'observed_risk' | 'predictive_risk' | 'schedule_impact' | 'issue_evidence' | 'combined_evidence' | 'data_quality' | 'completion'

export interface ActivitySnapshot {
  report_date: string | null
  submission_order: number
  progress_percentage: number | null
  quantity_completed: number | null
  unit: string | null
  status: string | null
  issues: string[]
  delay_reason: string | null
  delay_duration_hours: number | null
}

export interface ActivityHistory {
  project_name: string
  activity_name: string
  snapshots: ActivitySnapshot[]
}

export interface ForecastConfidence {
  assessment_status: ConfidenceAssessmentStatus
  level: ConfidenceLevel | null
  total_snapshot_count: number
  usable_observation_count: number
  missing_progress_count: number
  interval_count: number
  valid_velocity_interval_count: number
  zero_day_gap_count: number
  positive_interval_count: number
  zero_interval_count: number
  negative_interval_count: number
  velocity_stability: 'not_assessable' | 'stable' | 'variable' | 'unstable'
  direction_consistency: 'positive' | 'mixed' | 'non_positive' | 'not_assessable'
  date_quality: 'complete' | 'submission_order_fallback' | 'unusable'
  evidence: string[]
  data_note: string | null
}

export interface PredictiveRisk {
  project_name: string
  activity_name: string
  level: PredictiveRiskLevel
  evidence: string[]
  data_note: string | null
}

export interface ForecastResult {
  project_name: string
  activity_name: string
  status: ForecastStatus
  current_progress: number | null
  remaining_progress: number | null
  historical_velocity_per_day: number | null
  estimated_days_to_completion: number | null
  estimated_completion_date: string | null
  observation_count: number
  first_report_date: string | null
  latest_report_date: string | null
  forecast_method: string
  evidence: string[]
  data_note: string | null
  confidence: ForecastConfidence | null
  predictive_risk: PredictiveRisk | null
}

export interface DecisionSupport {
  project_name: string
  activity_name: string
  status: DecisionSupportStatus
  priority: DecisionSupportPriority
  response: DecisionSupportResponse
  trigger: DecisionSupportTrigger
  evidence: string[]
  rationale: string
  limitations: string[]
}

export interface ActivityPredictiveSummary {
  project_name: string
  activity_name: string
  forecast: ForecastResult
  decision_support: DecisionSupport
}

export interface ProjectPredictiveActivity {
  activity_name: string
  forecast_status: ForecastStatus
  confidence_assessment_status: ConfidenceAssessmentStatus
  confidence_level: ConfidenceLevel | null
  predictive_risk_level: PredictiveRiskLevel
  decision_support_status: DecisionSupportStatus
  decision_support_priority: DecisionSupportPriority
  decision_support_response: DecisionSupportResponse
  decision_support_trigger: DecisionSupportTrigger
  limitations: string[]
}

export interface ProjectPredictiveSummary {
  project_name: string
  total_activity_count: number
  active_activity_count: number
  completed_activity_count: number
  forecast_status_distribution: Record<ForecastStatus, number>
  confidence_level_distribution: Record<ConfidenceLevel | 'not_assessed' | 'not_applicable', number>
  predictive_risk_distribution: Record<PredictiveRiskLevel, number>
  decision_support_status_distribution: Record<DecisionSupportStatus, number>
  decision_support_priority_distribution: Record<DecisionSupportPriority, number>
  activities_requiring_attention: ProjectPredictiveActivity[]
  activities_with_insufficient_evidence: ProjectPredictiveActivity[]
  evidence_limitations: string[]
}

export interface UploadResponse {
  file_id: string
  original_filename: string
  stored_filename: string
  status: string
  processing_result: Record<string, unknown>
}

export interface ApiErrorPayload {
  error?: { code?: string; message?: string }
}
