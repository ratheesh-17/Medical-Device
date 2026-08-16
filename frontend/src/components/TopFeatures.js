export default function TopFeatures({ features }) {
  if (!features || features.length === 0) return null;
  return (
    <div>
      {features.map((f, i) => (
        <div className="feature-item" key={i}>
          <span className="feature-rank">{i + 1}</span>
          <span className="feature-name">{f.feature}</span>
          <span className="feature-score">{(f.importance * 100).toFixed(1)}%</span>
        </div>
      ))}
    </div>
  );
}
