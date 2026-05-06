import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useVehicle } from '../../hooks/useFleetData';
import TopBar from '../../components/Layout/TopBar';
import KpiCard from '../../components/Charts/KpiCard';
import { Bot, Gauge, Clock, MapPin, Battery, Thermometer, Activity } from 'lucide-react';
import './VehicleDetail.css';

export default function VehicleDetail() {
  const { id } = useParams();
  const { data: vehicle, loading } = useVehicle(id);
  const [activeTab, setActiveTab] = useState('overview');
  const navigate = useNavigate();

  if (loading || !vehicle) {
    return (
      <>
        <TopBar title={id} showBack />
        <div className="page page-with-topbar">
          <div className="skeleton" style={{ height: 200, borderRadius: 12 }} />
        </div>
      </>
    );
  }

  const tabs = ['Overview', 'Timeline', 'Diagnostics', 'Trips'];

  return (
    <>
      <TopBar title={vehicle.asset_id} showBack />
      <div className="page page-with-topbar">
        {/* Status banner */}
        <div className={`vd-banner vd-banner-${vehicle.status} animate-fade-in`}>
          <span className={`badge badge-${vehicle.status === 'critical' ? 'critical' : vehicle.status === 'warning' ? 'warning' : 'success'}`}>
            ● {vehicle.status}
          </span>
          <span className="vd-banner-name">{vehicle.asset_name}</span>
        </div>

        {/* Quick metrics */}
        <div className="vd-quick animate-fade-in" style={{ animationDelay: '50ms' }}>
          <div className="vd-quick-item">
            <Gauge size={16} />
            <div>
              <span className="vd-quick-val">{vehicle.latest_idle_minutes ?? '--'}</span>
              <span className="vd-quick-label">Idle (min)</span>
            </div>
          </div>
          <div className="vd-quick-item">
            <Battery size={16} />
            <div>
              <span className="vd-quick-val">{vehicle.latest_battery_voltage ?? '--'}V</span>
              <span className="vd-quick-label">Battery</span>
            </div>
          </div>
          {vehicle.refrigerated && (
            <div className="vd-quick-item">
              <Thermometer size={16} />
              <div>
                <span className="vd-quick-val">{vehicle.latest_refrigeration_temp ?? '--'}°C</span>
                <span className="vd-quick-label">Temp</span>
              </div>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="tabs" style={{ marginTop: 16, marginBottom: 16 }}>
          {tabs.map((t) => (
            <button
              key={t}
              className={`tab ${activeTab === t.toLowerCase() ? 'active' : ''}`}
              onClick={() => setActiveTab(t.toLowerCase())}
            >
              {t}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="stagger">
            <div className="card animate-fade-in">
              <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Vehicle Info</h3>
              <div className="vd-info-grid">
                <div className="vd-info-item"><span>Asset ID</span><span>{vehicle.asset_id}</span></div>
                <div className="vd-info-item"><span>Name</span><span>{vehicle.asset_name}</span></div>
                <div className="vd-info-item"><span>Type</span><span>{vehicle.asset_type}</span></div>
                <div className="vd-info-item"><span>Region</span><span>{vehicle.region}</span></div>
                <div className="vd-info-item"><span>Device</span><span>{vehicle.device_model}</span></div>
                <div className="vd-info-item"><span>Refrigerated</span><span>{vehicle.refrigerated ? 'Yes' : 'No'}</span></div>
                <div className="vd-info-item"><span>Odometer</span><span>{vehicle.latest_odometer_km?.toLocaleString()} km</span></div>
              </div>
            </div>

            {/* Today's Summary */}
            <div className="card-grid" style={{ marginTop: 12 }}>
              <KpiCard icon={MapPin} label="Distance" value="128 km" color="blue" />
              <KpiCard icon={Clock} label="Drive Time" value="2h 45m" color="green" />
              <KpiCard icon={Activity} label="Trips" value={vehicle.latest_trip_count ?? 0} color="purple" />
              <KpiCard icon={Gauge} label="Efficiency" value="7.2 km/L" color="amber" />
            </div>

            {/* Alert History */}
            {vehicle.alert_history?.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>Alert History</h3>
                {vehicle.alert_history.map((alert, i) => (
                  <div key={i} className="card vd-alert-item" style={{ marginBottom: 8 }}>
                    <div className="dash-alert-row">
                      <span className={`status-dot ${alert.severity === 'high' ? 'critical' : 'warning'}`} />
                      <div className="dash-alert-info">
                        <span className="dash-alert-note">{alert.note}</span>
                        <span className="dash-alert-meta">
                          {alert.alert_type} · {new Date(alert.timestamp).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'timeline' && (
          <div className="card animate-fade-in">
            <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
              Metrics history for {vehicle.asset_id}:
            </p>
            {vehicle.metrics_history?.map((m, i) => (
              <div key={i} className="vd-timeline-item">
                <span className="vd-timeline-date">{m.date}</span>
                <span>{m.trip_count} trips · {m.engine_hours}h engine · {m.idle_minutes}min idle</span>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'diagnostics' && (
          <div className="card animate-fade-in">
            <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 12 }}>
              {vehicle.alert_count} alert(s) recorded for this vehicle.
            </p>
            {vehicle.alert_count === 0 && <p style={{ color: 'var(--accent-green)' }}>✓ No diagnostic issues</p>}
            {vehicle.alert_history?.map((a, i) => (
              <div key={i} style={{ padding: '8px 0', borderBottom: '1px solid var(--border-subtle)' }}>
                <strong style={{ color: a.severity === 'high' ? 'var(--accent-red)' : 'var(--accent-amber)' }}>
                  {a.alert_type}
                </strong>
                <span style={{ marginLeft: 8, fontSize: 13, color: 'var(--text-secondary)' }}>
                  {a.sensor_value} — {a.note}
                </span>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'trips' && (
          <div className="card animate-fade-in">
            <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
              Trip data for {vehicle.asset_id}:
            </p>
            {vehicle.metrics_history?.map((m, i) => (
              <div key={i} className="vd-timeline-item">
                <span className="vd-timeline-date">{m.date}</span>
                <span>{m.trip_count} trip(s) — {m.odometer_km?.toLocaleString()} km odometer</span>
              </div>
            ))}
          </div>
        )}

        {/* Ask AI */}
        <button
          className="btn btn-primary vd-ask-ai animate-slide-up"
          onClick={() => navigate(`/copilot?context=vehicle&id=${vehicle.asset_id}`)}
        >
          <Bot size={18} /> Ask AI about {vehicle.asset_id}
        </button>
      </div>
    </>
  );
}
