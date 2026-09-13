import sys
import os

sys.path.append(os.path.abspath("backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models import Prediction, PredictionCandidate, Alert, AuditLog, User
from app.core.security import hash_password

client = TestClient(app)

print("--- 7. API LIVE VERIFICATION ---")

# Setup a test user for auth
with SessionLocal() as db:
    user = db.query(User).filter_by(username="test_admin").first()
    if not user:
        user = User(
            username="test_admin", 
            email="admin@test.com", 
            hashed_password=hash_password("password123"),
            role="ADMIN"
        )
        db.add(user)
        db.commit()

# GET /health
r = client.get("/health")
print(f"GET /health: {r.status_code}")

# POST /auth/login
r = client.post("/auth/login", json={"username": "test_admin", "password": "password123"})
print(f"POST /auth/login: {r.status_code}")
token = r.json().get("access_token") if r.status_code == 200 else ""
headers = {"Authorization": f"Bearer {token}"} if token else {}

# GET /cases
r = client.get("/cases", headers=headers)
print(f"GET /cases: {r.status_code}")
cases = r.json() if r.status_code == 200 else []
if cases:
    case_id = cases[0]['id']
    # GET /cases/{case_id}
    r2 = client.get(f"/cases/{case_id}", headers=headers)
    print(f"GET /cases/{{case_id}}: {r2.status_code}")
else:
    print("GET /cases/{case_id}: SKIPPED (No cases returned or auth failed)")

# POST /predict
payload = {
  "case_id": "C-2026-9081",
  "location": {
    "latitude": 19.0760,
    "longitude": 72.8777
  },
  "time_of_day": "14:30:00",
  "amount_lost": 50000.0,
  "transaction_type": "ATM_WITHDRAWAL",
  "additional_features": {}
}
r_pred = client.post("/predict", json=payload, headers=headers)
print(f"POST /predict: {r_pred.status_code}")

# GET /alerts
r = client.get("/alerts", headers=headers)
print(f"GET /alerts: {r.status_code}")
alerts = r.json() if r.status_code == 200 else []
if alerts:
    alert_id = alerts[-1]['id']
    # GET /alerts/{alert_id}
    r2 = client.get(f"/alerts/{alert_id}", headers=headers)
    print(f"GET /alerts/{{alert_id}}: {r2.status_code}")

    # PATCH /alerts/{alert_id}/status
    r3 = client.patch(f"/alerts/{alert_id}/status", json={"status": "INVESTIGATING"}, headers=headers)
    print(f"PATCH /alerts/{{alert_id}}/status: {r3.status_code}")
else:
    print("GET/PATCH alerts: SKIPPED (No alerts)")


print("\n--- 8. PERSISTENCE VERIFICATION ---")
with SessionLocal() as db:
    pred_count = db.query(Prediction).count()
    cand_count = db.query(PredictionCandidate).count()
    alert_count = db.query(Alert).count()
    audit_count = db.query(AuditLog).count()
    print(f"Predictions: {pred_count}")
    print(f"PredictionCandidates: {cand_count}")
    print(f"Alerts: {alert_count}")
    print(f"AuditLogs: {audit_count}")
