import { useState } from 'react';
import { useFuelReport, useMetrics } from '../../hooks/useFleetData';
import TopBar from '../../components/Layout/TopBar';
import KpiCard from '../../components/Charts/KpiCard';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts';
import { MapPin, Fuel, Clock, Activity } from 'lucide-react';
import './Reports.css';

export default function Reports() {
  const [activeTab, setActiveTab] = useState('summary');
  const { data: fuel, loading: fuelLoading } = useFuelReport();
  const { data: metricsData } = useMetrics();

  const tabs = ['Summary', 'Trips', 'Fuel', 'Maintenance'];

  return (
    <>
      <TopBar title="Reports" showBack />
      <div className="page page-with-topbar">
        <div className="tabs" style={{ marginBottom: 16 }}>
          {tabs.map((t) => (
            <button key={t} className={`tab ${activeTab === t.toLowerCase() ? 'active' : ''}`}
              onClick={() => setActiveTab(t.toLowerCase())}>{t}</button>
          ))}
        </div>

        {activeTab === 'summary' && (
          <div className="animate-fade-in">
            <div className="card-grid" style={{ marginBottom: 16 }}>
              <KpiCard icon={MapPin} label="Total Distance" value="2,896 km" trend="↑ 12.5%" color="blue" />
              <KpiCard icon={Fuel} label="Total Fuel Used" value="245 L" trend="↓ 5.2%" color="green" />
              <KpiCard icon={Clock} label="Total Idle Time" value="18h 45m" trend="↑ 2.3%" color="amber" />
              <KpiCard icon={Activity} label="Fleet Utilization" value="72%" trend="↑ 4.5%" color="purple" />
            </div>
            <div className="card" style={{ marginBottom: 16 }}>
              <h3 className="rpt-chart-title">Fuel Efficiency by Region</h3>
              {fuel && (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={fuel.by_region}>
                    <XAxis dataKey="region" stroke="var(--text-muted)" fontSize={12} />
                    <YAxis stroke="var(--text-muted)" fontSize={12} />
                    <Tooltip
                      contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 8 }}
                      labelStyle={{ color: 'var(--text-primary)' }}
                    />
                    <Bar dataKey="avg_km_per_engine_hour" fill="var(--accent-blue)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        )}

        {activeTab === 'fuel' && fuel && (
          <div className="animate-fade-in">
            <div className="card" style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <h3 className="rpt-chart-title">Avg Fuel Efficiency</h3>
                <span style={{ fontSize: 24, fontWeight: 800 }}>{fuel.fleet_average_efficiency} <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>km/eh</span></span>
              </div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={fuel.by_asset}>
                  <XAxis dataKey="asset_id" stroke="var(--text-muted)" fontSize={11} angle={-45} textAnchor="end" height={50} />
                  <YAxis stroke="var(--text-muted)" fontSize={12} />
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 8 }} />
                  <Bar dataKey="km_per_engine_hour" fill="var(--accent-green)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="stagger">
              {fuel.by_asset.map((a) => (
                <div key={a.asset_id} className="card rpt-fuel-row" style={{ marginBottom: 6 }}>
                  <span className="rpt-fuel-id">{a.asset_id}</span>
                  <span className="rpt-fuel-name">{a.asset_name}</span>
                  <span className="rpt-fuel-val">{a.km_per_engine_hour} km/eh</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'trips' && (
          <div className="card animate-fade-in">
            <h3 className="rpt-chart-title">Trip Trends</h3>
            {metricsData && (
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={metricsData.metrics}>
                  <CartesianGrid stroke="var(--border-subtle)" strokeDasharray="3 3" />
                  <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} />
                  <YAxis stroke="var(--text-muted)" fontSize={12} />
                  <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-default)', borderRadius: 8 }} />
                  <Line type="monotone" dataKey="trip_count" stroke="var(--accent-blue)" strokeWidth={2} dot={{ fill: 'var(--accent-blue)' }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        )}

        {activeTab === 'maintenance' && (
          <div className="card animate-fade-in">
            <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: 32 }}>
              Maintenance report data coming soon. Use the Maintenance tab for current items.
            </p>
          </div>
        )}
      </div>
    </>
  );
}
