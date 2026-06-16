import os

import oracledb

from .base import BaseAdapter

QUERIES = {
    "training": "SELECT * FROM transactions WHERE is_fraud IS NOT NULL",
    "pending": "SELECT * FROM (SELECT * FROM transactions WHERE prediction_status = 'PENDING' ORDER BY created_at ASC) WHERE ROWNUM <= :limit",
    "update_prediction": "UPDATE transactions SET is_fraud = :is_fraud, fraud_type = :fraud_type, fraud_score = :fraud_score, prediction_status = 'PREDICTED', predicted_at = :predicted_at WHERE id = :id AND prediction_status = 'PENDING'",
    "summary": "SELECT COUNT(*) AS total_transactions, SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) AS fraud_count, SUM(CASE WHEN is_fraud = 0 THEN 1 ELSE 0 END) AS normal_count, AVG(fraud_score) AS avg_fraud_score FROM transactions",
    "latest": "SELECT * FROM (SELECT * FROM transactions ORDER BY created_at DESC) WHERE ROWNUM <= :limit",
    "timeseries": "SELECT TRUNC(created_at, 'MI') AS bucket, SUM(CASE WHEN is_fraud = 1 THEN 1 ELSE 0 END) AS fraud, SUM(CASE WHEN is_fraud = 0 THEN 1 ELSE 0 END) AS normal FROM transactions GROUP BY TRUNC(created_at, 'MI') ORDER BY bucket DESC FETCH FIRST 60 ROWS ONLY",
    "fraud_types": "SELECT fraud_type, COUNT(*) AS count FROM transactions WHERE fraud_type IS NOT NULL GROUP BY fraud_type ORDER BY count DESC"
}


class OracleAdapter(BaseAdapter):
    def _limit_params(self, limit):
        return {"limit": int(limit)}

    def _update_params(self, row_id, is_fraud, fraud_type, fraud_score, predicted_at):
        return {"is_fraud": self._bool(is_fraud), "fraud_type": fraud_type, "fraud_score": float(fraud_score), "predicted_at": predicted_at, "id": int(row_id)}


def get_dsn():
    oracle_dsn = os.getenv("ORACLE_DSN")
    if oracle_dsn:
        return oracle_dsn
    return f"{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '1521')}/{os.getenv('DB_NAME', 'FREEPDB1')}"


def create_adapter():
    def connect():
        return oracledb.connect(
            user=os.getenv("DB_USER", "fraud_user"),
            password=os.getenv("DB_PASSWORD"),
            dsn=get_dsn()
        )
    return OracleAdapter(connect, QUERIES, bool_style="int")
