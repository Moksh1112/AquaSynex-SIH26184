# PROJECT_COMPLETE_DOCUMENTATION

## 1. Project Overview
- **Project Name**: AquaSynex-SIH26184
- **SIH Problem Statement**: PS-1 (or equivalent) related to predictive policing for cybercrime.
- **Objective**: Predict cash withdrawal locations for cybercrime syndicates before they cash out, identify high-risk jurisdictions, and provide actionable intelligence to law enforcement agencies (LEAs).
- **Problem being solved**: Cybercriminals rapidly move money across accounts and cash out via ATMs. LEAs struggle to track the money trail in real-time and predict where the final cash-out will occur.
- **Expected real-world workflow**: 
  1. A victim reports a cybercrime on NCRP.
  2. The system ingests the complaint and identifies the first suspicious account.
  3. The system maps the historical financial network and uses an ML model (XGBoost) to predict the likely final cash-out ATMs.
  4. The system calculates the nearest police station for the high-risk ATMs and routes alerts to the appropriate jurisdiction for rapid intervention.
- **What the system actually does**: Implements the end-to-end pipeline described above, using historical and spatial features for ML prediction, PostgreSQL/PostGIS for spatial queries, Neo4j for the Money Trail visualization, and a Next.js dashboard for LEA investigators.

## 2. PS Requirement Mapping
1. **Analyze historical cybercrime data**: PASS. Implemented via the ML feature engineering pipeline which uses historical complaints and transactions.
2. **Analyze financial data**: PASS. Parses transactions and withdrawals to build the financial graph.
3. **Predict cash withdrawal locations**: PASS. XGBoost model predicts the Top-5 ATM locations.
4. **Predict in advance**: PASS. Uses a strict time-cutoff to ensure prediction only uses data available at T0 (complaint time).
5. **Pattern detection**: PASS. Uses network/syndicate features (e.g., node degree, transaction velocity) in XGBoost.
6. **Geospatial risk modeling**: PASS. Uses PostGIS to calculate spatial densities and distances.
7. **Risk heatmap**: PASS. Frontend Geo Intelligence tab displays risk density markers.
8. **Drill-down by location**: PASS. Geo Intelligence map supports zoom/drill-down into specific ATMs.
9. **Drill-down by time**: PASS. The time window prediction provides 4-hour temporal predictions.
10. **Drill-down by crime category**: PARTIAL / SANDBOX. Basic category filtering exists in the frontend UI simulation, but deep analytics per category is limited.
11. **Secure LEA interface**: PASS. Next.js dashboard with JWT authentication.
12. **Alerts**: PASS. `Alert` model and API routes implemented for lifecycle management.
13. **Law-enforcement action**: PASS. Police station recommendation engine routes actionable tasks.
14. **Banks/FIs**: PARTIAL / SANDBOX. Adapter parses bank data, but no live FI API is integrated (sandbox implementation).
15. **I4C coordination**: PARTIAL / SANDBOX. Modeled in the database but no external live connection.
16. **Cross-jurisdiction intelligence**: PASS. Nearest police station and jurisdictional routing handle cross-border interventions.
17. **Evidence access**: PASS. Evidence upload, validation, and secure download are fully implemented.
18. **Actionable intelligence**: PASS. Provides Top-5 ATMs, probabilities, SHAP rationales, and recommended actions.
19. **Real-time notification**: NOT IMPLEMENTED. No real-time WebSockets/SSE is actively pushing data to clients; relies on polling/refresh.
20. **SMS/email/API**: NOT IMPLEMENTED. Hooks exist in the alerts service, but no live SMTP/Twilio integration is active.
21. **NCRP input**: PARTIAL / SANDBOX. Local REST API endpoint acts as a webhook receiver for NCRP payloads, but no live upstream NCRP connection exists.

## 3. Complete Tech Stack
- **Python (3.x)**: Core backend runtime.
- **FastAPI**: High-performance web framework for the backend REST API. 
- **Pydantic**: Data validation and serialization.
- **SQLAlchemy**: ORM for relational data.
- **Alembic**: Database migrations.
- **PostgreSQL**: Primary authoritative relational database.
- **PostGIS**: PostgreSQL extension for geospatial calculations (nearest police station).
- **Neo4j**: Graph database for querying and projecting the "Money Trail" for investigators.
- **Cypher**: Query language used to interact with Neo4j.
- **Pandas/NumPy**: Data manipulation for ML feature engineering.
- **scikit-learn / XGBoost**: ML pipeline for candidate scoring.
- **SHAP**: Explainable AI to provide prediction rationale.
- **Next.js / React**: Frontend framework for the LEA dashboard.
- **TypeScript**: Static typing for the frontend.
- **Tailwind CSS**: Styling.
- **Leaflet / React Leaflet**: Map visualization for the Geo Intelligence and Predictions tabs.
- **JWT**: Secure authentication tokens.

## 4. Complete Folder/File Structure
- `backend/app/api/`: FastAPI route handlers (e.g., `predictions.py`, `cases.py`).
- `backend/app/crud/`: Database interaction logic.
- `backend/app/db/`: Database connection setup, Neo4j sync (`neo4j_sync.py`), and seeding logic.
- `backend/app/ml/`: Machine learning pipeline (`predictive_pipeline.py`, `feature_engineering.py`).
- `backend/app/models/`: SQLAlchemy models (`complaint.py`, `police_station.py`).
- `backend/app/schemas/`: Pydantic validation schemas.
- `backend/app/services/`: Business logic layer (e.g., `police_station_service.py`).
- `backend/tests/`: Pytest suite (e.g., `test_predictive_cutoff.py`).
- `frontend/app/`: Next.js app router pages.
- `frontend/components/`: Reusable React components (`PredictionPanel.tsx`, `NetworkGraph.tsx`).

## 5. Backend Architecture
The backend follows a standard layered architecture: API Routes → Services → CRUD → Database. 
FastAPI handles HTTP requests. The prediction pipeline generates candidates, scores them using XGBoost, computes SHAP values, and the police station service calculates the nearest intervention point using PostGIS.

## 6. Database Architecture
- **users**: LEA investigators.
- **complaints**: Core intake records from NCRP.
- **accounts / transactions / withdrawals**: Financial history representing the money trail.
- **atms**: Known cash-out locations.
- **predictions / prediction_candidates**: Persisted ML results and top-5 rankings.
- **alerts**: Intervention tasks for LEAs.
- **police_stations**: Geospatial records of law enforcement hubs.
- **evidence**: Associated case files.

## 7. ML Architecture
Complaint received → T0 cutoff established (no future data leakage) → spatial/network candidates generated → features engineered (transaction velocity, historical fraud rate, node degree) → XGBoost model predicts cash-out probability → Top 5 candidates ranked → 4-hour time window predicted → SHAP values computed for transparency. A zero-history case will legitimately return insufficient data as it lacks the historical edges required for candidate generation.

## 8. Neo4j Architecture
Neo4j acts as a downstream graph projection of the authoritative PostgreSQL database. `sync_to_neo4j()` merges PostgreSQL edges into the graph. It powers the visual Money Trail in the frontend, enabling rapid investigator comprehension of complex financial syndicates.

## 9. Geospatial Architecture
PostGIS is used to calculate exact distances between high-risk ATMs and known Police Stations using `ST_DistanceSphere`. This provides actionable intelligence by routing alerts to the physical station closest to the predicted crime.

## 10. Frontend Architecture
Next.js SSR/CSR application.
- **Command Center**: High-level system overview.
- **Case Files**: List of active investigations.
- **Predictions**: Detail view of a case's prediction, showing Top-5 ATMs, SHAP values, and the nearest police station map.
- **Geo Intelligence**: Heatmap of overall risk.
- **Money Trail**: Interactive graph visualization of the Neo4j data.
- **Alerts**: Workflow management for interventions.

## 11. Alert and Intervention Workflow
Prediction generated → Police Station identified → Alert created in OPEN state → Assigned to jurisdiction → ACKNOWLEDGED by officer → Action taken → RESOLVED.

## 12. Evidence and Audit
Evidence can be uploaded, validated for MIME type, stored locally (outside git), and associated with a case. Audit logs track every API mutation.

## 13. Security
JWT-based authentication protects API routes. Evidence files are protected behind authenticated download endpoints.

## 14. Complete End-to-End Data Flow
```text
Complaint (NCRP)
↓
Case + Account Identification
↓
Financial History (PostgreSQL)
↓
ML Feature Engineering (T0 Cutoff)
↓
XGBoost Scoring -> Top-5 ATMs
↓
SHAP Rationale + Time Window
↓
PostGIS Nearest Police Station
↓
Alert Creation
↓
Frontend Dashboard
```

## 15. APIs
| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/predictions/predict/{case_id}` | Generate prediction |
| GET | `/api/cases/{case_id}` | Retrieve case details |
| POST | `/api/evidence/` | Upload evidence |
| GET | `/api/alerts/` | List alerts |

## 16. Inputs and Outputs
- **Prediction Input**: Case ID (`C-2026-9081`).
- **Prediction Output**: Top-5 ATMs, probabilities (e.g., 85%), SHAP breakdown, Nearest Police Station (e.g., "Mumbai Central Police Station").

## 17. Demo Scenarios
- **A. Operational E2E Pipeline (`C-2026-9081`)**: This case demonstrates the functional execution of the prediction pipeline, including Top-5 ATM generation, SHAP rationale, map rendering, and response unit (Police Station) routing. Note: While it proves the software architecture works cohesively, it relies on historical features from synthetic test data and does not independently prove real-world future prediction accuracy without real-world training data.
- **B. Predictive Cutoff Validation (`NCRP-2026-501`)**: Demonstrates that the model rigorously excludes future transactions. This is a zero-history scenario where future transactions occur after the complaint T0. The system correctly identifies that insufficient data was known at T0 and refuses to hallucinate a prediction, thereby proving no future-data leakage.

## 18. Testing
- **Backend**: Pytest suite (85 passed, 0 failures).
- **Frontend**: `tsc` and `next build` succeed with 0 errors.
- **ML Cutoff**: Verified. Future data leakage is successfully prevented.

## 19. Current Working Status
All core components are PASS. External integrations (Banks, I4C, NCRP) are PARTIAL / SANDBOX. Notifications are NOT IMPLEMENTED.

## 20. Known Limitations
- **No live NCRP API credentials**: Currently operates as a sandbox webhook.
- **No live bank account blocking capabilities**: Simulated integrations.
- **No live SMS/Email delivery**: Alerts are in-app only.
- **Prediction Accuracy limitations**: Predictions depend heavily on having sufficient historical graph edges. C-2026-9081 demonstrates the software pipeline, but real-world accuracy requires live external training data.

## 21. Future Enhancements
- Live integration with I4C APIs.
- Real-time WebSocket notifications.

## 22. Setup and Run Instructions
1. Install PostgreSQL + PostGIS, and Neo4j.
2. `cd backend && python -m venv venv && source venv/bin/activate` (or equivalent on Windows)
3. `pip install -r requirements.txt`
4. `alembic upgrade head`
5. `python -m app.db.seed`
6. `python -m uvicorn app.main:app --port 8000`
7. `cd frontend && npm install && npm run dev`

## 23. Demo Procedure
1. Open Command Center on `localhost:3000`.
2. Navigate to Case Files and select `C-2026-9081` (Operational E2E).
3. View the Money Trail (Neo4j).
4. Run Prediction -> Show Top-5 ATMs, SHAP, and Nearest Police Station on the map.
5. Check Alerts for the generated intervention task.
6. Switch to `NCRP-2026-501` to demonstrate zero-history cutoff validation.

## 24. Final PS Compliance Summary
- **PASS**: 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 16, 17, 18
- **PARTIAL / SANDBOX**: 10, 14, 15, 21
- **NOT IMPLEMENTED**: 19, 20
