import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import BottomNav from './components/Layout/BottomNav';
import Login from './pages/Login/Login';
import Dashboard from './pages/Dashboard/Dashboard';
import LiveMap from './pages/LiveMap/LiveMap';
import Vehicles from './pages/Vehicles/Vehicles';
import VehicleDetail from './pages/VehicleDetail/VehicleDetail';
import Alerts from './pages/Alerts/Alerts';
import Maintenance from './pages/Maintenance/Maintenance';
import DriverScorecard from './pages/DriverScorecard/DriverScorecard';
import Reports from './pages/Reports/Reports';
import Copilot from './pages/Copilot/Copilot';
import More from './pages/More/More';
import TopBar from './components/Layout/TopBar';

function ProtectedRoute({ children }) {
  const auth = localStorage.getItem('fleet_auth');
  if (!auth) return <Navigate to="/" replace />;
  return children;
}

function DashboardWithTopBar() {
  return (
    <>
      <TopBar title="Dashboard" />
      <Dashboard />
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />

        <Route path="/dashboard" element={
          <ProtectedRoute><DashboardWithTopBar /></ProtectedRoute>
        } />
        <Route path="/map" element={
          <ProtectedRoute><LiveMap /></ProtectedRoute>
        } />
        <Route path="/vehicles" element={
          <ProtectedRoute><Vehicles /></ProtectedRoute>
        } />
        <Route path="/vehicles/:id" element={
          <ProtectedRoute><VehicleDetail /></ProtectedRoute>
        } />
        <Route path="/alerts" element={
          <ProtectedRoute><Alerts /></ProtectedRoute>
        } />
        <Route path="/maintenance" element={
          <ProtectedRoute><Maintenance /></ProtectedRoute>
        } />
        <Route path="/drivers" element={
          <ProtectedRoute><DriverScorecard /></ProtectedRoute>
        } />
        <Route path="/reports" element={
          <ProtectedRoute><Reports /></ProtectedRoute>
        } />
        <Route path="/copilot" element={
          <ProtectedRoute><Copilot /></ProtectedRoute>
        } />
        <Route path="/more" element={
          <ProtectedRoute><More /></ProtectedRoute>
        } />
      </Routes>
      <BottomNav />
    </BrowserRouter>
  );
}
