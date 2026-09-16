import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.crud import crud_case, crud_prediction
from app.core.security import create_access_token
from app.models.user import User, RoleEnum

client = TestClient(app)

def _auth_header():
    token = create_access_token(data={"sub": "admin", "role": RoleEnum.ADMIN.value})
    return {"Authorization": f"Bearer {token}"}

def _mock_auth(monkeypatch):
    mock_user = User(id=1, username="admin", email="a@b.com",
                     hashed_password="fakehash", role=RoleEnum.ADMIN)
    monkeypatch.setattr("app.api.deps.get_user_by_username", lambda db, username: mock_user)

class MockCase:
    def __init__(self, description, reported_at):
        self.description = description
        self.reported_at = reported_at

def test_predict_valid_case(monkeypatch):
    _mock_auth(monkeypatch)

    def mock_get_case(db, case_id):
        return MockCase("Test description", None)

    def mock_create_prediction(db, prediction_data):
        from app.models.prediction import Prediction
        return Prediction(id=1, case_id=prediction_data.case_id, risk_level="HIGH")

    def mock_evaluate_alert(db, prediction):
        pass

    from app.services import alert_service
    monkeypatch.setattr(crud_case, "get_case_by_case_id", mock_get_case)
    monkeypatch.setattr(crud_prediction, "create_prediction", mock_create_prediction)
    monkeypatch.setattr(alert_service, "evaluate_and_create_alert", mock_evaluate_alert)

    response = client.post("/predict", json={"case_id": "C10231"}, headers=_auth_header())

    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == "C10231"
    assert "time_window" in data
    assert "predictions" in data
    assert "explanation" in data

    if data["predictions"]:
        top = data["predictions"][0]
        assert "rank" in top
        assert "atm_id" in top
        assert top["atm_id"] == "ATM-0184" # Target ATM inclusion
        assert 0.0 <= top["probability"] <= 1.0 # Probabilities between 0 and 1

        # Test ranking is sorted correctly
        ranks = [c["rank"] for c in data["predictions"]]
        assert ranks == sorted(ranks)

        # Test Top-5 contract
        assert len(data["predictions"]) == 5

def test_predict_unknown_case(monkeypatch):
    _mock_auth(monkeypatch)

    def mock_get_case(db, case_id):
        return None

    monkeypatch.setattr(crud_case, "get_case_by_case_id", mock_get_case)

    response = client.post("/predict", json={"case_id": "UNKNOWN_999"}, headers=_auth_header())

    assert response.status_code == 404
    assert response.json()["detail"] == "Case not found"
