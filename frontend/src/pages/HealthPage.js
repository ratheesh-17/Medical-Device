import { useState, useEffect, useCallback } from 'react';
import { getHealth } from '../services/api';

const services = [
  { key: 'db',       label: 'MySQL Database', icon: '🗄️',  okVal: 'ok' },
  { key: 'model',    label: 'ML Model',        icon: '🤖',  okVal: 'loaded' },
  { key: 'pipeline', label: 'Preprocessor',    icon: '⚙️',  okVal: 'loaded' },
];

export default function HealthPage({ onStatus }) {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState(null);

  const check = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getHealth();
      setHealth(res.data);
      onStatus?.(res.data.status);
    } catch {
      setHealth({ status: 'error', db: 'error', model: 'error', pipeline: 'error', service: 'MedDevice Risk Predictor API' });
      onStatus?.('error');
    }
    setLastChecked(new Date());
    setLoading(false);
  }, [onStatus]);

  useEffect(() => { check(); }, [check]);

  const isOk = (key, val) => val === services.find((s) => s.key === key)?.okVal;

  return (
    <div className="wrap">
      <div className="headline">
        <div>
          <h1>System Health</h1>
          <p>Live status of all backend services · {lastChecked ? `Last checked ${lastChecked.toLocaleTimeString()}` : 'Checking…'}</p>
        </div>
        <button className="btn btn-secondary" onClick={check} disabled={loading}>
          {loading ? <><span className="spinner" /> Checking…</> : '↻ Refresh'}
        </button>
      </div>

      {health && (
        <>
          {/* Overall banner */}
          <div className="panel" style={{
            marginBottom: '20px',
            borderColor: health.status === 'ok' ? 'rgba(15,156,140,0.35)' : 'rgba(214,69,90,0.35)',
            background: health.status === 'ok' ? 'rgba(15,156,140,0.04)' : 'rgba(214,69,90,0.04)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <span style={{ fontSize: '30px' }}>{health.status === 'ok' ? '✅' : '❌'}</span>
              <div>
                <div style={{ fontWeight: 700, fontSize: '15px', color: health.status === 'ok' ? 'var(--teal)' : 'var(--red)' }}>
                  {health.status === 'ok' ? 'All Systems Operational' : 'System Degraded'}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '2px' }}>
                  {health.service || 'MedDevice Risk Predictor API'}
                </div>
              </div>
            </div>
          </div>

          {/* Service cards */}
          <div className="grid-3" style={{ marginBottom: '20px' }}>
            {services.map(({ key, label, icon }) => {
              const val = health[key];
              const ok = isOk(key, val);
              return (
                <div className="panel health-item" key={key}>
                  <span className="health-icon">{icon}</span>
                  <span className="health-label">{label}</span>
                  <span className={`health-val ${ok ? 'ok' : 'error'}`}>
                    {ok ? '● Online' : `● ${val}`}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Raw JSON */}
          <div className="panel">
            <div className="panel-title">Raw API Response</div>
            <div className="panel-sub">GET /api/v1/health</div>
            <pre style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '12px', color: 'var(--muted)', lineHeight: 1.7, overflowX: 'auto', background: 'var(--panel-2)', padding: '14px', borderRadius: '8px', border: '1px solid var(--line)' }}>
              {JSON.stringify(health, null, 2)}
            </pre>
          </div>
        </>
      )}
    </div>
  );
}
