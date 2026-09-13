import pytest

# --- Tests that REQUIRE PostgreSQL/PostGIS (Blocked) ---
from tests.db_utils import require_postgres
from app.db.session import SessionLocal
from app.models.prediction import Prediction, PredictionCandidate
import uuid

@require_postgres
def test_create_prediction_integration():
    """Integration test: actual database insert for Prediction and Candidates."""
    db = SessionLocal()
    try:
        pred = Prediction(case_id="C-2026-9081", risk_level="LOW", time_window="00:00-01:00", explanation={})
        db.add(pred)
        db.flush()
        
        cand = PredictionCandidate(prediction_id=pred.id, atm_id="ATM-MUM-01", rank=1, probability=0.9, risk="LOW")
        db.add(cand)
        db.flush()
        
        assert pred.id is not None
        assert cand.id is not None
    finally:
        db.rollback()
        db.close()

@require_postgres
def test_read_prediction_integration():
    """Integration test: actual database read for Prediction and Candidates."""
    db = SessionLocal()
    try:
        pred = db.query(Prediction).first()
        if pred:
            assert pred.case_id is not None
            cands = db.query(PredictionCandidate).filter(PredictionCandidate.prediction_id == pred.id).all()
            assert isinstance(cands, list)
    finally:
        db.close()
