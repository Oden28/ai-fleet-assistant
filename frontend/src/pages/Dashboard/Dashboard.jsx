import { useFleetSummary, useAlerts } from '../../hooks/useFleetData';
import KpiCard from '../../components/Charts/KpiCard';
import Gauge from '../../components/Charts/Gauge';
import { Truck, Activity, Wrench, Bell, Fuel, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './Dashboard.css';

export default function Dashboard() {
  const { data: summary, loading } = useFleetSummary();
  const { data: alertsData } = useAlerts();
  const navigate = useNavigate();

  const user = JSON.parse(localStorage.getItem('fleet_user') || '{}');
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  if (loading || !summary) {
    return (
      <div className="page page-with-topbar">
        <div className="dash-skeleton">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: 100, borderRadius: 12 }} />
          ))}
        </div>
      </div>
    );
  }

  const recentAlerts = alertsData?.alerts?.slice(0, 4) || [];

  return (
    <div className="page page-with-topbar">
      <header className="dash-header animate-fade-in">
        <div>
          <h1 className="dash-greeting">{greeting}, {user.name || 'User'} 👋</h1>
          <p className="dash-subtitle">Here's what's happening with your fleet.</p>
        </div>
      </header>

      {/* KPI Grid */}
      <div className="card-grid stagger" style={{ marginBottom: 20 }}>
        <KpiCard
          icon={Truck}
          label="Total Vehicles"
          value={summary.total_vehicles}
          sub={`↑ ${summary.active_vehicles} active`}
          color="blue"
        />
        <KpiCard
          icon={Activity}
          label="Active Vehicles"
          value={summary.active_vehicles}
          trend={`↑ ${summary.active_vehicles}`}
          color="green"
        />
        <KpiCard
          icon={Wrench}
          label="Maintenance Due"
          value={summary.warning_alerts}
          trend={`↑ ${summary.warning_alerts}`}
          color="amber"
        />
        <KpiCard
          icon={Bell}
          label="Open Alerts"
          value={summary.total_alerts}
          trend={`↑ ${summary.critical_alerts} critical`}
          color="red"
        />
      </div>

      {/* Fleet Health */}
      <div className="card dash-health animate-slide-up" style={{ animationDelay: '100ms' }}>
        <div className="dash-health-row">
          <Gauge value={summary.fleet_health_score} size={110} />
          <div className="dash-health-info">
            <span className="badge badge-success">
              {summary.fleet_health_score >= 70 ? '● Good' :
               summary.fleet_health_score >= 40 ? '● Fair' : '● Needs Attention'}
            </span>
            <p className="dash-health-desc">
              Your fleet is operating {summary.fleet_health_score >= 70 ? 'well' : 'with some concerns'}.
              {summary.critical_alerts > 0 && ` ${summary.critical_alerts} critical alert(s) need attention.`}
            </p>
          </div>
        </div>
        <div className="section-header" style={{ marginTop: 16 }}>
          <span className="section-title" style={{ fontSize: 14 }}>Fleet Health</span>
        </div>
      </div>

      {/* Fuel Efficiency */}
      <div className="card dash-fuel animate-slide-up" style={{ animationDelay: '200ms', marginTop: 12 }}>
        <div className="section-header">
          <span className="section-title" style={{ fontSize: 14 }}>
            <Fuel size={14} style={{ marginRight: 6, verticalAlign: -2 }} />
            Fuel Efficiency (This Week)
          </span>
        </div>
        <div className="dash-fuel-value">
          12.4 <span>km/L</span>
        </div>
        <div className="dash-fuel-trend">↑ 4.0% vs last week</div>
        {/* Sparkline placeholder */}
        <div className="dash-sparkline">
          <svg viewBox="0 0 200 40" className="dash-spark-svg">
            <polyline
              points="0,30 30,25 60,28 90,20 120,22 150,15 180,18 200,10"
              fill="none"
              stroke="var(--accent-blue)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <polyline
              points="0,30 30,25 60,28 90,20 120,22 150,15 180,18 200,10 200,40 0,40"
              fill="url(#sparkGrad)"
              opacity="0.3"
            />
            <defs>
              <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--accent-blue)" />
                <stop offset="100%" stopColor="transparent" />
              </linearGradient>
            </defs>
          </svg>
          <div className="dash-spark-labels">
            <span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span>
            <span>Fri</span><span>Sat</span><span>Sun</span>
          </div>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="dash-alerts animate-slide-up" style={{ animationDelay: '300ms', marginTop: 20 }}>
        <div className="section-header">
          <span className="section-title">Recent Alerts</span>
          <button className="btn btn-ghost" onClick={() => navigate('/alerts')}>View all</button>
        </div>
        <div className="stagger">
          {recentAlerts.map((alert, i) => (
            <div key={i} className="card dash-alert-card animate-fade-in" style={{ marginBottom: 8 }}>
              <div className="dash-alert-row">
                <AlertTriangle
                  size={16}
                  style={{
                    color: alert.severity === 'high' ? 'var(--accent-red)' :
                           alert.severity === 'medium' ? 'var(--accent-amber)' : 'var(--accent-blue)',
                    flexShrink: 0,
                  }}
                />
                <div className="dash-alert-info">
                  <span className="dash-alert-note">{alert.note}</span>
                  <span className="dash-alert-meta">
                    {alert.asset_name || alert.asset_id} · {new Date(alert.timestamp).toLocaleDateString()}
                  </span>
                </div>
                <span className={`badge badge-${alert.severity === 'high' ? 'critical' : alert.severity === 'medium' ? 'warning' : 'info'}`}>
                  {alert.severity}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
