import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import './TopBar.css';

export default function TopBar({ title, showBack = false, right = null }) {
  const navigate = useNavigate();

  return (
    <header className="topbar">
      <div className="topbar-inner">
        <div className="topbar-left">
          {showBack && (
            <button className="topbar-back" onClick={() => navigate(-1)}>
              <ArrowLeft size={20} />
            </button>
          )}
          <h1 className="topbar-title">{title}</h1>
        </div>
        {right && <div className="topbar-right">{right}</div>}
      </div>
    </header>
  );
}
