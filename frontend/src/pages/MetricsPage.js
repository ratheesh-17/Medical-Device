import { useState, useEffect } from 'react';
import { getMetrics } from '../services/api';

function Gauge({ value, label, color }) {
  const pct = Math.round(value * 100);
  const r = 36, circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  return (
    <div className="gauge-wrap">
      <div className="gauge-ring">
        <svg width="90" height="90" viewBox="0 0 90 90">
          <circle cx="45" cy="45" r={r} fill="none" stroke="var(--line)" strokeWidth="7" />
          <circle cx="45" cy="45" r={r} fill="none" stroke={color} strokeWidth="7"
            strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" />
        </svg>
        <div className="gauge-text">
          <span className="gauge-pct" style={{ color }}>{pct}%</span>
          <span className="gauge-lbl">F1</span>
        </div>
      </div>
      <span style={{ fontSize: '11px', color: 'var(--muted)', fontWeight: 600 }}>{label}</span>
    </div>
  );
}

const CLASS_COLOR = { I: 'var(--red)', II: 'var(--amber)', III: 'var(--teal)' };
const CLASS_PILL  = { I: 'high', II: 'med', III: 'low' };

export default function MetricsPage() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getMetrics()
      .then((r) => setMetrics(r.data))
      .catch(() => setError('Failed to load metrics. Is the backend running?'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="wrap"><div className="spinner-center"><div className="spinner spinner-lg" /></div></div>;
  if (error) return <div className="wrap"><div className="empty"><p style={{ color: 'var(--red)' }}>{error}</p></div></div>;
  if (!metrics) return null;

  const weights = metrics.class_weights || {};
  const maxWeight = Math.max(...Object.values(weights).map(Number));

  return (
    <div className="wrap">
      <div className="headline">
        <div>
          <h1>Model Performance</h1>
          <p>{metrics.algorithm} · Version {metrics.version_name} · Trained {new Date(metrics.trained_at).toLocaleDateString('en-IN')}</p>
        </div>
      </div>

      {/* Top stats */}
      <div className="stats">
        {[
          { label: 'Macro F1 Score', value: metrics.macro_f1.toFixed(4), cls: 'teal' },
          { label: 'Precision', value: metrics.precision_score.toFixed(4), cls: 'blue' },
          { label: 'Recall', value: metrics.recall_score.toFixed(4), cls: 'amber' },
          { label: 'Algorithm', value: 'XGBoost', cls: '' },
        ].map((s) => (
          <div className="stat" key={s.label}>
            <div className="stat-label">{s.label}</div>
            <div className={`stat-value mono ${s.cls}`}>{s.value}</div>
            <div className="stat-delta">{s.label === 'Algorithm' ? 'WeightedDecision wrapper' : 'on holdout test set'}</div>
          </div>
        ))}
      </div>

      <div className="grid-main">
        {/* Left: per-class table */}
        <div className="panel">
          <div className="panel-title">Per-Class Metrics</div>
          <div className="panel-sub">Weighted decision classifier with custom class penalties</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Class</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1-Score</th>
                  <th>Support</th>
                  <th>Decision Weight</th>
                </tr>
              </thead>
              <tbody>
                {['I', 'II', 'III'].map((cls) => {
                  const d = metrics.per_class?.[cls] || {};
                  const w = weights[cls];
                  return (
                    <tr key={cls}>
                      <td><span className={`risk-pill ${CLASS_PILL[cls]}`}><span className="dot" />Class {cls}</span></td>
                      <td><span className="mono" style={{ color: CLASS_COLOR[cls], fontWeight: 600 }}>{d.precision != null ? (d.precision * 100).toFixed(1) + '%' : '—'}</span></td>
                      <td><span className="mono" style={{ color: CLASS_COLOR[cls], fontWeight: 600 }}>{d.recall != null ? (d.recall * 100).toFixed(1) + '%' : '—'}</span></td>
                      <td><span className="mono" style={{ color: CLASS_COLOR[cls], fontWeight: 600 }}>{d['f1-score'] != null ? (d['f1-score'] * 100).toFixed(1) + '%' : '—'}</span></td>
                      <td><span className="mono" style={{ color: 'var(--muted)' }}>{d.support ?? '—'}</span></td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div className="bar-bg" style={{ width: '60px' }}>
                            <div className="bar-fill" style={{ width: `${(w / maxWeight) * 100}%`, background: CLASS_COLOR[cls] }} />
                          </div>
                          <span className="mono" style={{ fontSize: '11px', fontWeight: 600, color: CLASS_COLOR[cls] }}>{w}×</span>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: gauges + weights */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="panel">
            <div className="panel-title">F1 Score by Class</div>
            <div className="panel-sub">Higher = better class-level performance</div>
            <div style={{ display: 'flex', justifyContent: 'space-around', padding: '12px 0' }}>
              {['I', 'II', 'III'].map((cls) => (
                <Gauge key={cls}
                  value={metrics.per_class?.[cls]?.['f1-score'] ?? 0}
                  label={`Class ${cls}`}
                  color={CLASS_COLOR[cls]}
                />
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="panel-title">Decision Weights</div>
            <div className="panel-sub">Higher weight = stronger penalty for misclassification</div>
            {['I', 'II', 'III'].map((cls) => {
              const w = weights[cls] ?? 1;
              return (
                <div className="factor" key={cls}>
                  <span className="factor-name">Class {cls}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div className="bar-bg" style={{ width: '80px' }}>
                      <div className="bar-fill" style={{ width: `${(w / maxWeight) * 100}%`, background: CLASS_COLOR[cls] }} />
                    </div>
                    <span className="mono" style={{ fontSize: '12px', fontWeight: 600, color: CLASS_COLOR[cls], width: '28px' }}>{w}×</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
