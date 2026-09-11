import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { prismApi } from '../lib/api'
import type { ProjectPredictiveActivity, ProjectPredictiveSummary } from '../types/api'
import { MetricCard } from '../components/MetricCard'
import { SectionHeader } from '../components/SectionHeader'
import { StatePanel } from '../components/StatePanel'
import { StatusBadge, toneFor } from '../components/StatusBadge'

const filters = [
  ['all', 'All activities'], ['high', 'High predictive risk'], ['medium', 'Medium predictive risk'], ['low', 'Low predictive risk'], ['review', 'Needs review'], ['investigate', 'Needs investigation'], ['insufficient', 'Insufficient evidence'],
] as const

function activityMatches(activity: ProjectPredictiveActivity, filter: string) {
  if (filter === 'all') return true
  if (filter === 'insufficient') return activity.forecast_status === 'insufficient_data' || activity.decision_support_status === 'insufficient_evidence'
  if (filter === 'review') return activity.decision_support_response === 'review'
  return activity.predictive_risk_level === filter || activity.decision_support_response === filter
}

export function ProjectDashboardPage() {
  const { projectName = '' } = useParams()
  const project = decodeURIComponent(projectName)
  const [summary, setSummary] = useState<ProjectPredictiveSummary | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [filter, setFilter] = useState('all')
  useEffect(() => { setSummary(null); setError(null); prismApi.getProjectPredictiveSummary(project).then(setSummary).catch(setError) }, [project])
  const activities = useMemo(() => summary ? [...summary.activities_requiring_attention, ...summary.activities_with_insufficient_evidence].filter((activity, index, all) => all.findIndex(item => item.activity_name === activity.activity_name) === index).filter(activity => activityMatches(activity, filter)) : [], [summary, filter])
  if (error) return <div className="page"><StatePanel kind="error" title="Project not found" message="That project is not available in the current PRISM session." action={<Link className="button secondary" to="/projects">Back to projects</Link>} /></div>
  if (!summary) return <div className="page"><StatePanel kind="loading" title="Loading project intelligence" message="Gathering the latest predictive summary…" /></div>
  return <div className="page">
    <SectionHeader eyebrow="Project dashboard" title={summary.project_name} description="A clear separation of observed evidence, forecast, evidence quality, predictive risk, and decision support." action={<Link className="button secondary" to="/reports">Upload report</Link>} />
    <div className="metric-grid"><MetricCard label="Total activities" value={summary.total_activity_count} /><MetricCard label="Active activities" value={summary.active_activity_count} /><MetricCard label="Completed activities" value={summary.completed_activity_count} /><MetricCard label="Forecast available" value={summary.forecast_status_distribution.available} detail={`${summary.forecast_status_distribution.insufficient_data} insufficient · ${summary.forecast_status_distribution.unavailable} unavailable`} /></div>
    <div className="dashboard-grid"><section className="panel distribution-panel"><div className="panel-heading"><div><span className="eyebrow">Predictive overview</span><h2>Signal distribution</h2></div><span className="muted">Backend summary</span></div><Distribution label="Forecast" values={summary.forecast_status_distribution} /><Distribution label="Confidence" values={summary.confidence_level_distribution} /><Distribution label="Predictive risk" values={summary.predictive_risk_distribution} /><Distribution label="Decision priority" values={summary.decision_support_priority_distribution} /></section><section className="panel attention-panel"><div className="panel-heading"><div><span className="eyebrow">Attention</span><h2>Activities requiring attention</h2></div><span className="count-pill">{summary.activities_requiring_attention.length}</span></div>{summary.activities_requiring_attention.length === 0 ? <p className="muted">No activities were returned in the attention list.</p> : <div className="attention-list">{summary.activities_requiring_attention.map(activity => <ActivityListItem key={activity.activity_name} activity={activity} project={project} />)}</div>}</section></div>
    <section className="panel activity-panel"><div className="panel-heading"><div><span className="eyebrow">Activities</span><h2>Project activity list</h2></div><label className="filter-label">Filter<select value={filter} onChange={event => setFilter(event.target.value)}>{filters.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label></div><div className="table-wrap"><table><thead><tr><th>Activity</th><th>Forecast</th><th>Evidence</th><th>Predictive risk</th><th>Decision priority</th><th>Response</th></tr></thead><tbody>{activities.length ? activities.map(activity => <ActivityRow key={activity.activity_name} activity={activity} project={project} />) : <tr><td colSpan={6}><p className="table-empty">No activities match this filter.</p></td></tr>}</tbody></table></div></section>
    {summary.activities_with_insufficient_evidence.length > 0 && <section className="panel insufficient-panel"><div className="panel-heading"><div><span className="eyebrow">Evidence boundary</span><h2>Insufficient evidence</h2></div></div><p className="callout-text"><strong>Insufficient evidence does not mean the activity is healthy.</strong> It means the available history did not support the backend assessment.</p><div className="insufficient-list">{summary.activities_with_insufficient_evidence.map(activity => <ActivityListItem key={activity.activity_name} activity={activity} project={project} />)}</div></section>}
  </div>
}

function Distribution({ label, values }: { label: string; values: Record<string, number> }) { return <div className="distribution"><div><strong>{label}</strong><span>{Object.values(values).reduce((sum, value) => sum + value, 0)} activities</span></div><div className="distribution-items">{Object.entries(values).map(([key, value]) => <span key={key}><i className={`dot dot-${key}`} />{key.replaceAll('_', ' ')} <strong>{value}</strong></span>)}</div></div> }
function ActivityListItem({ activity, project }: { activity: ProjectPredictiveActivity; project: string }) { return <Link className="attention-item" to={`/projects/${encodeURIComponent(project)}/activities/${encodeURIComponent(activity.activity_name)}`}><div><strong>{activity.activity_name}</strong><span><StatusBadge value={activity.predictive_risk_level} tone={toneFor(activity.predictive_risk_level)} /><StatusBadge value={activity.decision_support_priority} tone={toneFor(activity.decision_support_priority)} /></span></div><span className="arrow">→</span></Link> }
function ActivityRow({ activity, project }: { activity: ProjectPredictiveActivity; project: string }) { return <tr><td><Link className="table-link" to={`/projects/${encodeURIComponent(project)}/activities/${encodeURIComponent(activity.activity_name)}`}>{activity.activity_name}</Link></td><td><StatusBadge value={activity.forecast_status} tone={toneFor(activity.forecast_status)} /></td><td><StatusBadge value={activity.confidence_level ?? activity.confidence_assessment_status} tone={toneFor(activity.confidence_level)} /></td><td><StatusBadge value={activity.predictive_risk_level} tone={toneFor(activity.predictive_risk_level)} /></td><td><StatusBadge value={activity.decision_support_priority} tone={toneFor(activity.decision_support_priority)} /></td><td><StatusBadge value={activity.decision_support_response} tone={toneFor(activity.decision_support_response)} /></td></tr> }
