from sqlalchemy.orm import Session
from app.models.prediction import Prediction, PredictionCandidate
from app.schemas.prediction import PredictResponse

def create_prediction(db: Session, prediction_data: PredictResponse) -> Prediction:
    # 1. Create Prediction record
    db_prediction = Prediction(
        case_id=prediction_data.case_id,
        risk_level=prediction_data.risk,
        time_window=prediction_data.time_window,
        explanation={"reasons": prediction_data.explanation}
    )
    db.add(db_prediction)
    db.flush() # flush to get db_prediction.id

    # 2. Create PredictionCandidate records
    candidates = []
    for p in prediction_data.predictions:
        cand = PredictionCandidate(
            prediction_id=db_prediction.id,
            atm_id=p.atm_id,
            rank=p.rank,
            probability=p.probability,
            risk=p.risk
        )
        candidates.append(cand)
    
    db.add_all(candidates)
    db.commit()
    db.refresh(db_prediction)
    return db_prediction
