import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useVehicles } from '../../hooks/useFleetData';
import { Search, Battery, Gauge, MapPin } from 'lucide-react';
import TopBar from '../../components/Layout/TopBar';
import './Vehicles.css';

export default function Vehicles() {
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState('all');
  const navigate = useNavigate();

  const statusMap = { all: undefined, active: undefined, inactive: undefined };
  const { data, loading } = useVehicles({
    search: search || undefined,
    status: activeTab === 'critical' ? 'critical' : activeTab === 'warning' ? 'warning' : undefined,
  });

  const vehicles = data?.vehicles || [];

  const tabs = [
    { id: 'all', label: 'All', count: data?.total || 0 },
    { id: 'critical', label: 'Critical' },
    { id: 'warning', label: 'Warning' },
  ];

  const filtered = activeTab === 'all' ? vehicles :
    vehicles.filter(v => v.status === activeTab);

  return (
    <>
      <TopBar title="Vehicles" />
      <div className="page page-with-topbar">
        {/* Search */}
        <div className="vehicles-search animate-fade-in">
          <Search size={18} className="vehicles-search-icon" />
          <input
            className="input vehicles-search-input"
            placeholder="Search vehicles..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {/* Tabs */}
        <div className="tabs" style={{ marginBottom: 16 }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
              {tab.count != null && <span className="tab-count">({tab.count})</span>}
            </button>
          ))}
        </div>

        {/* Vehicle List */}
        {loading ? (
          <div className="stagger">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 80, marginBottom: 8, borderRadius: 12 }} />
            ))}
          </div>
        ) : (
          <div className="stagger">
            {filtered.map((v) => (
              <div
                key={v.asset_id}
                className="card vehicle-card animate-fade-in"
                onClick={() => navigate(`/vehicles/${v.asset_id}`)}
              >
                <div className="vehicle-card-header">
                  <div className="vehicle-card-id">
                    <span className={`status-dot ${v.status}`} />
                    <span className="vehicle-name">{v.asset_id}</span>
                  </div>
                  <span className={`badge badge-${v.status === 'critical' ? 'critical' : v.status === 'warning' ? 'warning' : 'success'}`}>
                    ● {v.status}
                  </span>
                </div>
                <div className="vehicle-card-metrics">
                  <div className="vehicle-metric">
                    <Gauge size={13} />
                    <span>{v.latest_idle_minutes ?? '--'} min idle</span>
                  </div>
                  <div className="vehicle-metric">
                    <Battery size={13} />
                    <span>{v.latest_battery_voltage ?? '--'}V</span>
                  </div>
                  <div className="vehicle-metric">
                    <MapPin size={13} />
                    <span>{v.region}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
