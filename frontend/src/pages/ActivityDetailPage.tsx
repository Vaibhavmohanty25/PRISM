import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { prismApi } from '../lib/api'
import type { ActivityHistory, ActivityPredictiveSummary } from '../types/api'
import { StatePanel } from '../components/StatePanel'
import { SectionHeader } from '../components/SectionHeader'
import { ForecastCard } from '../components/ForecastCard'
import { EvidenceQualityCard } from '../components/EvidenceQualityCard'
import { RiskCard } from '../components/RiskCard'
import { DecisionSupportCard } from '../components/DecisionSupportCard'
import { ProgressHistory } from '../components/ProgressHistory'

export function ActivityDetailPage() {
  const { projectName = '', activityName = '' } = useParams()
  const project = decodeURIComponent(projectName), activity = decodeURIComponent(activityName)
  const [data, setData] = useState<{ summary: ActivityPredictiveSummary; history: ActivityHistory } | null>(null)
  const [error, setError] = useState<Error | null>(null)
  useEffect(() => { setData(null); setError(null); Promise.all([prismApi.getActivityPredictiveSummary(project, activity), prismApi.getActivityHistory(project, activity)]).then(([summary, history]) => setData({ summary, history })).catch(setError) }, [project, activity])
  if (error) return <div className="page"><StatePanel kind="error" title="Activity not found" message="That activity is not available for this project in the current PRISM session." action={<Link className="button secondary" to={`/projects/${encodeURIComponent(project)}`}>Back to project</Link>} /></div>
  if (!data) return <div className="page"><StatePanel kind="loading" title="Loading activity intelligence" message="Gathering observed history and predictive evidence…" /></div>
  return <div className="page"><SectionHeader eyebrow="Activity detail" title={data.summary.activity_name} description={<><Link className="breadcrumb-link" to={`/projects/${encodeURIComponent(project)}`}>{data.summary.project_name}</Link> · Current activity intelligence</>} /><div className="detail-grid"><ForecastCard forecast={data.summary.forecast} /><ProgressHistory history={data.history} /><EvidenceQualityCard confidence={data.summary.forecast.confidence} /><RiskCard risk={data.summary.forecast.predictive_risk} /><DecisionSupportCard decision={data.summary.decision_support} /></div></div>
}
