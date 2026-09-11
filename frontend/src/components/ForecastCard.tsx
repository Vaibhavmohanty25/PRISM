import type { ForecastResult } from '../types/api'
import { StatusBadge, toneFor } from './StatusBadge'

export function ForecastCard({ forecast }: { forecast: ForecastResult }) {
  const unavailable = forecast.status !== 'available'
  return <section className="panel forecast-card">
    <div className="panel-heading"><div><span className="eyebrow">Forecast</span><h2>Deterministic completion outlook</h2></div><StatusBadge value={forecast.status} tone={toneFor(forecast.status)} /></div>
    {unavailable ? <div className="callout"><strong>{forecast.status === 'insufficient_data' ? 'Insufficient historical evidence' : 'Forecast unavailable'}</strong><p>{forecast.data_note ?? (forecast.status === 'insufficient_data' ? 'More usable progress observations are needed before a deterministic forecast can be calculated.' : 'A meaningful deterministic forecast could not be calculated from the available history.')}</p></div> : <div className="forecast-grid">
      <div><span className="eyebrow">Current progress</span><strong>{forecast.current_progress ?? '—'}{forecast.current_progress === null ? '' : '%'}</strong></div>
      <div><span className="eyebrow">Remaining progress</span><strong>{forecast.remaining_progress ?? '—'}{forecast.remaining_progress === null ? '' : '%'}</strong></div>
      <div><span className="eyebrow">Historical velocity</span><strong>{forecast.historical_velocity_per_day ?? '—'}<small> % / day</small></strong></div>
      <div><span className="eyebrow">Estimated completion</span><strong>{forecast.estimated_completion_date ?? '—'}</strong><span>{forecast.estimated_days_to_completion === null ? 'No duration returned' : `${forecast.estimated_days_to_completion} days remaining`}</span></div>
    </div>}
    <div className="detail-strip"><span>{forecast.observation_count} observations</span><span>{forecast.first_report_date ?? 'No first report date'} → {forecast.latest_report_date ?? 'No latest report date'}</span><span>Method: {forecast.forecast_method}</span></div>
    <EvidenceList title="Forecast evidence" items={forecast.evidence} note={forecast.data_note} />
  </section>
}

export function EvidenceList({ title, items, note }: { title: string; items: string[]; note?: string | null }) {
  return <div className="evidence"><h3>{title}</h3>{items.length ? <ul>{items.map((item, index) => <li key={`${item}-${index}`}>{item}</li>)}</ul> : <p className="muted">No evidence notes were returned.</p>}{note && <p className="data-note">{note}</p>}</div>
}
