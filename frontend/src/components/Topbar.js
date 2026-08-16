import { NavLink } from 'react-router-dom';

const navItems = [
  {
    to: '/', label: 'Predict Risk', end: true,
    icon: <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>,
  },
  {
    to: '/history', label: 'History',
    icon: <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>,
  },
  {
    to: '/metrics', label: 'Model Metrics',
    icon: <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>,
  },
  {
    to: '/health', label: 'System Health',
    icon: <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" /></svg>,
  },
];

export default function Topbar({ healthStatus }) {
  const statusClass = healthStatus === 'ok' ? 'ok' : healthStatus ? 'error' : '';
  const statusText = healthStatus === 'ok' ? 'All Systems OK' : healthStatus ? 'Degraded' : 'Checking…';

  return (
    <header className="topbar">
      <NavLink to="/" className="brand">
        <div className="brand-mark" />
        <div>
          <span className="brand-name">SentryMed</span>
          <small className="brand-sub">Device Failure Intelligence</small>
        </div>
      </NavLink>

      <nav className="topnav">
        {navItems.map(({ to, label, icon, end }) => (
          <NavLink
            key={to} to={to} end={end}
            className={({ isActive }) => `topnav-item${isActive ? ' active' : ''}`}
          >
            {icon}<span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="topbar-right">
        <div className={`health-badge ${statusClass}`}>
          <span className="health-dot" />
          {statusText}
        </div>
      </div>
    </header>
  );
}
