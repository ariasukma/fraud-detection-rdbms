import mysql from 'mysql2/promise';

const columns = ['transaction_id','customer_id','customer_name','email','phone_number','amount','currency','transaction_type','transaction_channel','transaction_time','hour_of_day','day_of_week','account_age_days','kyc_status','customer_risk_level','merchant_id','merchant_category','merchant_country','merchant_risk_level','device_id','device_type','device_os','is_new_device','device_change_count_24h','ip_address','ip_country','ip_city','is_vpn','is_proxy','ip_risk_score','source_country','destination_country','is_cross_border','avg_transaction_amount_30d','transaction_count_1h','transaction_count_24h','failed_login_count_24h','password_change_recently','beneficiary_is_new','beneficiary_age_days','distance_from_last_location_km','minutes_since_last_transaction','days_since_last_transaction','is_fraud','fraud_type','fraud_score','prediction_status','predicted_at','created_at'];
const boolColumns = new Set(['is_new_device','is_vpn','is_proxy','is_cross_border','password_change_recently','beneficiary_is_new','is_fraud']);

function value(row, column) {
  return boolColumns.has(column) && row[column] !== null ? Number(row[column]) : row[column];
}

export function createAdapter() {
  const pool = mysql.createPool({
    host: process.env.DB_HOST || 'localhost',
    port: Number(process.env.DB_PORT || 3306),
    database: process.env.DB_NAME || 'fraud_db',
    user: process.env.DB_USER || 'fraud_user',
    password: process.env.DB_PASSWORD,
    waitForConnections: true,
    connectionLimit: 10
  });
  return {
    async insertTransactions(rows) {
      if (!rows.length) return;
      const values = rows.flatMap((row) => columns.map((column) => value(row, column)));
      const placeholders = rows.map(() => `(${columns.map(() => '?').join(',')})`).join(',');
      await pool.execute(`INSERT INTO transactions (${columns.join(',')}) VALUES ${placeholders}`, values);
    },
    close: () => pool.end()
  };
}

