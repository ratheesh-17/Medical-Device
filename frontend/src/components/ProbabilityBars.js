const colors = { I: 'var(--red)', II: 'var(--amber)', III: 'var(--teal)' };

export default function ProbabilityBars({ probabilities }) {
  if (!probabilities) return null;
  return (
    <div>
      {['I', 'II', 'III'].map((cls) => {
        const pct = Math.round((probabilities[cls] ?? 0) * 100);
        return (
          <div className="prob-row" key={cls}>
            <span className="prob-label">Class {cls}</span>
            <div className="prob-track">
              <div className="prob-fill" style={{ width: `${pct}%`, background: colors[cls] }} />
            </div>
            <span className="prob-val">{pct}%</span>
          </div>
        );
      })}
    </div>
  );
}
