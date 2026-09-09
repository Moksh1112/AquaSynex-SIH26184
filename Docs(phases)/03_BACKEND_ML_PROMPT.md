# SIH26184 — Backend + ML Master Prompt

You are the backend/ML engineer for SIH26184. Build a reliable prototype, not an enterprise platform.

## Pipeline
DATA → FEATURES → MONEY GRAPH → SPATIAL/TEMPORAL → CANDIDATES → XGBoost/LightGBM → TOP-5 → TIME → SHAP → RISK → ALERT → FastAPI → React.

## Data
Create realistic synthetic correlated scenarios:
Victim → Mule A → Mule B → Mule C → cash-out.

Tables/entities:
complaints, accounts, transactions, withdrawals, ATMs, devices, IPs, predictions, alerts, users, audit_logs.

## Features
transaction_count, transaction_velocity, amount_velocity, average_amount, time_since_last_transaction, account_age, previous_fraud_count, connected_account_count, risky_neighbor_count, shared_device_count, shared_ip_count, network_depth, distance_to_atm, historical_cashout_count, H3 activity, hour, day_of_week, transfer_to_withdrawal_interval.

No future leakage.

## Candidate generation
Do not make every ATM a multiclass target.

10,000 ATMs → geographic/history/risk filtering → 20–50 candidates → score candidates → Top-5.

Implement:
`generate_candidates(case_id)`

## Model
Start with XGBoost. Return candidate scores and rank descending. Probability/score is not accuracy.

Evaluate Top-1/3/5 where ground truth exists.

## Graph
Preferred Neo4j/Cypher. If Neo4j becomes a blocker, compute equivalent graph features in Python and keep the graph service interface replaceable.

## Spatial
Use H3 and/or PostGIS if practical. Python distance calculations are an acceptable fallback for the MVP.

## Time
Return an operational window such as `22:00–23:00`.

## Explainability
Use SHAP TreeExplainer if practical. Convert important features into human-readable reasons.

## FastAPI
Required:
POST `/predict`

Optional:
GET `/cases`
GET `/cases/{id}`
GET `/predictions/{id}`
GET `/alerts`
POST `/alerts`
GET `/graph/{id}`
GET `/audit`

## Security
Lightweight JWT + RBAC + audit logs.
Roles: LEA Investigator, Bank/FI Officer, I4C Analyst, Administrator.

## Alert
>=0.75 HIGH, >=0.50 MEDIUM, otherwise LOW as prototype thresholds.

## AI agent rules
Inspect existing repository first. Preserve API contracts. Use minimal dependencies. Make small changes. Test after each module. Never silently rewrite the project.

Every implementation response:
Understanding → Plan → Files → Implementation → Validation → Integration → Risks.

## Done
POST `/predict` for C10231 returns Top-5, scores, time window, risk and explanation, and the frontend can display them on a map.
