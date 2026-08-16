export default function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100);
  const color = pct >= 75 ? 'var(--teal)' : pct >= 50 ? 'var(--amber)' : 'var(--red)';
  return (
    <div className="conf-wrap">
      <div className="conf-row"><span>Confidence</span><span className="mono">{pct}%</span></div>
      <div className="conf-track">
        <div className="conf-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
}
