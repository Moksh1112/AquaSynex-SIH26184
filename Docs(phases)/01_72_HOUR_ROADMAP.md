# SIH26184 — 72-Hour Roadmap

## Day 1 — Make the brain work
**Person 1:** architecture, money-flow logic, candidate logic.
**Person 2:** synthetic data, features, XGBoost/LightGBM, Top-5.
**Person 3:** PostgreSQL, FastAPI skeleton, React shell, mock JSON.

### Acceptance
`predict.py --case C10231` returns ranked Top-5 candidates.

## Day 2 — Connect everything
**Person 1:** graph-derived features + integration.
**Person 2:** H3/spatial + time + SHAP + evaluation.
**Person 3:** `/predict`, React integration, Leaflet map, case screen.

### Acceptance
React → FastAPI → ML → JSON → React works.

## Day 3 — Product + demo
**Person 1:** full integration, risk/action, demo.
**Person 2:** model validation and explanations.
**Person 3:** alerts, auth/RBAC, audit, UI polish.

### Final hours
No major new technology. Only bug fixes, integration, deployment and demo rehearsal.

## Final demo
Login → Case C10231 → Money trail → Predict → Top-5 → Map → Time → Why → Risk → Generate Alert → Audit.
