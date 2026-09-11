import type { PredictiveRisk } from '../types/api'
import { EvidenceList } from './ForecastCard'
import { StatusBadge, toneFor } from './StatusBadge'

export function RiskCard({ risk }: { risk: PredictiveRisk | null }) {
  return <section className="panel"><div className="panel-heading"><div><span className="eyebrow">Predictive risk</span><h2>Forward-looking trajectory</h2></div><StatusBadge value={risk?.level ?? 'not_assessed'} tone={toneFor(risk?.level)} /></div>{risk ? <EvidenceList title="Risk evidence" items={risk.evidence} note={risk.data_note} /> : <p className="muted">Predictive risk was not assessed for this activity.</p>}</section>
}
