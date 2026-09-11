import type { ActivityHistory } from '../types/api'

export function ProgressHistory({ history }: { history: ActivityHistory }) {
  const plotted = history.snapshots.filter(snapshot => snapshot.progress_percentage !== null)
  return <section className="panel history-panel">
    <div className="panel-heading"><div><span className="eyebrow">Observed evidence</span><h2>Progress over time</h2></div><span className="muted">{plotted.length} usable observations</span></div>
    {plotted.length === 0 ? <p className="muted">No progress percentages were recorded in the available reports.</p> : <>
      <div className="history-chart" aria-label="Progress over time chart">
        {plotted.map((snapshot, index) => <div className="history-point" key={`${snapshot.submission_order}-${index}`} style={{ left: `${plotted.length === 1 ? 50 : (index / (plotted.length - 1)) * 100}%`, bottom: `${snapshot.progress_percentage}%` }}><span>{snapshot.progress_percentage}%</span><i /></div>)}
        <div className="chart-axis"><span>Earlier reports</span><span>Latest report</span></div>
      </div>
      <div className="history-list">{history.snapshots.map(snapshot => <div className="history-row" key={snapshot.submission_order}><span>{snapshot.report_date ?? `Report ${snapshot.submission_order}`}</span><strong>{snapshot.progress_percentage === null ? 'Not recorded' : `${snapshot.progress_percentage}%`}</strong><span>{snapshot.status ?? 'Status not recorded'}</span></div>)}</div>
    </>}
  </section>
}
