import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'

export function AppShell() {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  useEffect(() => setOpen(false), [location.pathname])
  return <div className="app-shell">
    <button className="mobile-menu" onClick={() => setOpen(!open)} aria-label="Toggle navigation">☰</button>
    <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
      <div className="brand"><span className="brand-mark">P</span><div><strong>PRISM</strong><small>Project intelligence</small></div></div>
      <nav aria-label="Primary navigation">
        <NavLink to="/projects" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>▦ <span>Projects</span></NavLink>
        <NavLink to="/reports" className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>↥ <span>Reports</span></NavLink>
      </nav>
      <div className="sidebar-footer"><span className="live-dot" /> Backend connected via API</div>
    </aside>
    <main className="main-content"><Outlet /></main>
  </div>
}
