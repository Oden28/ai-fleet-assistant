import { useVehicles } from '../../hooks/useFleetData';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Search } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import TopBar from '../../components/Layout/TopBar';
import 'leaflet/dist/leaflet.css';
import './LiveMap.css';

// Fix Leaflet default icons
import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Generate deterministic positions based on asset region
const regionCoords = {
  North: { lat: -37.82, lng: 144.96 },
  South: { lat: -37.86, lng: 145.0 },
  East: { lat: -37.84, lng: 145.08 },
  West: { lat: -37.83, lng: 144.88 },
};

function getVehiclePosition(vehicle) {
  const base = regionCoords[vehicle.region] || regionCoords.North;
  // Offset each vehicle slightly within its region
  const hash = vehicle.asset_id.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
  return {
    lat: base.lat + (hash % 7 - 3) * 0.005,
    lng: base.lng + (hash % 5 - 2) * 0.008,
  };
}

export default function LiveMap() {
  const { data } = useVehicles();
  const [search, setSearch] = useState('');
  const navigate = useNavigate();
  const vehicles = data?.vehicles || [];

  const filtered = search
    ? vehicles.filter(v =>
        v.asset_id.toLowerCase().includes(search.toLowerCase()) ||
        v.asset_name.toLowerCase().includes(search.toLowerCase())
      )
    : vehicles;

  return (
    <>
      <TopBar title="Live Map" />
      <div className="livemap-container">
        <div className="livemap-search">
          <Search size={16} />
          <input
            placeholder="Search vehicles..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <MapContainer
          center={[-37.84, 144.97]}
          zoom={12}
          className="livemap-map"
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://carto.com">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          {filtered.map((v) => {
            const pos = getVehiclePosition(v);
            return (
              <Marker key={v.asset_id} position={[pos.lat, pos.lng]}>
                <Popup>
                  <div className="livemap-popup">
                    <strong>{v.asset_id}</strong> — {v.asset_name}
                    <br />
                    <span className={`badge badge-${v.status === 'critical' ? 'critical' : v.status === 'warning' ? 'warning' : 'success'}`} style={{ marginTop: 4, display: 'inline-block' }}>
                      {v.status}
                    </span>
                    <br />
                    <span style={{ fontSize: 12, color: '#999' }}>{v.region} · {v.device_model}</span>
                    <br />
                    <button
                      onClick={() => navigate(`/vehicles/${v.asset_id}`)}
                      style={{
                        marginTop: 6, padding: '4px 10px', background: '#3b82f6',
                        color: 'white', border: 'none', borderRadius: 6, fontSize: 12, cursor: 'pointer'
                      }}
                    >
                      View Details
                    </button>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>

        {/* Bottom vehicle strip */}
        <div className="livemap-strip">
          {filtered.slice(0, 6).map((v) => (
            <div key={v.asset_id} className="livemap-strip-card" onClick={() => navigate(`/vehicles/${v.asset_id}`)}>
              <span className={`status-dot ${v.status}`} />
              <span className="livemap-strip-id">{v.asset_id}</span>
              <span className="livemap-strip-meta">{v.latest_battery_voltage}V</span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
