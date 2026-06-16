import logging
from contextlib import closing

import pandas as pd

logger = logging.getLogger(__name__)


class BaseAdapter:
    def __init__(self, connection_factory, queries, bool_style="native"):
        self.connection_factory = connection_factory
        self.queries = queries
        self.bool_style = bool_style

    def _bool(self, value):
        if value is None:
            return None
        return int(value) if self.bool_style in {"int", "bit"} else bool(value)

    def fetch_training_data(self):
        with closing(self.connection_factory()) as conn:
            return self._normalize_df(pd.read_sql(self.queries["training"], conn))

    def fetch_pending_transactions(self, limit=1000):
        with closing(self.connection_factory()) as conn:
            return self._normalize_df(pd.read_sql(self.queries["pending"], conn, params=self._limit_params(limit)))

    def update_prediction(self, row_id, is_fraud, fraud_type, fraud_score, predicted_at):
        with closing(self.connection_factory()) as conn:
            cursor = conn.cursor()
            try:
                params = self._update_params(row_id, is_fraud, fraud_type, fraud_score, predicted_at)
                cursor.execute(self.queries["update_prediction"], params)
                conn.commit()
            except Exception:
                conn.rollback()
                logger.exception("Failed to update prediction for row id %s", row_id)
                raise
            finally:
                cursor.close()

    def get_summary(self):
        return self._read_one("summary")

    def get_latest_transactions(self, limit=25):
        return self._read_many("latest", self._limit_params(limit))

    def get_fraud_timeseries(self):
        return self._read_many("timeseries")

    def get_fraud_types(self):
        return self._read_many("fraud_types")

    def _read_one(self, key):
        rows = self._read_many(key)
        return rows[0] if rows else {}

    def _read_many(self, key, params=None):
        with closing(self.connection_factory()) as conn:
            df = pd.read_sql(self.queries[key], conn, params=params)
            df = self._normalize_df(df)
            return df.where(pd.notnull(df), None).to_dict(orient="records")

    def _normalize_df(self, df):
        df.columns = [column.lower() for column in df.columns]
        return df

    def _limit_params(self, limit):
        return (int(limit),)

    def _update_params(self, row_id, is_fraud, fraud_type, fraud_score, predicted_at):
        return (self._bool(is_fraud), fraud_type, float(fraud_score), predicted_at, int(row_id))
