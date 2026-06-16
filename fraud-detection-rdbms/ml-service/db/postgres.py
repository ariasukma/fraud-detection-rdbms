import os

import psycopg2

from .base import BaseAdapter

QUERIES = {
    "training": "SELECT * FROM transactions WHERE is_fraud IS NOT NULL",
    "pending": "SELECT * FROM transactions WHERE prediction_status = 'PENDING' ORDER BY created_at ASC LIMIT %s",
    "update_prediction": "UPDATE transactions SET is_fraud = %s, fraud_type = %s, fraud_score = %s, prediction_status = 'PREDICTED', predicted_at = %s WHERE id = %s AND prediction_status = 'PENDING'",
    "summary": "SELECT COUNT(*) AS total_transactions, SUM(CASE WHEN is_fraud = TRUE THEN 1 ELSE 0 END) AS fraud_count, SUM(CASE WHEN is_fraud = FALSE THEN 1 ELSE 0 END) AS normal_count, AVG(fraud_score) AS avg_fraud_score FROM transactions",
    "latest": "SELECT * FROM transactions ORDER BY created_at DESC LIMIT %s",
    "timeseries": "SELECT DATE_TRUNC('minute', created_at) AS bucket, SUM(CASE WHEN is_fraud = TRUE THEN 1 ELSE 0 END) AS fraud, SUM(CASE WHEN is_fraud = FALSE THEN 1 ELSE 0 END) AS normal FROM transactions GROUP BY bucket ORDER BY bucket DESC LIMIT 60",
    "fraud_types": "SELECT fraud_type, COUNT(*) AS count FROM transactions WHERE fraud_type IS NOT NULL GROUP BY fraud_type ORDER BY count DESC"
}


def create_adapter():
    def connect():
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME", "fraud_db"),
            user=os.getenv("DB_USER", "fraud_user"),
            password=os.getenv("DB_PASSWORD")
        )
    return BaseAdapter(connect, QUERIES)

