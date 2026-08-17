import { useState, useEffect, useCallback } from 'react';
import { getMfrDashboard, getMfrDevices, getMfrAlerts, markAlertRead } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

function StatCard({ label, value, color, delta }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className={`stat-value mono ${color || ''}`}>{value}</div>
      {delta && <div className="stat-delta">{delta}</div>}
    </div>
  );
}

function ClassificationBar({ name, count, max }) {
  const pct = max > 0 ? (count / max) * 100 : 0;
  return (
    <div style={{ marginBottom: '10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
        <span style={{ color: 'var(--text)', fontWeight: 500 }}>{name}</span>
        <span className="mono" style={{ color: 'var(--muted)', fontSize: '11px' }}>{count}</span>
      </div>
      <div className="conf-track">
        <div className="conf-fill" style={{ width: `${pct}%`, background: 'var(--teal)' }} />
      </div>
    </div>
  );
}

export default function MfrDashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [devices, setDevices] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [devSearch, setDevSearch] = useState('');
  const [activeTab, setActiveTab] = useState('devices');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const [dashRes, devRes, alertRes] = await Promise.all([
        getMfrDashboard(),
        getMfrDevices(0, 50),
        getMfrAlerts(0, 50),
      ]);
      setStats(dashRes.data);
      setDevices(devRes.data);
      setAlerts(alertRes.data);
    } catch (e) {
      console.error(e);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSearch = async (q) => {
    setDevSearch(q);
    try {
      const res = await getMfrDevices(0, 50, q);
      setDevices(res.data);
    } catch { }
  };

  const handleMarkRead = async (id) => {
    await markAlertRead(id);
    setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, status: 'read' } : a));
    setStats((prev) => prev ? { ...prev, unread_alerts: Math.max(0, prev.unread_alerts - 1) } : prev);
  };

  if (loading) return <div className="spinner-center"><div className="spinner spinner-lg" /></div>;

  const maxClf = stats?.classification_breakdown?.[0]?.count || 1;
  const unreadAlerts = alerts.filter((a) => a.status === 'unread');

  return (
    <div className="wrap">
      <div className="headline">
        <div>
          <h1>Manufacturer Dashboard</h1>
          <p>{user?.manufacturer_name || `Manufacturer #${user?.manufacturer_id}`} · Device portfolio overview</p>
        </div>
      </div>

      {/* Stat cards */}
      {stats && (
        <div className="stats">
          <StatCard label="Total Devices" value={stats.total_devices} color="teal" delta="in USA dataset" />
          <StatCard label="Total Events" value={stats.total_events.toLocaleString()} color="" delta="recalls & safety notices" />
          <StatCard label="Countries Active" value={stats.countries_active} color="blue" delta="markets with events" />
          <StatCard label="Unread Alerts" value={stats.unread_alerts} color={stats.unread_alerts > 0 ? 'red' : 'teal'} delta="from technician checks" />
        </div>
      )}

      <div className="grid-main">
        {/* Left: Devices + Alerts tabs */}
        <div className="panel">
          {/* Tab bar */}
          <div style={{ display: 'flex', gap: '4px', marginBottom: '16px' }}>
            {['devices', 'alerts'].map((t) => (
              <button key={t} onClick={() => setActiveTab(t)}
                className={`topnav-item${activeTab === t ? ' active' : ''}`}
                style={{ fontSize: '13px' }}>
                {t === 'devices' ? `Devices (${stats?.total_devices ?? '—'})` : `Alerts (${alerts.length})`}
                {t === 'alerts' && unreadAlerts.length > 0 && (
                  <span style={{ background: 'var(--red)', color: '#fff', borderRadius: '10px', fontSize: '10px', padding: '1px 6px', marginLeft: '4px' }}>
                    {unreadAlerts.length}
                  </span>
                )}
              </button>
            ))}
          </div>

          {activeTab === 'devices' && (
            <>
              <input
                className="form-input"
                placeholder="Search devices..."
                value={devSearch}
                onChange={(e) => handleSearch(e.target.value)}
                style={{ marginBottom: '12px' }}
              />
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Device</th>
                      <th>Classification</th>
                      <th>Country</th>
                    </tr>
                  </thead>
                  <tbody>
                    {devices.length === 0 && (
                      <tr><td colSpan={3} style={{ textAlign: 'center', color: 'var(--muted)', padding: '24px' }}>No devices found</td></tr>
                    )}
                    {devices.map((d) => (
                      <tr key={d.id}>
                        <td>
                          <div className="dev-name" style={{ fontSize: '12px' }}>{d.name?.slice(0, 55) || '—'}{d.name?.length > 55 ? '…' : ''}</div>
                          <div className="dev-id">#{d.id}</div>
                        </td>
                        <td style={{ fontSize: '11px', color: 'var(--muted)' }}>{d.classification || '—'}</td>
                        <td style={{ fontSize: '11px', color: 'var(--muted)' }}>{d.country || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {activeTab === 'alerts' && (
            <div>
              {alerts.length === 0 && (
                <div className="empty">
                  <p>No alerts yet. Alerts appear when a technician flags one of your devices as high risk.</p>
                </div>
              )}
              {alerts.map((a) => (
                <div key={a.id} style={{
                  padding: '12px 14px', borderRadius: '8px', marginBottom: '8px',
                  background: a.status === 'unread' ? 'rgba(214,69,90,0.05)' : 'var(--panel-2)',
                  border: `1px solid ${a.status === 'unread' ? 'rgba(214,69,90,0.25)' : 'var(--line)'}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '13px' }}>
                        {a.status === 'unread' && <span style={{ color: 'var(--red)', marginRight: '6px' }}>●</span>}
                        {a.device_name?.slice(0, 50) || `Device #${a.device_id}`}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '3px' }}>
                        P(failure) = <span className="mono" style={{ color: 'var(--red)', fontWeight: 600 }}>{(a.prob_failure * 100).toFixed(1)}%</span>
                        &nbsp;· Flagged by <span className="mono">{a.triggered_by}</span>
                        &nbsp;· {new Date(a.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    {a.status === 'unread' && (
                      <button className="btn btn-secondary" style={{ fontSize: '11px', padding: '4px 10px' }}
                        onClick={() => handleMarkRead(a.id)}>
                        Mark read
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Classification breakdown */}
        <div className="panel">
          <div className="panel-title">Device Classification Breakdown</div>
          <div className="panel-sub">Distribution of your devices across FDA categories</div>

          {stats?.classification_breakdown?.map((row) => (
            <ClassificationBar key={row.classification} name={row.classification} count={row.count} max={maxClf} />
          ))}

          <div className="divider" />
          <div className="panel-title" style={{ marginBottom: '12px' }}>Portfolio Summary</div>
          {stats && [
            { label: 'Total Devices', value: stats.total_devices },
            { label: 'Total Events (Recalls)', value: stats.total_events.toLocaleString() },
            { label: 'Countries Active', value: stats.countries_active },
            { label: 'Unread Alerts', value: stats.unread_alerts },
            { label: 'Classifications', value: stats.classification_breakdown.length },
          ].map(({ label, value }) => (
            <div className="factor" key={label}>
              <span className="factor-name" style={{ color: 'var(--muted)', fontSize: '12px' }}>{label}</span>
              <span className="mono" style={{ fontSize: '13px', fontWeight: 600 }}>{value}</span>
            </div>
          ))}

          <div className="divider" />
          <div style={{ padding: '12px', background: 'var(--panel-2)', borderRadius: '8px', border: '1px solid var(--line)' }}>
            <div style={{ fontSize: '11px', color: 'var(--muted)', lineHeight: 1.6 }}>
              <strong style={{ color: 'var(--text)' }}>Alert System</strong><br />
              Alerts are automatically created when a technician runs a prediction on one of your devices and the model returns P(failure) &ge; 0.42.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
