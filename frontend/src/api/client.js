/**
 * API client for the Fleet Intelligence backend.
 * All fetch calls are centralized here.
 */

const API_BASE = 'http://localhost:8000/api';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }
  return res.json();
}

// ── AI Copilot ────────────────────────────────────────────────
export const ai = {
  ask: (question, context = null) =>
    request('/ask', { method: 'POST', body: JSON.stringify({ question, context }) }),

  queryDocs: (question) =>
    request('/query-docs', { method: 'POST', body: JSON.stringify({ question }) }),

  queryData: (question) =>
    request('/query-data', { method: 'POST', body: JSON.stringify({ question }) }),
};

// ── Fleet Data ────────────────────────────────────────────────
export const fleet = {
  summary: () => request('/fleet/summary'),

  vehicles: (params = {}) => {
    const qs = new URLSearchParams();
    if (params.region) qs.set('region', params.region);
    if (params.asset_type) qs.set('asset_type', params.asset_type);
    if (params.status) qs.set('status', params.status);
    if (params.search) qs.set('search', params.search);
    const q = qs.toString();
    return request(`/fleet/vehicles${q ? '?' + q : ''}`);
  },

  vehicle: (id) => request(`/fleet/vehicles/${id}`),

  alerts: (params = {}) => {
    const qs = new URLSearchParams();
    if (params.severity) qs.set('severity', params.severity);
    if (params.alert_type) qs.set('alert_type', params.alert_type);
    if (params.asset_id) qs.set('asset_id', params.asset_id);
    const q = qs.toString();
    return request(`/fleet/alerts${q ? '?' + q : ''}`);
  },

  metrics: (params = {}) => {
    const qs = new URLSearchParams();
    if (params.asset_id) qs.set('asset_id', params.asset_id);
    if (params.date) qs.set('date', params.date);
    const q = qs.toString();
    return request(`/fleet/metrics${q ? '?' + q : ''}`);
  },

  maintenance: () => request('/fleet/maintenance'),
  drivers: () => request('/fleet/drivers'),
  fuelReport: () => request('/fleet/reports/fuel'),
  health: () => request('/health'),
};

// ── WebSocket ─────────────────────────────────────────────────
export function createCopilotSocket(onMessage) {
  const ws = new WebSocket('ws://localhost:8000/api/ws/copilot');
  ws.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      onMessage(data);
    } catch {
      console.error('Invalid WS message', e.data);
    }
  };
  return ws;
}
