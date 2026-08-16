import { useState, useEffect, useCallback } from 'react';
import { getHistory } from '../services/api';
import RiskBadge from '../components/RiskBadge';

const LIMIT = 25;

export default function HistoryPage() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const load = useCallback(async (s = 0) => {
    setLoading(true);
    try {
      const res = await getHistory(s, LIMIT);
      setRecords((prev) => s === 0 ? res.data : [...prev, ...res.data]);
      setHasMore(res.data.length === LIMIT);
    } catch { }
    setLoading(false);
  }, []);

  useEffect(() => { load(0); }, [load]);

  const loadMore = () => { const next = skip + LIMIT; setSkip(next); load(next); };

  const fmt = (dt) => new Date(dt).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });

  const confColor = (c) => c >= 0.75 ? 'var(--teal)' : c >= 0.5 ? 'var(--amber)' : 'var(--red)';

  return (
    <div className="wrap">
      <div className="headline">
        <div>
          <h1>Prediction History</h1>
          <p>{records.length} records · All past predictions stored in database</p>
        </div>
        <button className="btn btn-secondary" onClick={() => { setSkip(0); load(0); }}>↻ Refresh</button>
      </div>

      <div className="panel">
        {loading && records.length === 0 ? (
          <div className="spinner-center"><div className="spinner spinner-lg" /></div>
        ) : records.length === 0 ? (
          <div className="empty">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            <p>No predictions yet. Run your first prediction!</p>
          </div>
        ) : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Device Description</th>
                    <th>Classification</th>
                    <th>Manufacturer</th>
                    <th>Risk Class</th>
                    <th>Confidence</th>
                    <th>Flag</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((r) => (
                    <tr key={r.id}>
                      <td><span className="mono" style={{ color: 'var(--muted)', fontSize: '11px' }}>#{r.id}</span></td>
                      <td style={{ maxWidth: '240px' }}>
                        <div className="dev-name" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '220px' }} title={r.input_description}>
                          {r.input_description}
                        </div>
                      </td>
                      <td><span style={{ color: 'var(--muted)', fontSize: '12px' }}>{r.input_classification}</span></td>
                      <td><span style={{ color: 'var(--muted)', fontSize: '12px' }}>{r.input_manufacturer || '—'}</span></td>
                      <td><RiskBadge cls={r.predicted_class} /></td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div className="bar-bg" style={{ width: '60px' }}>
                            <div className="bar-fill" style={{ width: `${Math.round(r.confidence * 100)}%`, background: confColor(r.confidence) }} />
                          </div>
                          <span className="mono" style={{ fontSize: '11px', color: confColor(r.confidence) }}>
                            {Math.round(r.confidence * 100)}%
                          </span>
                        </div>
                      </td>
                      <td>
                        {r.low_confidence_flag
                          ? <span style={{ color: 'var(--amber)', fontSize: '11px', fontWeight: 600 }}>⚠ Low</span>
                          : <span style={{ color: 'var(--teal)', fontSize: '11px', fontWeight: 600 }}>✓ OK</span>}
                      </td>
                      <td><span style={{ color: 'var(--muted)', fontSize: '11px', whiteSpace: 'nowrap' }}>{fmt(r.created_at)}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {hasMore && (
              <div style={{ textAlign: 'center', marginTop: '20px' }}>
                <button className="btn btn-secondary" onClick={loadMore} disabled={loading}>
                  {loading ? <><span className="spinner" /> Loading…</> : 'Load More'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
