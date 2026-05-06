import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Truck, Eye, EyeOff } from 'lucide-react';
import './Login.css';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = (e) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      localStorage.setItem('fleet_auth', 'true');
      localStorage.setItem('fleet_user', JSON.stringify({
        name: 'Joshua',
        email: email || 'joshua@powerfleet.com',
      }));
      navigate('/dashboard');
    }, 800);
  };

  return (
    <div className="login-page">
      <div className="login-bg-gradient" />
      <div className="login-content animate-fade-in">
        <div className="login-brand">
          <div className="login-logo">
            <Truck size={32} />
          </div>
          <h1 className="login-title">Powerfleet</h1>
          <p className="login-subtitle">AI Fleet Intelligence</p>
        </div>

        <div className="login-welcome">
          <h2>Welcome back</h2>
          <p>Sign in to continue</p>
        </div>

        <form className="login-form" onSubmit={handleLogin}>
          <div className="login-field">
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              className="input"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="login-field">
            <label htmlFor="login-password">Password</label>
            <div className="login-password-wrap">
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                className="input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                className="login-eye"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            <a href="#" className="login-forgot">Forgot password?</a>
          </div>

          <button
            type="submit"
            className={`btn btn-primary login-submit ${loading ? 'loading' : ''}`}
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="login-signup">
          Don't have an account? <a href="#">Sign up</a>
        </p>
      </div>
    </div>
  );
}
