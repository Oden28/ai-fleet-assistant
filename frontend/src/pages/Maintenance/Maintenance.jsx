import { useState } from 'react';
import { useMaintenance } from '../../hooks/useFleetData';
import TopBar from '../../components/Layout/TopBar';
import { Wrench, AlertCircle, Clock } from 'lucide-react';
import './Maintenance.css';

export default function Maintenance() {
  const { data, loading } = useMaintenance();
  const [activeTab, setActiveTab] = useState('upcoming');

  const items = activeTab === 'upcoming' ? data?.upcoming : data?.completed;

  return (
    <>
      <TopBar title="Maintenance" />
      <div className="page page-with-topbar">
        <div className="tabs" style={{ marginBottom: 16 }}>
          <button className={`tab ${activeTab === 'upcoming' ? 'active' : ''}`} onClick={() => setActiveTab('upcoming')}>
            Upcoming ({data?.upcoming?.length || 0})
          </button>
          <button className={`tab ${activeTab === 'completed' ? 'active' : ''}`} onClick={() => setActiveTab('completed')}>
            Completed
          </button>
        </div>

        {loading ? (
          <div className="stagger">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 100, marginBottom: 8, borderRadius: 12 }} />
            ))}
          </div>
        ) : (
          <div className="stagger">
            {(items || []).map((item, i) => (
              <div key={i} className="card maint-card animate-fade-in">
                <div className="maint-header">
                  <span className="maint-asset">{item.asset_id}</span>
                  <span className={`badge badge-${item.severity === 'high' ? 'critical' : 'warning'}`}>
                    ● {item.severity === 'high' ? 'High' : 'Medium'}
                  </span>
                </div>
                <div className="maint-type">
                  <Wrench size={14} />
                  {item.maintenance_type}
                </div>
                <p className="maint-desc">{item.description}</p>
                <div className="maint-footer">
                  {item.due_status === 'overdue' ? (
                    <span className="maint-overdue"><AlertCircle size={12} /> Overdue</span>
                  ) : (
                    <span className="maint-upcoming"><Clock size={12} /> Upcoming</span>
                  )}
                  <span className="maint-name">{item.asset_name}</span>
                </div>
              </div>
            ))}
            {items?.length === 0 && (
              <div className="card" style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)' }}>
                No {activeTab} maintenance items
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
