import pg from 'pg';

const { Pool } = pg;
const columns = ['transaction_id','customer_id','customer_name','email','phone_number','amount','currency','transaction_type','transaction_channel','transaction_time','hour_of_day','day_of_week','account_age_days','kyc_status','customer_risk_level','merchant_id','merchant_category','merchant_country','merchant_risk_level','device_id','device_type','device_os','is_new_device','device_change_count_24h','ip_address','ip_country','ip_city','is_vpn','is_proxy','ip_risk_score','source_country','destination_country','is_cross_border','avg_transaction_amount_30d','transaction_count_1h','transaction_count_24h','failed_login_count_24h','password_change_recently','beneficiary_is_new','beneficiary_age_days','distance_from_last_location_km','minutes_since_last_transaction','days_since_last_transaction','is_fraud','fraud_type','fraud_score','prediction_status','predicted_at','created_at'];

export function createAdapter() {
  const pool = new Pool({
    host: process.env.DB_HOST || 'localhost',
    port: Number(process.env.DB_PORT || 26257),
    database: process.env.DB_NAME || 'fraud_db',
    user: process.env.DB_USER || 'fraud_user',
    password: process.env.DB_PASSWORD || undefined,
    ssl: false
  });
  return {
    async insertTransactions(rows) {
      if (!rows.length) return;
      const values = rows.flatMap((row) => columns.map((column) => row[column]));
      const placeholders = rows.map((_, rowIndex) => `(${columns.map((__, colIndex) => `$${rowIndex * columns.length + colIndex + 1}`).join(',')})`).join(',');
      await pool.query(`INSERT INTO transactions (${columns.join(',')}) VALUES ${placeholders}`, values);
    },
    close: () => pool.end()
  };
}

