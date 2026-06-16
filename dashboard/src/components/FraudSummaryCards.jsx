function formatNumber(value) {
  return Number(value || 0).toLocaleString();
}

export default function FraudSummaryCards({ summary }) {
  const fraud = Number(summary.fraud_count || 0);
  const total = Number(summary.total_transactions || 0);
  const rate = total ? ((fraud / total) * 100).toFixed(2) : '0.00';
  const cards = [
    ['Total', formatNumber(summary.total_transactions)],
    ['Fraud', formatNumber(summary.fraud_count)],
    ['Normal', formatNumber(summary.normal_count)],
    ['Fraud Rate', `${rate}%`]
  ];

  return (
    <section className="summary-grid">
      {cards.map(([label, value]) => (
        <div className="metric-card" key={label}>
          <span>{label}</span>
          <strong className={label === 'Fraud' ? 'fraud-text' : label === 'Normal' ? 'normal-text' : ''}>{value}</strong>
        </div>
      ))}
    </section>
  );
}

