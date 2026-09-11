import type { DecisionSupport } from '../types/api'
import { EvidenceList } from './ForecastCard'
import { StatusBadge, toneFor } from './StatusBadge'

export function DecisionSupportCard({ decision }: { decision: DecisionSupport }) {
  return <section className="panel"><div className="panel-heading"><div><span className="eyebrow">Decision support</span><h2>Bounded attention guidance</h2></div><StatusBadge value={decision.status} tone={toneFor(decision.status)} /></div><div className="decision-summary"><div><span className="eyebrow">Priority</span><StatusBadge value={decision.priority} tone={toneFor(decision.priority)} /></div><div><span className="eyebrow">Response</span><StatusBadge value={decision.response} tone={toneFor(decision.response)} /></div><div><span className="eyebrow">Trigger</span><StatusBadge value={decision.trigger} /></div></div><p className="rationale">{decision.rationale}</p><EvidenceList title="Decision evidence" items={decision.evidence} />{decision.limitations.length > 0 && <div className="limitations"><h3>Limitations</h3><ul>{decision.limitations.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul></div>}<p className="muted support-note">This is bounded guidance for human review, not an autonomous action.</p></section>
}
