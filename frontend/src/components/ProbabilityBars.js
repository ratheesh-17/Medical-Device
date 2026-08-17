export default function ProbabilityBars({ probFailure, probNoFailure }) {
  if (probFailure == null) return null;
  const bars = [
    { label: 'Failure', pct: Math.round(probFailure * 100), color: 'var(--red)' },
    { label: 'No Fail', pct: Math.round(probNoFailure * 100), color: 'var(--teal)' },
  ];
  return (
    <div>
      {bars.map(({ label, pct, color }) => (
        <div className="prob-row" key={label}>
          <span className="prob-label">{label}</span>
          <div className="prob-track">
            <div className="prob-fill" style={{ width: `${pct}%`, background: color }} />
          </div>
          <span className="prob-val">{pct}%</span>
        </div>
      ))}
    </div>
  );
}
