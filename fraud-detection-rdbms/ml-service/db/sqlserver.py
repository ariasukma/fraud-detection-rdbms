import os

import pyodbc

from .base import BaseAdapter

QUERIES = {
    "training": "SELECT * FROM transactions WHERE is_fraud IS NOT NULL",
    "pending": "SELECT TOP (?) * FROM transactions WHERE prediction_status = 'PENDING' ORDER BY created_at ASC",
    "update_prediction": "UPDATE transactions SET is_fraud = ?, fraud_type = ?, fraud_score = ?, prediction_status = 'PREDICTED', predicted_at = ? WHERE id = ? AND prediction_status = 'PENDING'",
    "summary": "SELECT COUNT(*) AS total_transactions, SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count, SUM(CASE WHEN is_fraud = 0 THEN 1 ELSE 0 END) AS normal_count, AVG(fraud_score) AS avg_fraud_score FROM transactions",
    "latest": "SELECT TOP (?) * FROM transactions ORDER BY created_at DESC",
    "timeseries": "SELECT TOP (60) DATEADD(minute, DATEDIFF(minute, 0, created_at), 0) AS bucket, SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) AS fraud, SUM(CASE WHEN is_fraud = 0 THEN 1 ELSE 0 END) AS normal FROM transactions GROUP BY DATEADD(minute, DATEDIFF(minute, 0, created_at), 0) ORDER BY bucket DESC",
    "fraud_types": "SELECT fraud_type, COUNT(*) AS count FROM transactions WHERE fraud_type IS NOT NULL GROUP BY fraud_type ORDER BY count DESC"
}


def create_adapter():
    def connect():
        driver = os.getenv("ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
        conn_str = (
            f"DRIVER={{{driver}}};SERVER={os.getenv('DB_HOST', 'localhost')},{os.getenv('DB_PORT', '1433')};"
            f"DATABASE={os.getenv('DB_NAME', 'fraud_db')};UID={os.getenv('DB_USER', 'fraud_user')};"
            f"PWD={os.getenv('DB_PASSWORD')};TrustServerCertificate=yes;Encrypt=no"
        )
        return pyodbc.connect(conn_str)
    return BaseAdapter(connect, QUERIES, bool_style="bit")

