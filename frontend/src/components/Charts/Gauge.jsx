import './Gauge.css';

export default function Gauge({ value, max = 100, label, color, size = 120 }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  const getColor = () => {
    if (color) return color;
    if (pct >= 70) return 'var(--accent-green)';
    if (pct >= 40) return 'var(--accent-amber)';
    return 'var(--accent-red)';
  };

  const getGrade = () => {
    if (pct >= 85) return 'Excellent';
    if (pct >= 70) return 'Good';
    if (pct >= 50) return 'Fair';
    if (pct >= 30) return 'Poor';
    return 'Critical';
  };

  return (
    <div className="gauge" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="gauge-svg">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--border-subtle)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getColor()}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="gauge-progress"
          style={{
            filter: `drop-shadow(0 0 6px ${getColor()})`,
          }}
        />
      </svg>
      <div className="gauge-center">
        <span className="gauge-value" style={{ color: getColor() }}>
          {Math.round(value)}
        </span>
        <span className="gauge-label">{label || getGrade()}</span>
      </div>
    </div>
  );
}
