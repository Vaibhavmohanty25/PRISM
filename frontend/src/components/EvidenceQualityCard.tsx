import type { ForecastConfidence } from '../types/api'
import { EvidenceList } from './ForecastCard'
import { StatusBadge, toneFor } from './StatusBadge'

export function EvidenceQualityCard({ confidence }: { confidence: ForecastConfidence | null }) {
  if (!confidence) return <section className="panel"><div className="panel-heading"><div><span className="eyebrow">Evidence quality</span><h2>Forecast support</h2></div><StatusBadge value="not_applicable" /></div><p className="muted">Evidence quality was not returned for this activity.</p></section>
  return <section className="panel"><div className="panel-heading"><div><span className="eyebrow">Evidence quality</span><h2>Support for the forecast</h2></div><StatusBadge value={confidence.level ?? confidence.assessment_status} tone={toneFor(confidence.level ?? confidence.assessment_status)} /></div>
    <p className="explainer">Evidence quality supporting the forecast — not a probability that the forecast is correct.</p>
    <div className="evidence-stats">{[['Usable observations', confidence.usable_observation_count], ['Missing progress', confidence.missing_progress_count], ['Intervals', confidence.interval_count], ['Valid velocity intervals', confidence.valid_velocity_interval_count], ['Zero-day gaps', confidence.zero_day_gap_count], ['Positive intervals', confidence.positive_interval_count], ['Zero intervals', confidence.zero_interval_count], ['Negative intervals', confidence.negative_interval_count]].map(([label, value]) => <div key={String(label)}><span>{label}</span><strong>{value}</strong></div>)}</div>
    <div className="attribute-grid"><div><span>Velocity stability</span><StatusBadge value={confidence.velocity_stability} tone={toneFor(confidence.velocity_stability)} /></div><div><span>Direction consistency</span><StatusBadge value={confidence.direction_consistency} /></div><div><span>Date quality</span><StatusBadge value={confidence.date_quality} /></div></div>
    <EvidenceList title="Evidence notes" items={confidence.evidence} note={confidence.data_note} />
  </section>
}
