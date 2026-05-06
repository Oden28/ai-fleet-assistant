import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Truck,
  Bell,
  Wrench,
  MoreHorizontal,
  Bot,
} from 'lucide-react';
import './BottomNav.css';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/vehicles', icon: Truck, label: 'Vehicles' },
  { to: '/alerts', icon: Bell, label: 'Alerts' },
  { to: '/maintenance', icon: Wrench, label: 'Maintenance' },
  { to: '/more', icon: MoreHorizontal, label: 'More' },
];

export default function BottomNav() {
  const location = useLocation();

  // Hide on login page
  if (location.pathname === '/' || location.pathname === '/login') return null;

  return (
    <nav className="bottom-nav">
      <div className="bottom-nav-inner">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `bottom-nav-item ${isActive ? 'active' : ''}`
            }
          >
            <Icon size={20} strokeWidth={isActive(to, location) ? 2.2 : 1.8} />
            <span>{label}</span>
          </NavLink>
        ))}
        <NavLink to="/copilot" className="bottom-nav-ai">
          <Bot size={20} />
          <span>Ask AI</span>
        </NavLink>
      </div>
    </nav>
  );
}

function isActive(to, location) {
  return location.pathname.startsWith(to);
}
