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

    # 2. Ensure ATMs exist to avoid ForeignKeyViolation
    from app.models.atm import ATM
    added_atms = set()
    for p in prediction_data.predictions:
        if p.atm_id in added_atms:
            continue
        existing_atm = db.query(ATM).filter(ATM.atm_id == p.atm_id).first()
        if not existing_atm:
            new_atm = ATM(
                atm_id=p.atm_id,
                latitude=p.latitude,
                longitude=p.longitude,
                address="Unknown ATM (Discovered via Prediction)"
            )
            db.add(new_atm)
            added_atms.add(p.atm_id)

    db.flush() # Flush new ATMs

    # 3. Create PredictionCandidate records
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
