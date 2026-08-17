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
          <span className="gauge-lbl">{label}</span>
        </div>
      </div>
    </div>
  );
}

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

  return (
    <div className="wrap">
      <div className="headline">
        <div>
          <h1>Model Performance</h1>
          <p>XGBoost + ThresholdedClassifier · Binary failure prediction · Decision threshold {metrics.threshold}</p>
        </div>
      </div>

      {/* Top stats */}
      <div className="stats">
        {[
          { label: 'ROC-AUC', value: metrics.roc_auc.toFixed(4), cls: 'teal', delta: 'threshold-independent' },
          { label: 'F1 (Tuned 0.42)', value: metrics.f1_tuned.toFixed(4), cls: 'blue', delta: 'at decision threshold' },
          { label: 'F1 (Default 0.50)', value: metrics.f1_default.toFixed(4), cls: 'amber', delta: 'baseline comparison' },
          { label: 'Decision Threshold', value: metrics.threshold, cls: '', delta: 'P(failure) ≥ threshold → Failure' },
        ].map((s) => (
          <div className="stat" key={s.label}>
            <div className="stat-label">{s.label}</div>
            <div className={`stat-value mono ${s.cls}`}>{s.value}</div>
            <div className="stat-delta">{s.delta}</div>
          </div>
        ))}
      </div>

      <div className="grid-main">
        {/* Left: metric details table */}
        <div className="panel">
          <div className="panel-title">Metric Breakdown</div>
          <div className="panel-sub">Test set evaluation · 6,733 held-out USA devices · 80/20 stratified split</div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Value</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { metric: 'ROC-AUC', value: metrics.roc_auc.toFixed(4), color: 'var(--teal)', desc: 'Area under ROC curve — threshold-independent discriminative ability' },
                  { metric: 'F1 (threshold 0.42)', value: metrics.f1_tuned.toFixed(4), color: 'var(--blue)', desc: 'F1 at tuned threshold — optimised for Failure recall' },
                  { metric: 'F1 (threshold 0.50)', value: metrics.f1_default.toFixed(4), color: 'var(--amber)', desc: 'F1 at default threshold — baseline comparison' },
                  { metric: 'Failure Recall (tuned)', value: '0.83', color: 'var(--red)', desc: 'Of all true failures, 83% correctly identified at threshold 0.42' },
                  { metric: 'Failure Recall (default)', value: '0.70', color: 'var(--muted)', desc: 'Of all true failures, 70% correctly identified at threshold 0.50' },
                  { metric: 'Decision Threshold', value: metrics.threshold, color: 'var(--text)', desc: 'P(failure) ≥ 0.42 → predicted Failure' },
                ].map((row) => (
                  <tr key={row.metric}>
                    <td><span style={{ fontWeight: 600, fontSize: '13px' }}>{row.metric}</span></td>
                    <td><span className="mono" style={{ fontWeight: 700, color: row.color }}>{row.value}</span></td>
                    <td><span style={{ color: 'var(--muted)', fontSize: '12px' }}>{row.desc}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: gauges + threshold note */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div className="panel">
            <div className="panel-title">Key Metrics at a Glance</div>
            <div className="panel-sub">Higher = better</div>
            <div style={{ display: 'flex', justifyContent: 'space-around', padding: '12px 0' }}>
              <Gauge value={metrics.roc_auc} label="ROC-AUC" color="var(--teal)" />
              <Gauge value={metrics.f1_tuned} label="F1 Tuned" color="var(--blue)" />
              <Gauge value={metrics.f1_default} label="F1 Default" color="var(--amber)" />
            </div>
          </div>

          <div className="panel">
            <div className="panel-title">Threshold Tuning Impact</div>
            <div className="panel-sub">Why 0.42 instead of 0.50?</div>
            {[
              { label: 'Failure Recall @ 0.50', value: '70%', color: 'var(--muted)', pct: 70 },
              { label: 'Failure Recall @ 0.42', value: '83%', color: 'var(--teal)', pct: 83 },
              { label: 'F1 @ 0.50', value: `${(metrics.f1_default * 100).toFixed(1)}%`, color: 'var(--muted)', pct: Math.round(metrics.f1_default * 100) },
              { label: 'F1 @ 0.42', value: `${(metrics.f1_tuned * 100).toFixed(1)}%`, color: 'var(--blue)', pct: Math.round(metrics.f1_tuned * 100) },
            ].map((row) => (
              <div className="factor" key={row.label}>
                <span className="factor-name" style={{ fontSize: '12px' }}>{row.label}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div className="bar-bg" style={{ width: '80px' }}>
                    <div className="bar-fill" style={{ width: `${row.pct}%`, background: row.color }} />
                  </div>
                  <span className="mono" style={{ fontSize: '12px', fontWeight: 600, color: row.color, width: '36px' }}>{row.value}</span>
                </div>
              </div>
            ))}
            <div style={{ marginTop: '14px', padding: '10px 12px', background: 'var(--panel-2)', borderRadius: '8px', border: '1px solid var(--line)', fontSize: '11px', color: 'var(--muted)', lineHeight: 1.6 }}>
              In a safety-critical domain, missing a true failure (false negative) is more costly than a false alarm. Threshold 0.42 improves Failure recall by <strong style={{ color: 'var(--teal)' }}>+13 percentage points</strong>.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
