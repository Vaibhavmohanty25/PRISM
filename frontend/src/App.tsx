import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { ProjectsPage } from './pages/ProjectsPage'
import { ProjectDashboardPage } from './pages/ProjectDashboardPage'
import { ActivityDetailPage } from './pages/ActivityDetailPage'
import { ReportsPage } from './pages/ReportsPage'

export function App() { return <Routes><Route element={<AppShell />}><Route path="/" element={<Navigate to="/projects" replace />} /><Route path="/projects" element={<ProjectsPage />} /><Route path="/projects/:projectName" element={<ProjectDashboardPage />} /><Route path="/projects/:projectName/activities/:activityName" element={<ActivityDetailPage />} /><Route path="/reports" element={<ReportsPage />} /><Route path="*" element={<Navigate to="/projects" replace />} /></Route></Routes> }
