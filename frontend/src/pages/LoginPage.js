import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getMfrAccounts } from '../services/api';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('user');
  const [mfrList, setMfrList] = useState([]);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);   // { username, manufacturer_id, name }
  const [showDrop, setShowDrop] = useState(false);
  const [password, setPassword] = useState('user123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const dropRef = useRef(null);

  useEffect(() => {
    getMfrAccounts()
      .then((r) => setMfrList(r.data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const handler = (e) => {
      if (dropRef.current && !dropRef.current.contains(e.target)) setShowDrop(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const filtered = search.trim()
    ? mfrList.filter((m) => m.name.toLowerCase().includes(search.toLowerCase())).slice(0, 60)
    : mfrList.slice(0, 200);

  const handleSelect = (m) => {
    setSelected(m);
    setSearch(m.name);
    setShowDrop(false);
  };

  const handleTabSwitch = (t) => {
    setTab(t);
    setPassword(t === 'user' ? 'user123' : 'mfr123');
    setError('');
    setSelected(null);
    setSearch('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (tab === 'manufacturer' && !selected) {
      setError('Please select a manufacturer from the list.');
      return;
    }
    setLoading(true); setError('');
    try {
      const username = tab === 'user' ? 'user' : selected.username;
      const role = await login(username, password);
      navigate(role === 'manufacturer' ? '/manufacturer' : '/');
    } catch {
      setError('Invalid credentials. Please try again.');
    } finally { setLoading(false); }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)' }}>
      <div style={{ width: '100%', maxWidth: '420px', padding: '0 16px' }}>

        {/* Brand */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'conic-gradient(from 210deg, var(--teal), var(--blue), var(--teal))', margin: '0 auto 12px' }} />
          <div style={{ fontSize: '22px', fontWeight: 700 }}>SentryMed</div>
          <div style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '4px' }}>Medical Device Risk Intelligence</div>
        </div>

        <div className="panel">
          {/* Tab switcher */}
          <div style={{ display: 'flex', background: 'var(--panel-2)', borderRadius: '8px', padding: '3px', marginBottom: '22px' }}>
            {['user', 'manufacturer'].map((t) => (
              <button key={t} onClick={() => handleTabSwitch(t)} style={{
                flex: 1, padding: '7px', border: 'none', borderRadius: '6px', cursor: 'pointer',
                fontFamily: 'inherit', fontSize: '13px', fontWeight: 600, transition: 'all 0.15s',
                background: tab === t ? 'var(--panel)' : 'transparent',
                color: tab === t ? 'var(--text)' : 'var(--muted)',
                boxShadow: tab === t ? 'var(--shadow)' : 'none',
              }}>
                {t === 'user' ? '👤 Technician' : '🏭 Manufacturer'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit}>
            {tab === 'manufacturer' ? (
              <div className="form-group">
                <label className="form-label">Manufacturer Name</label>
                <div className="autocomplete-wrap" ref={dropRef}>
                  <input
                    className="form-input"
                    placeholder="Search manufacturer..."
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setSelected(null); setShowDrop(true); }}
                    onFocus={() => setShowDrop(true)}
                    autoComplete="off"
                  />
                  {showDrop && filtered.length > 0 && (
                    <div className="autocomplete-list" style={{ maxHeight: '220px' }}>
                      {filtered.map((m) => (
                        <div key={m.username} className="autocomplete-item"
                          onMouseDown={() => handleSelect(m)}>
                          <span style={{ fontWeight: 500 }}>{m.name}</span>
                          <span style={{ color: 'var(--muted)', fontSize: '11px', marginLeft: '6px' }}>
                            #{m.manufacturer_id}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '4px' }}>
                  {selected
                    ? <span style={{ color: 'var(--teal)' }}>Selected: {selected.name}</span>
                    : 'Type to search from registered manufacturers'}
                </div>
              </div>
            ) : (
              <div className="form-group">
                <label className="form-label">Username</label>
                <input className="form-input" value="user" readOnly style={{ color: 'var(--muted)' }} />
                <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '4px' }}>
                  Demo technician account
                </div>
              </div>
            )}

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                className="form-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '4px' }}>
                {tab === 'user' ? 'Demo password: user123' : 'Demo password: mfr123'}
              </div>
            </div>

            {error && <div className="error-box" style={{ marginBottom: '12px' }}>⚠ {error}</div>}

            <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
              {loading ? <><span className="spinner" /> Signing in…</> : 'Sign In'}
            </button>
          </form>
        </div>

        <div style={{ textAlign: 'center', marginTop: '20px', fontSize: '11px', color: 'var(--muted)' }}>
          Cognizant NPN AI Hackathon · SentryMed
        </div>
      </div>
    </div>
  );
}
