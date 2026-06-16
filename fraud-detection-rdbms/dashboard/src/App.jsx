import { useEffect, useState } from 'react';
import { fetchDashboardData } from './services/api.js';
import FraudSummaryCards from './components/FraudSummaryCards.jsx';
import FraudRealtimeChart from './components/FraudRealtimeChart.jsx';
import FraudTypeChart from './components/FraudTypeChart.jsx';
import LatestTransactionsTable from './components/LatestTransactionsTable.jsx';
import ModelMetricsCard from './components/ModelMetricsCard.jsx';

const emptyData = {
  summary: {},
  latest: [],
  timeseries: [],
  fraudTypes: [],
  metrics: {}
};

export default function App() {
  const [data, setData] = useState(emptyData);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const next = await fetchDashboardData();
        if (!cancelled) {
          setData(next);
          setError('');
          setLastUpdated(new Date());
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      }
    }
    load();
    const interval = setInterval(load, 1000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>Fraud Detection</h1>
          <p>Realtime RDBMS monitoring dashboard</p>
        </div>
        <div className="status-pill">
          {error ? 'API error' : `Updated ${lastUpdated ? lastUpdated.toLocaleTimeString() : '--:--:--'}`}
        </div>
      </header>
      {error && <div className="error-banner">{error}</div>}
      <FraudSummaryCards summary={data.summary} />
      <section className="dashboard-grid">
        <FraudRealtimeChart data={data.timeseries} />
        <FraudTypeChart data={data.fraudTypes} />
        <ModelMetricsCard metrics={data.metrics} />
      </section>
      <LatestTransactionsTable rows={data.latest} />
    </main>
  );
}

