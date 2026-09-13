import pytest
from fastapi import HTTPException
from app.services.alert_service import map_risk_to_priority, evaluate_and_create_alert, update_alert
from app.schemas.alert import AlertUpdateStatus, AlertStatusEnum
from app.models.prediction import Prediction
from app.models.alert import Alert

def test_map_risk_to_priority():
    assert map_risk_to_priority("HIGH") == "P1"
    assert map_risk_to_priority("high") == "P1"
    assert map_risk_to_priority("MEDIUM") == "P2"
    assert map_risk_to_priority("LOW") == "P3"
    assert map_risk_to_priority("UNKNOWN") == "P4"
    assert map_risk_to_priority(None) == "P4"

def test_evaluate_and_create_alert_new(monkeypatch):
    """Test creating a new alert when one doesn't exist."""
    
    def mock_get_alert(db, prediction_id):
        return None
        
    def mock_create_alert(db, alert_in):
        return Alert(
            id=1,
            case_id=alert_in.case_id,
            prediction_id=alert_in.prediction_id,
            priority=alert_in.priority,
            status=alert_in.status
        )
        
    from app.crud import crud_alert
    monkeypatch.setattr(crud_alert, "get_alert_by_prediction_id", mock_get_alert)
    monkeypatch.setattr(crud_alert, "create_alert", mock_create_alert)
    
    pred = Prediction(id=10, case_id="C-1", risk_level="HIGH")
    alert = evaluate_and_create_alert(None, pred)
    
    assert alert.id == 1
    assert alert.priority == "P1"
    assert alert.status == AlertStatusEnum.OPEN

def test_evaluate_and_create_alert_duplicate(monkeypatch):
    """Test idempotency: returning existing alert."""
    
    existing = Alert(id=2, case_id="C-1", prediction_id=10, priority="P1", status=AlertStatusEnum.OPEN)
    
    def mock_get_alert(db, prediction_id):
        return existing
        
    from app.crud import crud_alert
    monkeypatch.setattr(crud_alert, "get_alert_by_prediction_id", mock_get_alert)
    
    pred = Prediction(id=10, case_id="C-1", risk_level="HIGH")
    alert = evaluate_and_create_alert(None, pred)
    
    assert alert.id == 2
    assert alert is existing

def test_update_alert_valid(monkeypatch):
    
    def mock_update(db, alert_id, status_in):
        return Alert(id=alert_id, status=status_in.status)
        
    from app.crud import crud_alert
    monkeypatch.setattr(crud_alert, "update_alert_status", mock_update)
    
    updated = update_alert(None, 1, AlertUpdateStatus(status=AlertStatusEnum.ACKNOWLEDGED))
    assert updated.status == AlertStatusEnum.ACKNOWLEDGED

def test_update_alert_not_found(monkeypatch):
    
    def mock_update(db, alert_id, status_in):
        return None
        
    from app.crud import crud_alert
    monkeypatch.setattr(crud_alert, "update_alert_status", mock_update)
    
    with pytest.raises(HTTPException) as excinfo:
        update_alert(None, 99, AlertUpdateStatus(status=AlertStatusEnum.RESOLVED))
        
    assert excinfo.value.status_code == 404
