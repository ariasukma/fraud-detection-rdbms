const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function get(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json();
}

export function fetchDashboardData() {
  return Promise.all([
    get('/api/summary'),
    get('/api/latest-transactions'),
    get('/api/fraud-timeseries'),
    get('/api/fraud-types'),
    get('/api/model-metrics')
  ]).then(([summary, latest, timeseries, fraudTypes, metrics]) => ({
    summary,
    latest,
    timeseries: [...timeseries].reverse(),
    fraudTypes,
    metrics
  }));
}

