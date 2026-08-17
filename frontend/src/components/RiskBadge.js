export default function RiskBadge({ failure, full = false }) {
  if (failure === undefined || failure === null) return null;
  const pillCls = failure ? 'high' : 'low';
  const label = failure ? 'Failure' : 'No Failure';
  return (
    <span className={`risk-pill ${pillCls}`}>
      <span className="dot" />
      {full ? (failure ? 'Predicted Failure' : 'No Failure Predicted') : label}
    </span>
  );
}
