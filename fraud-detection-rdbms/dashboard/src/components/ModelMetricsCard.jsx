function percent(value) {
  return value === null || value === undefined ? 'N/A' : `${(Number(value) * 100).toFixed(1)}%`;
}

export default function ModelMetricsCard({ metrics }) {
  const items = [
    ['Accuracy', percent(metrics.accuracy)],
    ['Precision', percent(metrics.precision)],
    ['Recall', percent(metrics.recall)],
    ['F1', percent(metrics.f1)],
    ['ROC AUC', percent(metrics.roc_auc)],
    ['Rows', Number(metrics.training_rows || 0).toLocaleString()]
  ];

  return (
    <section className="panel metrics-panel">
      <h2>Model Metrics</h2>
      <div className="metrics-list">
        {items.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

