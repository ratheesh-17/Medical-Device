import { useState, useEffect, useRef, useCallback } from 'react';
import { predict, searchDevices, getHistory, getMetrics } from '../services/api';
import RiskBadge from '../components/RiskBadge';
import ConfidenceBar from '../components/ConfidenceBar';
import ProbabilityBars from '../components/ProbabilityBars';

function ScoreCircle({ confidence, failure }) {
  const pct = Math.round(confidence * 100);
  const color = failure ? 'var(--red)' : 'var(--teal)';
  const r = 28, circ = 2 * Math.PI * r;
  const dash = (pct / 100) * circ;
  return (
    <div className="score-circle" style={{ background: 'none' }}>
      <svg width="64" height="64" viewBox="0 0 64 64" style={{ position: 'absolute', transform: 'rotate(-90deg)' }}>
        <circle cx="32" cy="32" r={r} fill="none" stroke="var(--line)" strokeWidth="7" />
        <circle cx="32" cy="32" r={r} fill="none" stroke={color} strokeWidth="7"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" />
      </svg>
      <span style={{ color }}>{pct}%</span>
    </div>
  );
}

export default function PredictPage() {
  const [deviceId, setDeviceId] = useState('');
  const [priorIncidents, setPriorIncidents] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSugg, setShowSugg] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({ total: 0, failures: 0, lowConf: 0, roc_auc: null });
  const debounceRef = useRef(null);
  const suggRef = useRef(null);

  const loadStats = useCallback(async () => {
    try {
      const [histRes, metricsRes] = await Promise.all([getHistory(0, 200), getMetrics()]);
      const records = histRes.data;
      setStats({
        total: records.length,
        failures: records.filter((r) => r.predicted_failure).length,
        lowConf: records.filter((r) => r.low_confidence_flag).length,
        roc_auc: metricsRes.data.roc_auc,
      });
    } catch { }
  }, []);

  useEffect(() => { loadStats(); }, [loadStats]);

  useEffect(() => {
    const handler = (e) => { if (suggRef.current && !suggRef.current.contains(e.target)) setShowSugg(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleDeviceInput = (val) => {
    setDeviceId(val);
    clearTimeout(debounceRef.current);
    if (val.length < 1) { setSuggestions([]); setShowSugg(false); return; }
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await searchDevices(val, 8);
        setSuggestions(res.data);
        setShowSugg(res.data.length > 0);
      } catch { setSuggestions([]); }
    }, 250);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!deviceId.trim()) return;
    setLoading(true); setError(''); setResult(null);
    try {
      const payload = { device_id: parseInt(deviceId, 10) };
      if (priorIncidents !== '') payload.known_prior_incidents = parseInt(priorIncidents, 10);
      const res = await predict(payload);
      setResult(res.data);
      loadStats();
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed. Is the backend running?');
    } finally { setLoading(false); }
  };

  const reset = () => {
    setDeviceId(''); setPriorIncidents(''); setResult(null); setError('');
    setSuggestions([]); setShowSugg(false);
  };

  return (
    <div className="wrap">
      <div className="headline">
        <div>
          <h1>Device Failure Predictor</h1>
          <p>Enter a USA device ID to assess failure risk · XGBoost ThresholdedClassifier · Threshold 0.42 · ROC-AUC 0.8553</p>
        </div>
        <div className="headline-actions">
          {result && <button className="btn btn-secondary" onClick={reset}>Clear</button>}
        </div>
      </div>

      {/* Stat cards */}
      <div className="stats">
        <div className="stat">
          <div className="stat-label">Predictions Run</div>
          <div className="stat-value mono">{stats.total}</div>
          <div className="stat-delta">total in database</div>
        </div>
        <div className="stat">
          <div className="stat-label">Failure Predictions</div>
          <div className="stat-value red mono">{stats.failures}</div>
          <div className="stat-delta">predicted as failure</div>
        </div>
        <div className="stat">
          <div className="stat-label">Low Confidence</div>
          <div className="stat-value amber mono">{stats.lowConf}</div>
          <div className="stat-delta">flagged for review</div>
        </div>
        <div className="stat">
          <div className="stat-label">Model ROC-AUC</div>
          <div className="stat-value teal mono">{stats.roc_auc != null ? stats.roc_auc.toFixed(4) : '—'}</div>
          <div className="stat-delta">on holdout test set</div>
        </div>
      </div>

      {/* Main grid */}
      <div className="grid-main">
        {/* Left: Form */}
        <div className="panel">
          <div className="panel-title">Lookup Device by ID</div>
          <div className="panel-sub">Enter a USA device ID — all features are pulled automatically from the database</div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Device ID *</label>
              <div className="autocomplete-wrap" ref={suggRef}>
                <input
                  className="form-input mono"
                  type="text"
                  placeholder="Enter ID or search device name…"
                  value={deviceId}
                  onChange={(e) => handleDeviceInput(e.target.value)}
                  onFocus={() => suggestions.length > 0 && setShowSugg(true)}
                  autoComplete="off"
                  required
                />
                {showSugg && suggestions.length > 0 && (
                  <div className="autocomplete-list">
                    {suggestions.map((d) => (
                      <div key={d.id} className="autocomplete-item"
                        onMouseDown={() => { setDeviceId(String(d.id)); setSuggestions([]); setShowSugg(false); }}>
                        <span className="mono" style={{ fontWeight: 600 }}>#{d.id}</span>
                        {d.name ? ` — ${d.name}` : ''}
                        {d.classification ? <span style={{ color: 'var(--muted)', fontSize: '11px' }}> · {d.classification}</span> : ''}
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '4px' }}>
                USA device ID from the ICIJ Implant Files dataset. Description, classification, and manufacturer are fetched automatically.
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Prior Incidents <span style={{ textTransform: 'none', letterSpacing: 0, fontWeight: 400 }}>(optional — from maintenance log)</span></label>
              <input
                className="form-input"
                type="number"
                min="0"
                placeholder="e.g. 2"
                value={priorIncidents}
                onChange={(e) => setPriorIncidents(e.target.value)}
              />
              <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '4px' }}>
                Post-model escalation rule only — not a model feature.
              </div>
            </div>

            <button type="submit" className="btn btn-primary btn-full" disabled={loading} style={{ marginTop: '4px' }}>
              {loading
                ? <><span className="spinner" /> Analysing…</>
                : <><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg> Predict Failure Risk</>}
            </button>
          </form>

          {error && <div className="error-box">⚠ {error}</div>}

          {/* Device info card */}
          {result && (
            <div style={{ marginTop: '16px', padding: '12px', background: 'var(--panel-2)', borderRadius: '8px', border: '1px solid var(--line)' }}>
              <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Device Info</div>
              {[
                { label: 'ID', value: result.device_id },
                { label: 'Name', value: result.device_name || '—' },
                { label: 'Classification', value: result.device_classification || '—' },
                { label: 'Manufacturer', value: result.manufacturer_name || '—' },
              ].map(({ label, value }) => (
                <div className="factor" key={label}>
                  <span className="factor-name" style={{ color: 'var(--muted)', fontSize: '11px' }}>{label}</span>
                  <span className="mono" style={{ fontSize: '11px', color: 'var(--text)' }}>{value}</span>
                </div>
              ))}
              <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--muted)', lineHeight: 1.5 }}>
                {result.device_description?.slice(0, 160)}{result.device_description?.length > 160 ? '…' : ''}
              </div>
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="predict-result">
              <div className="score-row">
                <ScoreCircle confidence={result.confidence} failure={result.predicted_failure} />
                <div>
                  <div className="score-class">
                    {result.device_name || `Device #${result.device_id}`}
                  </div>
                  <div className={`score-sub ${result.predicted_failure ? 'red' : 'teal'}`}>
                    {result.predicted_label} · P(failure) = {(result.prob_failure * 100).toFixed(1)}%
                  </div>
                  <div style={{ marginTop: '6px' }}><RiskBadge failure={result.predicted_failure} /></div>
                </div>
              </div>

              {result.low_confidence_flag && (
                <div className="warn-banner">⚠ Low confidence — consider manual review</div>
              )}

              {result.escalated && (
                <div className="warn-banner" style={{ background: 'rgba(214,69,90,0.08)', borderColor: 'rgba(214,69,90,0.3)', color: 'var(--red)' }}>
                  🚨 Escalated — {result.escalation_note}
                </div>
              )}

              <div className="divider" />
              <div className="section-label">Failure Probability</div>
              <ProbabilityBars probFailure={result.prob_failure} probNoFailure={result.prob_no_failure} />

              {result.top_features?.length > 0 && (
                <>
                  <div className="divider" />
                  <div className="section-label">Top Influencing Features</div>
                  {result.top_features.map((f, i) => (
                    <div className="factor" key={i}>
                      <span className="factor-name">{f.feature}</span>
                      <span className={`factor-impact ${f.importance > 0.05 ? 'up' : f.importance > 0.02 ? 'neutral' : 'down'}`}>
                        {f.importance > 0.05 ? '▲' : f.importance > 0.02 ? '◆' : '▼'} {(f.importance * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
                </>
              )}
            </div>
          )}
        </div>

        {/* Right: Breakdown or How It Works */}
        <div className="panel">
          {result ? (
            <>
              <div className="panel-title">Prediction Breakdown</div>
              <div className="panel-sub">Model: {result.model_version} · XGBoost · Threshold 0.42</div>

              <div style={{ display: 'flex', justifyContent: 'center', padding: '16px 0 20px' }}>
                <ScoreCircle confidence={result.confidence} failure={result.predicted_failure} />
              </div>

              <ConfidenceBar value={result.confidence} />

              <div className="divider" />
              <div className="section-label">Probability Breakdown</div>
              <ProbabilityBars probFailure={result.prob_failure} probNoFailure={result.prob_no_failure} />

              <div className="divider" />
              <div className="section-label">Classification Details</div>
              {[
                { label: 'Prediction', value: result.predicted_label, color: result.predicted_failure ? 'var(--red)' : 'var(--teal)' },
                { label: 'P(Failure)', value: `${(result.prob_failure * 100).toFixed(1)}%`, color: 'var(--text)' },
                { label: 'P(No Failure)', value: `${(result.prob_no_failure * 100).toFixed(1)}%`, color: 'var(--text)' },
                { label: 'Confidence', value: `${Math.round(result.confidence * 100)}%`, color: 'var(--text)' },
                { label: 'Low Confidence Flag', value: result.low_confidence_flag ? 'Yes — review needed' : 'No', color: result.low_confidence_flag ? 'var(--amber)' : 'var(--teal)' },
                { label: 'Escalated', value: result.escalated ? 'Yes' : 'No', color: result.escalated ? 'var(--red)' : 'var(--teal)' },
                { label: 'Model Version', value: result.model_version, color: 'var(--muted)' },
              ].map((row) => (
                <div className="factor" key={row.label}>
                  <span className="factor-name" style={{ color: 'var(--muted)', fontSize: '12px' }}>{row.label}</span>
                  <span className="mono" style={{ fontSize: '12px', fontWeight: 600, color: row.color }}>{row.value}</span>
                </div>
              ))}
            </>
          ) : (
            <>
              <div className="panel-title">How It Works</div>
              <div className="panel-sub">XGBoost model trained on ICIJ Implant Files data · USA devices only</div>
              <div className="upload-zone" style={{ cursor: 'default' }}>
                <strong>Enter a Device ID to get started</strong>
                The system fetches description, classification, and manufacturer history automatically — no manual input needed
              </div>
              {[
                { failure: true,  label: 'Failure',    desc: 'P(failure) ≥ 0.42 — device has elevated risk based on manufacturer history and description signals.' },
                { failure: false, label: 'No Failure', desc: 'P(failure) < 0.42 — device does not show elevated failure risk based on available signals.' },
              ].map(({ failure, label, desc }) => (
                <div key={label} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', padding: '10px 0', borderBottom: '1px solid var(--line)' }}>
                  <RiskBadge failure={failure} />
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 600 }}>{label}</div>
                    <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>{desc}</div>
                  </div>
                </div>
              ))}
              <div style={{ marginTop: '16px', padding: '12px', background: 'var(--panel-2)', borderRadius: '8px', border: '1px solid var(--line)' }}>
                <div style={{ fontSize: '11px', color: 'var(--muted)', lineHeight: 1.6 }}>
                  <strong style={{ color: 'var(--text)' }}>Decision threshold: 0.42</strong><br />
                  Tuned to maximise Failure recall (0.70 → 0.83). In safety-critical domains, missing a true failure is more costly than a false alarm.
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
