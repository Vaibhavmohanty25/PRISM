import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { prismApi } from '../lib/api'
import { StatePanel } from '../components/StatePanel'
import { SectionHeader } from '../components/SectionHeader'

export function ProjectsPage() {
  const [projects, setProjects] = useState<string[] | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const navigate = useNavigate()
  useEffect(() => { prismApi.getProjects().then(setProjects).catch(setError) }, [])
  return <div className="page"><SectionHeader eyebrow="Workspace" title="Projects" description="Select a project to review observed evidence, deterministic forecasts, and bounded decision support." />
    {error ? <StatePanel kind="error" title="Projects could not be loaded" message={error.message} action={<button className="button secondary" onClick={() => window.location.reload()}>Retry</button>} /> : projects === null ? <StatePanel kind="loading" title="Loading projects" message="Connecting to the PRISM analysis service…" /> : projects.length === 0 ? <StatePanel kind="empty" title="No projects yet" message="Upload a construction progress report to start building project intelligence." action={<button className="button" onClick={() => navigate('/reports')}>Upload a report</button>} /> : <div className="project-grid">{projects.map(project => <Link className="project-card" to={`/projects/${encodeURIComponent(project)}`} key={project}><span className="project-card-icon">P</span><div><h2>{project}</h2><p>Open project intelligence</p></div><span className="arrow">→</span></Link>)}</div>}
  </div>
}
