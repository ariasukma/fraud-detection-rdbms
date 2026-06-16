# Project Mission

Build a production-grade real-time fraud detection platform supporting:

- PostgreSQL
- CockroachDB
- MySQL
- Oracle
- SQL Server

with:

- Node.js Data Loader
- Python ML Service
- FastAPI
- React Dashboard

# Architecture Rules

- Use adapter pattern for all database access.
- Never place database-specific SQL outside adapter files.
- Runtime database selected by DB_TYPE environment variable.
- Only one active database per deployment.
- Dashboard must never access database directly.
- Dashboard only talks to FastAPI.

# Database Rules

- transactions table is the source of truth.
- Do not rename columns.
- Do not remove columns.
- New columns require migration scripts for all supported databases.
- No ORM.
- Use raw SQL.

# ML Rules

- Use scikit-learn Pipeline.
- Use ColumnTransformer.
- Model artifact stored in models/fraud_model.pkl.
- Metrics stored in models/model_metrics.json.
- Predictor service processes max 1000 rows per cycle.
- Predictor service must be idempotent.

# Frontend Rules

- Use React + Vite.
- Use Recharts.
- Fraud = red.
- Normal = blue.
- Refresh interval = 1 second.
- No direct database access.

# API Rules

Required endpoints:

- /api/summary
- /api/latest-transactions
- /api/fraud-timeseries
- /api/fraud-types
- /api/model-metrics

# Code Quality

- Python 3.11
- Node.js 22
- Error handling required.
- Logging required.
- No hardcoded credentials.
- All configuration from .env.

# Testing Rules

Any new feature must include:

- unit tests
- integration tests when database access is involved

# Forbidden Changes

Do not:

- remove multi-database support
- replace FastAPI
- replace React
- replace sklearn
- replace adapter pattern
- introduce ORM
- hardcode credentials

