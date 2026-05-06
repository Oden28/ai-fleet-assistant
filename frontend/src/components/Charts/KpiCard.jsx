import './KpiCard.css';

export default function KpiCard({ icon: Icon, label, value, sub, trend, color = 'blue' }) {
  return (
    <div className={`kpi-card kpi-${color}`}>
      <div className="kpi-icon-wrap">
        {Icon && <Icon size={18} />}
      </div>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {(sub || trend) && (
        <div className="kpi-footer">
          {trend && (
            <span className={`kpi-trend ${trend.startsWith('+') || trend.startsWith('↑') ? 'up' : 'down'}`}>
              {trend}
            </span>
          )}
          {sub && <span className="kpi-sub">{sub}</span>}
        </div>
      )}
    </div>
  );
}
