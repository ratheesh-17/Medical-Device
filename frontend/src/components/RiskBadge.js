const config = {
  I:   { cls: 'high', label: 'Class I — Critical Risk' },
  II:  { cls: 'med',  label: 'Class II — Moderate Risk' },
  III: { cls: 'low',  label: 'Class III — Low Risk' },
};

export default function RiskBadge({ cls, full = false }) {
  if (!cls || !config[cls]) return null;
  const { cls: pillCls, label } = config[cls];
  return (
    <span className={`risk-pill ${pillCls}`}>
      <span className="dot" />
      {full ? label : `Class ${cls}`}
    </span>
  );
}
