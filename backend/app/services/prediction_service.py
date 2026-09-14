from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.crud import crud_case, crud_prediction
from app.ml.predictor import Predictor
from app.schemas.prediction import PredictRequest, PredictResponse
from app.services import alert_service

def generate_prediction(db: Session, request: PredictRequest, predictor: Predictor) -> PredictResponse:
    # 1. Validate case_id exists
    case = crud_case.get_case_by_case_id(db, case_id=request.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # 2. Gather context data (in a real scenario, this fetches accounts, transactions, etc.)
    context_data = {
        "description": case.description,
        "reported_at": case.reported_at.isoformat() if case.reported_at else None
    }

    # 3. Call predictor
    prediction_response = predictor.predict(db=db, case_id=request.case_id, context_data=context_data)

    # 4. Persist Prediction and Candidates
    db_prediction = crud_prediction.create_prediction(db, prediction_response)

    # 5. Evaluate and trigger alert idempotently
    alert_service.evaluate_and_create_alert(db, db_prediction)

    # 6. Return exactly the frozen response
    return prediction_response
