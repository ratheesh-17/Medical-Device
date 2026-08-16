import { useState, useEffect, useRef, useCallback } from 'react';
import { predict, getManufacturers, getHistory, getMetrics } from '../services/api';
import RiskBadge from '../components/RiskBadge';
import ConfidenceBar from '../components/ConfidenceBar';
import ProbabilityBars from '../components/ProbabilityBars';

const CLASSIFICATIONS = [
  'Cardiovascular Devices', 'Orthopedic Devices', 'Neurological Devices',
  'Ophthalmic Devices', 'Dental Devices', 'Diagnostic Imaging Devices',
  'General Hospital Devices', 'In Vitro Diagnostic Devices',
  'Obstetrical and Gynecological Devices', 'Ear, Nose, Throat Devices',
  'Gastroenterology Devices', 'Hematology Devices', 'Immunology Devices',
  'Anesthesiology Devices', 'Physical Medicine Devices', 'Radiology Devices',
  'General and Plastic Surgery Devices', 'Toxicology Devices',
];

const CLASS_COLOR = { I: 'var(--red)', II: 'var(--amber)', III: 'var(--teal)' };
const CLASS_SUB_CLS = { I: 'red', II: 'amber', III: 'teal' };
const CLASS_LABEL = { I: 'Class I — Critical Risk', II: 'Class II — Moderate Risk', III: 'Class III — Low Risk' };

function ScoreCircle({ confidence, cls }) {
  const pct = Math.round(confidence * 100);
  const color = CLASS_COLOR[cls] || 'var(--muted)';
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
  const [form, setForm] = useState({ description: '', classification: '', manufacturer_name: '' });
  const [mfrQuery, setMfrQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSugg, setShowSugg] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({ total: 0, high: 0, med: 0, f1: null });
  const debounceRef = useRef(null);
  const suggRef = useRef(null);

  // Load summary stats for the stat cards
  const loadStats = useCallback(async () => {
    try {
      const [histRes, metricsRes] = await Promise.all([getHistory(0, 200), getMetrics()]);
      const records = histRes.data;
      setStats({
        total: records.length,
        high: records.filter((r) => r.predicted_class === 'I').length,
        med: records.filter((r) => r.predicted_class === 'II').length,
        f1: metricsRes.data.macro_f1,
      });
    } catch { }
  }, []);

  useEffect(() => { loadStats(); }, [loadStats]);

  useEffect(() => {
    const handler = (e) => { if (suggRef.current && !suggRef.current.contains(e.target)) setShowSugg(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleMfrInput = (val) => {
    setMfrQuery(val);
    setForm((f) => ({ ...f, manufacturer_name: val }));
    clearTimeout(debounceRef.current);
    if (val.length < 2) { setSuggestions([]); setShowSugg(false); return; }
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await getManufacturers(val, 8);
        setSuggestions(res.data);
        setShowSugg(true);
      } catch { setSuggestions([]); }
    }, 250);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await predict(form);
      setResult(res.data);
      loadStats();
    } catch (err) {
      setError(err.response?.data?.detail || 'Prediction failed. Is the backend running?');
    } finally { setLoading(false); }
  };

  const reset = () => {
    setForm({ description: '', classification: '', manufacturer_name: '' });
    setMfrQuery(''); setResult(null); setError('');
  };

  return (
    <div className="wrap">
      {/* Headline */}
      <div className="headline">
        <div>
          <h1>Device Risk Predictor</h1>
          <p>Predict FDA risk class (I / II / III) · Model: XGBoost WeightedDecision v1.0 · Macro-F1 0.8014</p>
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
          <div className="stat-label">Class I (Critical)</div>
          <div className="stat-value red mono">{stats.high}</div>
          <div className="stat-delta">high-risk predictions</div>
        </div>
        <div className="stat">
          <div className="stat-label">Class II (Moderate)</div>
          <div className="stat-value amber mono">{stats.med}</div>
          <div className="stat-delta">moderate-risk predictions</div>
        </div>
        <div className="stat">
          <div className="stat-label">Model F1 Score</div>
          <div className="stat-value teal mono">{stats.f1 != null ? stats.f1.toFixed(4) : '—'}</div>
          <div className="stat-delta">on holdout test set</div>
        </div>
      </div>

      {/* Main grid */}
      <div className="grid-main">
        {/* Left: Form */}
        <div className="panel">
          <div className="panel-title">Run New Prediction</div>
          <div className="panel-sub">Enter device details to get an instant risk classification</div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Device Description *</label>
              <textarea
                className="form-textarea"
                placeholder="e.g. Implantable cardiac pacemaker for rhythm management and arrhythmia treatment…"
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Device Classification *</label>
              <select
                className="form-select"
                value={form.classification}
                onChange={(e) => setForm((f) => ({ ...f, classification: e.target.value }))}
                required
              >
                <option value="">Select classification…</option>
                {CLASSIFICATIONS.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Manufacturer <span style={{ textTransform: 'none', letterSpacing: 0, fontWeight: 400 }}>(optional)</span></label>
              <div className="autocomplete-wrap" ref={suggRef}>
                <input
                  className="form-input"
                  placeholder="Search manufacturer name…"
                  value={mfrQuery}
                  onChange={(e) => handleMfrInput(e.target.value)}
                  onFocus={() => suggestions.length > 0 && setShowSugg(true)}
                  autoComplete="off"
                />
                {showSugg && suggestions.length > 0 && (
                  <div className="autocomplete-list">
                    {suggestions.map((m) => (
                      <div key={m.id} className="autocomplete-item"
                        onMouseDown={() => { setMfrQuery(m.name); setForm((f) => ({ ...f, manufacturer_name: m.name })); setShowSugg(false); }}>
                        {m.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <button type="submit" className="btn btn-primary btn-full" disabled={loading} style={{ marginTop: '4px' }}>
              {loading
                ? <><span className="spinner" /> Analysing…</>
                : <><svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg> Predict Risk Class</>}
            </button>
          </form>

          {error && <div className="error-box">⚠ {error}</div>}

          {/* Result */}
          {result && (
            <div className="predict-result">
              <div className="score-row">
                <ScoreCircle confidence={result.confidence} cls={result.predicted_class} />
                <div>
                  <div className="score-class">{form.description.slice(0, 40)}{form.description.length > 40 ? '…' : ''}</div>
                  <div className={`score-sub ${CLASS_SUB_CLS[result.predicted_class]}`}>
                    {CLASS_LABEL[result.predicted_class]}
                  </div>
                  <div style={{ marginTop: '6px' }}><RiskBadge cls={result.predicted_class} /></div>
                </div>
              </div>

              {result.low_confidence_flag && (
                <div className="warn-banner">⚠ Low confidence — consider manual review</div>
              )}

              <div className="divider" />
              <div className="section-label">Class Probabilities</div>
              <ProbabilityBars probabilities={result.probabilities} />

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

        {/* Right: Confidence breakdown (shown after prediction, else placeholder) */}
        <div className="panel">
          {result ? (
            <>
              <div className="panel-title">Prediction Breakdown</div>
              <div className="panel-sub">Model: {result.model_version} · XGBoost WeightedDecision</div>

              <div style={{ display: 'flex', justifyContent: 'center', padding: '16px 0 20px' }}>
                <ScoreCircle confidence={result.confidence} cls={result.predicted_class} />
              </div>

              <ConfidenceBar value={result.confidence} />

              <div className="divider" />
              <div className="section-label">Risk Class Distribution</div>
              <ProbabilityBars probabilities={result.probabilities} />

              <div className="divider" />
              <div className="section-label">Classification Details</div>
              {[
                { label: 'Predicted Class', value: `Class ${result.predicted_class}`, color: CLASS_COLOR[result.predicted_class] },
                { label: 'Confidence', value: `${Math.round(result.confidence * 100)}%`, color: 'var(--text)' },
                { label: 'Low Confidence Flag', value: result.low_confidence_flag ? 'Yes — review needed' : 'No', color: result.low_confidence_flag ? 'var(--amber)' : 'var(--teal)' },
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
              <div className="panel-sub">XGBoost model trained on ICIJ Implant Files data</div>
              <div className="upload-zone" style={{ cursor: 'default' }}>
                <strong>Fill in the form to get started</strong>
                Enter a device description and classification to predict its FDA risk class
              </div>
              {[
                { cls: 'I',   label: 'Class I — Critical Risk',  desc: 'Reasonable chance of causing serious health problems or death.' },
                { cls: 'II',  label: 'Class II — Moderate Risk', desc: 'May cause temporary health problems or slight chance of serious harm.' },
                { cls: 'III', label: 'Class III — Low Risk',     desc: 'Not likely to cause any health problem or injury.' },
              ].map(({ cls, label, desc }) => (
                <div key={cls} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start', padding: '10px 0', borderBottom: '1px solid var(--line)' }}>
                  <RiskBadge cls={cls} />
                  <div>
                    <div style={{ fontSize: '12px', fontWeight: 600 }}>{label}</div>
                    <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>{desc}</div>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
