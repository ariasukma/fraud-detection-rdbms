# Fraud Detection RDBMS Architecture

# Overview

Fraud Detection RDBMS is a production-oriented real-time fraud detection platform that supports multiple relational databases through an adapter-based architecture.

The system performs:

* Synthetic transaction generation
* Machine learning model training
* Real-time fraud prediction
* Dashboard visualization

Supported databases:

* PostgreSQL
* CockroachDB
* MySQL
* Oracle
* SQL Server

The active database is selected at runtime with the `DB_TYPE` environment variable. Only one database is active per deployment.

# High Level Architecture

```text
+------------------------------+
| data-loader                  |
| - initial data generation    |
| - realtime transactions      |
+---------------+--------------+
                |
                v
+---------------+--------------+
| Database                     |
| PostgreSQL / CockroachDB /   |
| MySQL / Oracle / SQL Server  |
+---------------+--------------+
                |
                v
+---------------+--------------+
| ML Training                  |
| train_model.py               |
| model + metrics artifacts    |
+---------------+--------------+
                |
                v
+---------------+--------------+
| Predictor Service            |
| predictor_service.py         |
| updates pending transactions |
+---------------+--------------+
                |
                v
+---------------+--------------+
| FastAPI                      |
| api_service.py               |
| dashboard API endpoints      |
+---------------+--------------+
                |
                v
+---------------+--------------+
| React Dashboard              |
| realtime visualization       |
+------------------------------+
```

Runtime flow:

```text
Data Loader -> Database -> ML Training -> Predictor Service -> FastAPI -> React Dashboard
```

Training and prediction share the same source-of-truth table, `transactions`. The dashboard never connects to the database directly; it only reads data through FastAPI.

# Components

## data-loader

The `data-loader` component is a Node.js service responsible for creating synthetic transaction records.

Responsibilities:

* Generate initial training data
* Generate real-time transactions
* Support multiple databases via adapters
* Keep database-specific insert SQL inside adapter files

Key files:

| File | Purpose |
| --- | --- |
| `generate_initial_data.js` | Generates 5000 labeled training transactions. |
| `realtime_transaction_generator.js` | Inserts one pending transaction every second. |
| `transaction_factory.js` | Creates synthetic transaction payloads and synthetic fraud labels. |
| `db/*` | Database adapters for PostgreSQL, CockroachDB, MySQL, Oracle, and SQL Server. |

Initial data rows include labels:

```text
is_fraud = true or false
fraud_type = synthetic rule name or null
fraud_score = generated score
prediction_status = TRAINING
```

Real-time rows are inserted as pending:

```text
is_fraud = NULL
fraud_type = NULL
fraud_score = NULL
prediction_status = PENDING
```

## ml-service

The `ml-service` component contains model training, real-time prediction, database access adapters, and the FastAPI service.

Responsibilities:

* Train fraud model
* Evaluate model
* Predict fraud in real time
* Serve dashboard APIs
* Keep database-specific query syntax inside adapter files

Key files:

| File | Purpose |
| --- | --- |
| `train_model.py` | Extracts labeled data, trains the model, evaluates it, and writes artifacts. |
| `predictor_service.py` | Continuously polls pending transactions and updates predictions. |
| `api_service.py` | Serves FastAPI dashboard endpoints. |
| `db/*` | Python database adapters and factory. |

Model artifacts:

| Artifact | Purpose |
| --- | --- |
| `models/fraud_model.pkl` | Trained scikit-learn pipeline. |
| `models/model_metrics.json` | Accuracy, precision, recall, F1, ROC AUC, and training row count. |

## dashboard

The `dashboard` component is a React + Vite frontend for monitoring fraud activity and model performance.

Responsibilities:

* Real-time monitoring
* Fraud visualization
* Model metrics display
* Poll FastAPI every second
* Use red for fraud and blue for normal transactions

Key files:

| File | Purpose |
| --- | --- |
| `FraudRealtimeChart.jsx` | Line chart showing fraud vs normal transaction counts. |
| `FraudSummaryCards.jsx` | Summary cards for total, fraud, normal, and fraud rate. |
| `FraudTypeChart.jsx` | Bar chart of fraud type counts. |
| `LatestTransactionsTable.jsx` | Table of latest transactions with fraud row highlighting. |
| `ModelMetricsCard.jsx` | Displays model metrics. |

# Database Architecture

The project uses the adapter pattern for database access. Each runtime component calls a common interface, while each database adapter owns the SQL syntax and connection details for its database.

This keeps database-specific SQL out of business logic.

Examples:

| Runtime | Adapter Location | Responsibility |
| --- | --- | --- |
| Node.js data loader | `data-loader/db/postgres.js` | PostgreSQL batch inserts |
| Node.js data loader | `data-loader/db/mysql.js` | MySQL batch inserts |
| Python ML/API | `ml-service/db/postgres.py` | PostgreSQL reads and updates |
| Python ML/API | `ml-service/db/sqlserver.py` | SQL Server reads and updates |

The active adapter is selected by `DB_TYPE`.

Example:

```env
DB_TYPE=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=fraud_db
DB_USER=fraud_user
DB_PASSWORD=fraud_password
```

Other valid database types:

```env
DB_TYPE=cockroachdb
DB_TYPE=mysql
DB_TYPE=oracle
DB_TYPE=sqlserver
```

The `transactions` table is the source of truth. Application code must not rename or remove columns. New columns require migration scripts for all supported databases.

# Fraud Rules

Synthetic fraud labels are created from business-style rules. These labels are used to train the initial model.

| Rule | Business Meaning | Trigger Condition | Example Transaction |
| --- | --- | --- | --- |
| `HIGH_AMOUNT_ANOMALY` | Transaction amount is unusually high compared to customer history. | `amount` is much larger than `avg_transaction_amount_30d`. | Customer averages USD 100 but sends USD 2,000. |
| `NEW_DEVICE_FRAUD` | Account is used from a new or frequently changing device. | `is_new_device = true` and `device_change_count_24h` is high. | Customer logs in from a new Android device after several device changes. |
| `ACCOUNT_TAKEOVER` | Account may have been compromised after login failures or credential changes. | High `failed_login_count_24h` and `password_change_recently = true`. | Five failed logins followed by a password change and transfer. |
| `NEW_BENEFICIARY_FRAUD` | Money is sent to a new beneficiary with little history. | `beneficiary_is_new = true` and `beneficiary_age_days` is low. | New payee added today receives a large transfer. |
| `VELOCITY_FRAUD` | Transaction frequency is abnormally high. | High `transaction_count_1h` or `transaction_count_24h`. | Ten transfers happen within one hour. |
| `GEO_ANOMALY` | Customer location changes too quickly to be plausible. | High `distance_from_last_location_km` and low `minutes_since_last_transaction`. | Login from Jakarta followed by another transaction from London minutes later. |
| `CROSS_BORDER_HIGH_RISK` | Cross-border transaction targets a high-risk destination. | `is_cross_border = true` and `destination_country` is high risk. | Local account sends funds to a high-risk jurisdiction. |
| `VPN_PROXY_FRAUD` | Network origin may be hidden or risky. | `is_vpn = true`, `is_proxy = true`, or high `ip_risk_score`. | Transaction originates from a proxy with IP risk score 92. |
| `HIGH_RISK_MERCHANT` | Merchant profile is associated with elevated fraud risk. | `merchant_risk_level = HIGH`. | Payment to a high-risk crypto merchant. |
| `DORMANT_ACCOUNT_FRAUD` | Dormant account suddenly performs abnormal activity. | High `days_since_last_transaction` and amount much higher than average. | Account inactive for 220 days sends a large transfer. |

# Machine Learning Architecture

## Training Flow

```text
Database
  -> extract labeled rows
  -> preprocessing
  -> train/test split
  -> RandomForestClassifier
  -> metrics
  -> model artifact
```

Training details:

| Stage | Description |
| --- | --- |
| Data extraction | Reads `transactions WHERE is_fraud IS NOT NULL`. |
| Preprocessing | Uses `ColumnTransformer` for numeric, categorical, and boolean features. |
| Model pipeline | Uses a scikit-learn `Pipeline`. |
| Classifier | Uses `RandomForestClassifier`. |
| Evaluation | Produces classification report and metrics. |
| Artifacts | Writes `models/fraud_model.pkl` and `models/model_metrics.json`. |

## Prediction Flow

```text
Database
  -> predictor service
  -> load pending transactions
  -> model prediction
  -> rule-based fraud explanation
  -> update database
```

The predictor service processes a maximum of 1000 pending rows per cycle.

Prediction state transition:

```text
PENDING -> PREDICTED
```

The update is idempotent because rows are updated only when their current `prediction_status` is still `PENDING`.

# Dashboard Architecture

The dashboard communicates only with FastAPI.

API endpoints:

| Endpoint | Purpose |
| --- | --- |
| `/api/summary` | Total, fraud, normal, and average fraud score summary. |
| `/api/latest-transactions` | Latest transaction table rows. |
| `/api/fraud-timeseries` | Fraud vs normal counts by time bucket. |
| `/api/fraud-types` | Fraud counts grouped by fraud type. |
| `/api/model-metrics` | Model accuracy, precision, recall, F1, ROC AUC, and training rows. |

Refresh behavior:

```text
Dashboard -> FastAPI every 1 second
```

Color scheme:

| Meaning | Color |
| --- | --- |
| Fraud | Red |
| Normal | Blue |

# Future Architecture

Reserved future expansion areas:

## Kafka

Kafka can be introduced as an event stream between transaction producers, prediction workers, and analytics consumers.

## Redis

Redis can be used for low-latency counters, feature caching, API caching, and distributed locks.

## Feature Store

A feature store can centralize feature definitions and ensure consistency between training and inference.

## XGBoost

XGBoost can be evaluated as a stronger tabular model for fraud classification.

## Streaming Inference

Streaming inference can move prediction from polling-based batches to event-driven processing.

## LLM Investigation Assistant

An LLM assistant can summarize suspicious activity, generate investigator notes, and explain fraud evidence from transaction context.

