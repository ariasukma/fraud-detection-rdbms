function money(row) {
  return `${row.currency || ''} ${Number(row.amount || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

export default function LatestTransactionsTable({ rows }) {
  return (
    <section className="panel table-panel">
      <h2>Latest Transactions</h2>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Time</th>
              <th>Customer</th>
              <th>Amount</th>
              <th>Channel</th>
              <th>Risk</th>
              <th>Status</th>
              <th>Fraud Type</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className={row.is_fraud ? 'fraud-row' : ''}>
                <td>{row.created_at ? new Date(row.created_at).toLocaleTimeString() : '-'}</td>
                <td>{row.customer_name}</td>
                <td>{money(row)}</td>
                <td>{row.transaction_channel}</td>
                <td>{row.customer_risk_level}</td>
                <td>{row.prediction_status}</td>
                <td>{row.fraud_type || '-'}</td>
                <td>{row.fraud_score === null || row.fraud_score === undefined ? '-' : Number(row.fraud_score).toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

