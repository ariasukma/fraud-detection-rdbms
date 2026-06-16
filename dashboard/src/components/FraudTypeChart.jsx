import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export default function FraudTypeChart({ data }) {
  return (
    <section className="panel chart-panel">
      <h2>Fraud Types</h2>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#d8dee9" />
          <XAxis dataKey="fraud_type" tick={{ fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={80} />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="count" fill="#dc2626" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </section>
  );
}

