# Fraud Detection RDBMS Runbook

Audience:

* DevOps Engineers
* Developers
* DBA

# Environment Requirements

| Requirement | Version |
| --- | --- |
| Ubuntu | 22.04+ |
| Docker | Recent Docker Engine with Compose support |
| Python | 3.11+ |
| Node.js | 22+ |

Recommended tools:

| Tool | Purpose |
| --- | --- |
| `psql` | PostgreSQL and CockroachDB schema execution and verification |
| `mysql` | MySQL schema execution and verification |
| `sqlplus` or SQL Developer | Oracle schema execution and verification |
| `sqlcmd` | SQL Server schema execution and verification |

# Initial Setup

Clone the repository:

```bash
git clone <repository-url>
cd fraud-detection
```

Enter the project:

```bash
cd fraud-detection-rdbms
```

Copy environment files:

```bash
cp .env.example .env
cp data-loader/.env.example data-loader/.env
cp ml-service/.env.example ml-service/.env
```

Set the active database in each `.env` file:

```env
DB_TYPE=postgres
```

Supported values:

| DB_TYPE | Database |
| --- | --- |
| `postgres` | PostgreSQL |
| `cockroachdb` | CockroachDB |
| `mysql` | MySQL |
| `oracle` | Oracle |
| `sqlserver` | SQL Server |

# Starting Databases

Start all database containers:

```bash
docker compose up -d
```

Verify containers:

```bash
docker ps
```

Expected database services:

| Service | Port |
| --- | --- |
| PostgreSQL | `5432` |
| CockroachDB SQL | `26257` |
| CockroachDB UI | `8080` |
| MySQL | `3306` |
| Oracle | `1521` |
| SQL Server | `1433` |

Health verification commands:

PostgreSQL:

```bash
docker exec -it fraud-postgres pg_isready -U fraud_user -d fraud_db
```

CockroachDB:

```bash
docker exec -it fraud-cockroachdb cockroach sql --insecure --execute "SHOW DATABASES;"
```

MySQL:

```bash
docker exec -it fraud-mysql mysqladmin ping -u fraud_user -pfraud_password
```

Oracle:

```bash
docker exec -it fraud-oracle healthcheck.sh
```

SQL Server:

```bash
docker exec -it fraud-sqlserver /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'FraudPassword123!' -Q "SELECT 1"
```

# Database Schema Creation

Run the schema file that matches `DB_TYPE`.

| Database | Schema File |
| --- | --- |
| PostgreSQL | `sql/postgres.sql` |
| CockroachDB | `sql/cockroachdb.sql` |
| MySQL | `sql/mysql.sql` |
| Oracle | `sql/oracle.sql` |
| SQL Server | `sql/sqlserver.sql` |

PostgreSQL:

```bash
psql -h localhost -p 5432 -U fraud_user -d fraud_db -f sql/postgres.sql
```

CockroachDB:

```bash
cockroach sql --insecure --host=localhost:26257 --database=fraud_db --file=sql/cockroachdb.sql
```

MySQL:

```bash
mysql -h 127.0.0.1 -P 3306 -u fraud_user -pfraud_password fraud_db < sql/mysql.sql
```

Oracle:

```bash
sqlplus fraud_user/fraud_password@localhost:1521/FREEPDB1 @sql/oracle.sql
```

SQL Server:

```bash
/opt/mssql-tools/bin/sqlcmd -S localhost,1433 -U fraud_user -P fraud_password -d fraud_db -i sql/sqlserver.sql
```

Verify table creation:

```sql
SELECT COUNT(*) FROM transactions;
```

# Generating Initial Data

Install dependencies:

```bash
cd data-loader
npm install
```

Generate initial data:

```bash
node generate_initial_data.js
```

Expected outcome:

```text
5000 rows inserted
```

Verification SQL:

```sql
SELECT COUNT(*) AS total_rows
FROM transactions;
```

```sql
SELECT prediction_status, COUNT(*) AS count
FROM transactions
GROUP BY prediction_status;
```

Expected status after initial generation:

| prediction_status | Expected |
| --- | --- |
| `TRAINING` | 5000 |

# Training Model

Install Python dependencies:

```bash
cd ../ml-service
pip install -r requirements.txt
```

Train the model:

```bash
python train_model.py
```

Expected output:

* Classification report printed to the terminal
* Saved model at `models/fraud_model.pkl`
* Saved metrics at `models/model_metrics.json`

Verify artifacts:

```bash
ls -l models/fraud_model.pkl models/model_metrics.json
```

# Running Real-Time Prediction

Start the predictor:

```bash
python predictor_service.py
```

The predictor runs continuously and polls up to 1000 pending rows per cycle.

Prediction status transitions:

| Status | Meaning |
| --- | --- |
| `TRAINING` | Historical labeled data used for model training. |
| `PENDING` | New transaction waiting for prediction. |
| `PREDICTED` | Transaction processed by predictor service. |

Start the real-time transaction generator in another terminal:

```bash
cd data-loader
node realtime_transaction_generator.js
```

Expected behavior:

* One new transaction inserted every second
* New rows start as `PENDING`
* Predictor updates rows to `PREDICTED`

# Starting API Service

Start FastAPI:

```bash
cd ml-service
uvicorn api_service:app --reload --host 0.0.0.0 --port 8000
```

Verification endpoints:

```bash
curl http://localhost:8000/api/summary
curl http://localhost:8000/api/latest-transactions
curl http://localhost:8000/api/fraud-timeseries
curl http://localhost:8000/api/fraud-types
curl http://localhost:8000/api/model-metrics
```

# Starting Dashboard

Install dependencies:

```bash
cd dashboard
npm install
```

Start the dashboard:

```bash
npm run dev
```

Expected URL:

[http://localhost:5173](http://localhost:5173/)

# Troubleshooting

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| Database connection failures | Incorrect `.env`, wrong port, container not ready | Check `DB_TYPE`, credentials, `docker ps`, and container logs. |
| Missing model file | `train_model.py` has not been run | Run training before starting predictor. |
| Python dependency errors | Missing package or incompatible Python version | Use Python 3.11+ and rerun `pip install -r requirements.txt`. |
| Node dependency errors | Missing `node_modules` or wrong Node version | Use Node.js 22+ and rerun `npm install`. |
| Dashboard cannot reach API | FastAPI not running or CORS/network issue | Verify `http://localhost:8000/api/summary` and `VITE_API_BASE_URL`. |
| Oracle startup delays | Oracle container needs extra initialization time | Wait several minutes and check `docker logs fraud-oracle`. |
| SQL Server startup delays | SQL Server initialization still running | Check `docker logs fraud-sqlserver` and retry health command. |

Useful logs:

```bash
docker logs fraud-postgres
docker logs fraud-cockroachdb
docker logs fraud-mysql
docker logs fraud-oracle
docker logs fraud-sqlserver
```

# Operational Checks

Total transactions:

```sql
SELECT COUNT(*) AS total_transactions
FROM transactions;
```

Fraud transactions:

```sql
SELECT COUNT(*) AS fraud_transactions
FROM transactions
WHERE is_fraud = true;
```

For Oracle and SQL Server, use numeric/bit comparison:

```sql
SELECT COUNT(*) AS fraud_transactions
FROM transactions
WHERE is_fraud = 1;
```

Pending predictions:

```sql
SELECT COUNT(*) AS pending_predictions
FROM transactions
WHERE prediction_status = 'PENDING';
```

Predicted transactions:

```sql
SELECT COUNT(*) AS predicted_transactions
FROM transactions
WHERE prediction_status = 'PREDICTED';
```

Fraud type distribution:

```sql
SELECT fraud_type, COUNT(*) AS count
FROM transactions
WHERE fraud_type IS NOT NULL
GROUP BY fraud_type
ORDER BY count DESC;
```

# Model Retraining

Retrain manually:

```bash
cd ml-service
python train_model.py
```

Recommended process:

| Step | Action |
| --- | --- |
| 1 | Stop predictor or ensure no deployment conflict. |
| 2 | Run `python train_model.py`. |
| 3 | Verify `models/fraud_model.pkl` and `models/model_metrics.json`. |
| 4 | Restart predictor service to load the new model. |

Weekly cron example:

```cron
0 2 * * 0 cd /opt/source/fraud-detection/fraud-detection-rdbms/ml-service && /usr/bin/python3 train_model.py >> /var/log/fraud-model-retrain.log 2>&1
```

# Backup and Recovery

Database backup recommendations:

| Database | Example Backup Approach |
| --- | --- |
| PostgreSQL | `pg_dump` scheduled backups. |
| CockroachDB | `BACKUP` jobs to external storage. |
| MySQL | `mysqldump` or physical backups. |
| Oracle | Data Pump export or managed backup tooling. |
| SQL Server | Native `.bak` backups. |

Model backup recommendations:

* Back up `ml-service/models/fraud_model.pkl`.
* Back up `ml-service/models/model_metrics.json`.
* Store model artifacts with timestamped versions.
* Keep the training code version associated with each model artifact.

Example artifact backup:

```bash
mkdir -p backups/models
cp ml-service/models/fraud_model.pkl backups/models/fraud_model-$(date +%Y%m%d).pkl
cp ml-service/models/model_metrics.json backups/models/model_metrics-$(date +%Y%m%d).json
```

# Security Recommendations

Passwords:

* Change all default passwords before production use.
* Use unique passwords for each database and service user.
* Rotate credentials regularly.

Secrets:

* Do not commit `.env` files.
* Store secrets in a secrets manager for production deployments.
* Restrict database users to the minimum privileges required.

TLS:

* Enable TLS for database connections in production.
* Serve FastAPI behind HTTPS.
* Use secure network policies between services.

Production deployment considerations:

| Area | Recommendation |
| --- | --- |
| Network | Restrict database ports to trusted networks only. |
| API | Add authentication and authorization before exposing externally. |
| Dashboard | Serve through a hardened reverse proxy. |
| Logging | Avoid logging credentials or sensitive customer data. |
| Monitoring | Track API latency, prediction lag, pending queue size, and model metrics. |
| Backups | Test restore procedures regularly. |

