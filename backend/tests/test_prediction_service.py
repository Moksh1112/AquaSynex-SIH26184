import pytest
from fastapi import HTTPException
from app.services.prediction_service import generate_prediction
from app.ml.predictor import MockPredictor
from app.schemas.prediction import PredictRequest

# --- Tests that can run WITHOUT a live database (Mocked) ---

class MockCase:
    def __init__(self, description, reported_at):
        self.description = description
        self.reported_at = reported_at

def test_generate_prediction_valid_case(monkeypatch):
    """Test generating a prediction for a valid case."""
    
    def mock_get_case(db, case_id):
        return MockCase("Test description", None)
    
    # We must mock out the DB persistence to avoid hitting the DB
    def mock_create_prediction(db, prediction_data):
        from app.models.prediction import Prediction
        return Prediction(id=1, case_id="C-2026-9081", risk_level="HIGH")
    
    def mock_evaluate_alert(db, prediction):
        pass
    
    from app.crud import crud_case, crud_prediction
    from app.services import alert_service
    monkeypatch.setattr(crud_case, "get_case_by_case_id", mock_get_case)
    monkeypatch.setattr(crud_prediction, "create_prediction", mock_create_prediction)
    monkeypatch.setattr(alert_service, "evaluate_and_create_alert", mock_evaluate_alert)
    
    req = PredictRequest(case_id="C-2026-9081")
    predictor = MockPredictor()
    
    res = generate_prediction(None, req, predictor)
    
    assert res.case_id == "C-2026-9081"
    assert res.risk == "HIGH"
    assert len(res.predictions) == 2
    assert res.predictions[0].atm_id == "ATM-184"

def test_generate_prediction_invalid_case(monkeypatch):
    """Test that an invalid case raises 404."""
    
    def mock_get_case(db, case_id):
        return None
    
    from app.crud import crud_case
    monkeypatch.setattr(crud_case, "get_case_by_case_id", mock_get_case)
    
    req = PredictRequest(case_id="UNKNOWN")
    predictor = MockPredictor()
    
    with pytest.raises(HTTPException) as excinfo:
        generate_prediction(None, req, predictor)
    
    assert excinfo.value.status_code == 404
    assert excinfo.value.detail == "Case not found"
