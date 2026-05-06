import { useDrivers } from '../../hooks/useFleetData';
import TopBar from '../../components/Layout/TopBar';
import Gauge from '../../components/Charts/Gauge';
import { TrendingUp, TrendingDown, Award } from 'lucide-react';
import './DriverScorecard.css';

export default function DriverScorecard() {
  const { data, loading } = useDrivers();

  if (loading || !data) {
    return (
      <>
        <TopBar title="Driver Scorecard" showBack />
        <div className="page page-with-topbar">
          <div className="skeleton" style={{ height: 200, borderRadius: 12 }} />
        </div>
      </>
    );
  }

  const topDriver = data.drivers[0];

  return (
    <>
      <TopBar title="Driver Scorecard" showBack />
      <div className="page page-with-topbar">
        {/* Fleet Average */}
        <div className="card ds-hero animate-fade-in">
          <div className="ds-hero-row">
            <Gauge value={data.fleet_average} size={130} />
            <div className="ds-hero-info">
              <h3>Fleet Average</h3>
              <p className="ds-hero-grade">
                {data.fleet_average >= 70 ? 'Good' : data.fleet_average >= 40 ? 'Fair' : 'Needs Work'}
              </p>
              <div className="ds-hero-stats">
                <span><Award size={14} /> Top: {topDriver?.asset_name} ({topDriver?.composite_score})</span>
              </div>
            </div>
          </div>
        </div>

        {/* Driver List */}
        <div className="stagger" style={{ marginTop: 16 }}>
          {data.drivers.map((d, i) => (
            <div key={d.asset_id} className="card ds-driver animate-fade-in" style={{ marginBottom: 8 }}>
              <div className="ds-driver-header">
                <div className="ds-driver-rank">#{i + 1}</div>
                <div className="ds-driver-info">
                  <span className="ds-driver-name">{d.asset_name}</span>
                  <span className="ds-driver-region">{d.region}</span>
                </div>
                <div className={`ds-grade ds-grade-${d.grade.toLowerCase()}`}>{d.grade}</div>
                <div className="ds-score">{d.composite_score}</div>
              </div>
              <div className="ds-bars">
                <div className="ds-bar-item">
                  <span>Idle</span>
                  <div className="ds-bar-track">
                    <div className="ds-bar-fill" style={{ width: `${d.idle_score}%`, background: 'var(--accent-blue)' }} />
                  </div>
                  <span>{d.idle_score}</span>
                </div>
                <div className="ds-bar-item">
                  <span>Trips</span>
                  <div className="ds-bar-track">
                    <div className="ds-bar-fill" style={{ width: `${d.trip_score}%`, background: 'var(--accent-green)' }} />
                  </div>
                  <span>{d.trip_score}</span>
                </div>
                <div className="ds-bar-item">
                  <span>Efficiency</span>
                  <div className="ds-bar-track">
                    <div className="ds-bar-fill" style={{ width: `${d.efficiency_score}%`, background: 'var(--accent-purple)' }} />
                  </div>
                  <span>{d.efficiency_score}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
