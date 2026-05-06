import { useNavigate } from 'react-router-dom';
import TopBar from '../../components/Layout/TopBar';
import { Map, Users, BarChart3, LogOut, ChevronRight } from 'lucide-react';
import './More.css';

const menuItems = [
  { to: '/map', icon: Map, label: 'Live Map', desc: 'Track vehicles in real-time' },
  { to: '/drivers', icon: Users, label: 'Driver Scorecard', desc: 'Performance metrics' },
  { to: '/reports', icon: BarChart3, label: 'Reports', desc: 'Fuel, distance & utilization' },
];

export default function More() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('fleet_auth');
    localStorage.removeItem('fleet_user');
    navigate('/');
  };

  return (
    <>
      <TopBar title="More" />
      <div className="page page-with-topbar">
        <div className="stagger">
          {menuItems.map((item) => (
            <div key={item.to} className="card more-item animate-fade-in" onClick={() => navigate(item.to)}>
              <div className="more-icon-wrap">
                <item.icon size={20} />
              </div>
              <div className="more-info">
                <span className="more-label">{item.label}</span>
                <span className="more-desc">{item.desc}</span>
              </div>
              <ChevronRight size={18} className="more-chevron" />
            </div>
          ))}
        </div>

        <button className="btn btn-secondary more-logout" onClick={handleLogout}>
          <LogOut size={16} /> Sign Out
        </button>
      </div>
    </>
  );
}
