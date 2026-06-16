import json
import logging
from pathlib import Path

import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, precision_recall_fscore_support, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from db import create_db_adapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MODEL_DIR = Path("models")
MODEL_PATH = MODEL_DIR / "fraud_model.pkl"
METRICS_PATH = MODEL_DIR / "model_metrics.json"

NUMERIC_FEATURES = [
    "amount", "hour_of_day", "day_of_week", "account_age_days", "device_change_count_24h",
    "ip_risk_score", "avg_transaction_amount_30d", "transaction_count_1h",
    "transaction_count_24h", "failed_login_count_24h", "beneficiary_age_days",
    "distance_from_last_location_km", "minutes_since_last_transaction", "days_since_last_transaction"
]
CATEGORICAL_FEATURES = [
    "currency", "transaction_type", "transaction_channel", "kyc_status", "customer_risk_level",
    "merchant_category", "merchant_country", "merchant_risk_level", "device_type", "device_os",
    "ip_country", "source_country", "destination_country"
]
BOOLEAN_FEATURES = ["is_new_device", "is_vpn", "is_proxy", "is_cross_border", "password_change_recently", "beneficiary_is_new"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES + BOOLEAN_FEATURES


def make_encoder():
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def main():
    adapter = create_db_adapter()
    df = adapter.fetch_training_data()
    if df.empty:
        raise RuntimeError("No training data found. Run data-loader/generate_initial_data.js first.")

    df[BOOLEAN_FEATURES] = df[BOOLEAN_FEATURES].fillna(False).astype(int)
    y = df["is_fraud"].astype(int)
    x = df[FEATURES].copy()

    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
            ("categorical", make_encoder(), CATEGORICAL_FEATURES),
            ("boolean", "passthrough", BOOLEAN_FEATURES)
        ]
    )
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(n_estimators=150, random_state=42, class_weight="balanced"))
    ])

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, stratify=y, random_state=42)
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    probabilities = pipeline.predict_proba(x_test)[:, 1]

    report = classification_report(y_test, predictions)
    print(report)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, predictions, average="binary", zero_division=0)
    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc_score(y_test, probabilities),
        "training_rows": int(len(df))
    }

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump({"pipeline": pipeline, "features": FEATURES, "boolean_features": BOOLEAN_FEATURES}, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    logger.info("Saved model to %s and metrics to %s", MODEL_PATH, METRICS_PATH)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Training failed")
        raise

