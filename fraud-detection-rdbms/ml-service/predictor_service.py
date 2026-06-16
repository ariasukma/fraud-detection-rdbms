import logging
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib

from db import create_db_adapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MODEL_PATH = Path("models/fraud_model.pkl")
MAX_ROWS_PER_CYCLE = 1000


def explain(row):
    if row["amount"] > row["avg_transaction_amount_30d"] * 5:
        return "HIGH_AMOUNT_ANOMALY"
    if bool(row["is_new_device"]) and row["device_change_count_24h"] >= 3:
        return "NEW_DEVICE_FRAUD"
    if row["failed_login_count_24h"] >= 5 and bool(row["password_change_recently"]):
        return "ACCOUNT_TAKEOVER"
    if bool(row["beneficiary_is_new"]) and row["beneficiary_age_days"] <= 3:
        return "NEW_BENEFICIARY_FRAUD"
    if row["transaction_count_1h"] >= 8 or row["transaction_count_24h"] >= 30:
        return "VELOCITY_FRAUD"
    if row["distance_from_last_location_km"] > 1200 and row["minutes_since_last_transaction"] <= 15:
        return "GEO_ANOMALY"
    if bool(row["is_cross_border"]) and row["destination_country"] in {"North Korea", "Iran", "Syria", "Russia"}:
        return "CROSS_BORDER_HIGH_RISK"
    if bool(row["is_vpn"]) or bool(row["is_proxy"]) or row["ip_risk_score"] >= 80:
        return "VPN_PROXY_FRAUD"
    if row["merchant_risk_level"] == "HIGH":
        return "HIGH_RISK_MERCHANT"
    if row["days_since_last_transaction"] >= 180 and row["amount"] > row["avg_transaction_amount_30d"] * 3:
        return "DORMANT_ACCOUNT_FRAUD"
    return "MODEL_DETECTED_FRAUD"


def main():
    if not MODEL_PATH.exists():
        raise RuntimeError("Model artifact not found. Run python train_model.py first.")
    artifact = joblib.load(MODEL_PATH)
    pipeline = artifact["pipeline"]
    features = artifact["features"]
    boolean_features = artifact["boolean_features"]
    adapter = create_db_adapter()
    logger.info("Predictor service started")

    while True:
        try:
            pending = adapter.fetch_pending_transactions(limit=MAX_ROWS_PER_CYCLE)
            if pending.empty:
                time.sleep(1)
                continue
            pending[boolean_features] = pending[boolean_features].fillna(False).astype(int)
            probabilities = pipeline.predict_proba(pending[features])[:, 1]
            predictions = (probabilities >= 0.5).astype(int)
            for position, (_, row) in enumerate(pending.iterrows()):
                fraud_score = round(float(probabilities[position]), 4)
                is_fraud = bool(predictions[position])
                fraud_type = explain(row) if is_fraud else None
                adapter.update_prediction(row["id"], is_fraud, fraud_type, fraud_score, datetime.now(timezone.utc))
            logger.info("Predicted %s pending transactions", len(pending))
        except Exception:
            logger.exception("Prediction cycle failed")
        time.sleep(1)


if __name__ == "__main__":
    main()
