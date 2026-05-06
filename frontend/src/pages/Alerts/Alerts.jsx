import { useState } from 'react';
import { useAlerts } from '../../hooks/useFleetData';
import { useNavigate } from 'react-router-dom';
import TopBar from '../../components/Layout/TopBar';
import { AlertTriangle, Bot } from 'lucide-react';
import './Alerts.css';

export default function Alerts() {
  const [severity, setSeverity] = useState(null);
  const { data, loading } = useAlerts({ severity });
  const navigate = useNavigate();

  const tabs = [
    { id: null, label: 'All', count: data?.total },
    { id: 'high', label: 'Critical', count: data?.critical },
    { id: 'medium', label: 'Warning', count: data?.warning },
    { id: 'low', label: 'Info', count: data?.info },
  ];

  return (
    <>
      <TopBar title="Alerts" />
      <div className="page page-with-topbar">
        <div className="tabs" style={{ marginBottom: 16 }}>
          {tabs.map((t) => (
            <button
              key={t.id ?? 'all'}
              className={`tab ${severity === t.id ? 'active' : ''}`}
              onClick={() => setSeverity(t.id)}
            >
              {t.label}
              {t.count != null && <span className="tab-count">({t.count})</span>}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="stagger">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 72, marginBottom: 8, borderRadius: 12 }} />
            ))}
          </div>
        ) : (
          <div className="stagger">
            {data?.alerts?.map((alert, i) => (
              <div key={i} className="card alert-card animate-fade-in">
                <div className="alert-card-header">
                  <AlertTriangle
                    size={16}
                    style={{
                      color: alert.severity === 'high' ? 'var(--accent-red)' :
                             alert.severity === 'medium' ? 'var(--accent-amber)' : 'var(--accent-blue)',
                      flexShrink: 0,
                    }}
                  />
                  <div className="alert-card-body">
                    <div className="alert-card-title">{alert.note}</div>
                    <div className="alert-card-meta">
                      <span className={`badge badge-${alert.severity === 'high' ? 'critical' : alert.severity === 'medium' ? 'warning' : 'info'}`}>
                        {alert.severity === 'high' ? 'Critical' : alert.severity === 'medium' ? 'Warning' : 'Info'}
                      </span>
                      <span>{alert.asset_name || alert.asset_id}</span>
                      <span>·</span>
                      <span>{timeAgo(alert.timestamp)}</span>
                    </div>
                  </div>
                </div>
                <button
                  className="btn btn-ghost alert-ask"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/copilot?q=What does this alert mean: ${alert.note} for ${alert.asset_id}?`);
                  }}
                >
                  <Bot size={14} /> Ask AI
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}

function timeAgo(ts) {
  const diff = Date.now() - new Date(ts).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
