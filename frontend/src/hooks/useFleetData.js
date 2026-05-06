import { useState, useEffect, useCallback, useRef } from 'react';
import { fleet, ai } from '../api/client';

/** Generic data-fetching hook */
export function useApi(fetcher, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      setData(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, deps);

  useEffect(() => { load(); }, [load]);

  return { data, loading, error, reload: load };
}

/** Fleet summary hook */
export function useFleetSummary() {
  return useApi(() => fleet.summary());
}

/** Vehicles list hook */
export function useVehicles(params = {}) {
  return useApi(() => fleet.vehicles(params), [JSON.stringify(params)]);
}

/** Single vehicle hook */
export function useVehicle(id) {
  return useApi(() => fleet.vehicle(id), [id]);
}

/** Alerts hook */
export function useAlerts(params = {}) {
  return useApi(() => fleet.alerts(params), [JSON.stringify(params)]);
}

/** Metrics hook */
export function useMetrics(params = {}) {
  return useApi(() => fleet.metrics(params), [JSON.stringify(params)]);
}

/** Maintenance hook */
export function useMaintenance() {
  return useApi(() => fleet.maintenance());
}

/** Drivers hook */
export function useDrivers() {
  return useApi(() => fleet.drivers());
}

/** Fuel report hook */
export function useFuelReport() {
  return useApi(() => fleet.fuelReport());
}

/** AI Copilot hook */
export function useCopilot() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const ask = useCallback(async (question, context = null) => {
    const userMsg = { role: 'user', content: question, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const resp = await ai.ask(question, context);
      const botMsg = {
        role: 'assistant',
        content: resp.answer,
        confidence: resp.confidence,
        sources: resp.sources_used,
        evidence: resp.evidence,
        caveats: resp.caveats,
        artifacts: resp.reasoning_artifacts,
        is_clarification: resp.is_clarification,
        timestamp: Date.now(),
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'error',
        content: e.message,
        timestamp: Date.now(),
      }]);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => setMessages([]), []);

  return { messages, loading, ask, clear };
}
