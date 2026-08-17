import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const userNavItems = [
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

const mfrNavItems = [
  {
    to: '/manufacturer', label: 'Dashboard', end: true,
    icon: <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" /></svg>,
  },
];

export default function Topbar({ healthStatus }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const statusClass = healthStatus === 'ok' ? 'ok' : healthStatus ? 'error' : '';
  const statusText = healthStatus === 'ok' ? 'All Systems OK' : healthStatus ? 'Degraded' : 'Checking…';
  const navItems = user?.role === 'manufacturer' ? mfrNavItems : userNavItems;

  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <header className="topbar">
      <NavLink to={user?.role === 'manufacturer' ? '/manufacturer' : '/'} className="brand">
        <div className="brand-mark" />
        <div>
          <span className="brand-name">SentryMed</span>
          <small className="brand-sub">Failure Risk Intelligence</small>
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
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '12px', color: 'var(--muted)', fontWeight: 500 }}>
              {user.role === 'manufacturer'
                ? (user.manufacturer_name?.slice(0, 22) || user.username)
                : user.username}
            </span>
            <button onClick={handleLogout} className="btn btn-secondary" style={{ padding: '5px 12px', fontSize: '12px' }}>
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
