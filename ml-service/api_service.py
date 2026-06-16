import math
import numpy as np
import pandas as pd
import json
import logging
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from db import create_db_adapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Fraud Detection API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
adapter = create_db_adapter()
METRICS_PATH = Path("models/model_metrics.json")


def serialize(value):
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def handle(callable_):
    try:
        # return serialize(callable_())
        return clean_json(serialize(callable_()))
    except Exception as exc:
        logger.exception("API request failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def clean_json(data):
    if isinstance(data, list):
        return [clean_json(item) for item in data]

    if isinstance(data, dict):
        return {key: clean_json(value) for key, value in data.items()}

    if isinstance(data, float):
        if math.isnan(data) or math.isinf(data):
            return None
        return data

    if isinstance(data, (np.integer,)):
        return int(data)

    if isinstance(data, (np.floating,)):
        value = float(data)
        if math.isnan(value) or math.isinf(value):
            return None
        return value

    if pd.isna(data):
        return None

    return data


@app.get("/api/summary")
def summary():
    return handle(adapter.get_summary)


@app.get("/api/latest-transactions")
def latest_transactions():
    return handle(lambda: adapter.get_latest_transactions(limit=25))


@app.get("/api/fraud-timeseries")
def fraud_timeseries():
    return handle(adapter.get_fraud_timeseries)


@app.get("/api/fraud-types")
def fraud_types():
    return handle(adapter.get_fraud_types)


@app.get("/api/model-metrics")
def model_metrics():
    if not METRICS_PATH.exists():
        return {"accuracy": None, "precision": None, "recall": None, "f1": None, "roc_auc": None, "training_rows": 0}
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))


@app.get("/health")
def health():
    return {"status": "ok"}

