from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.prediction import (
    PredictRequest, PredictResponse,
    EnrichedPredictResponse, EnrichedPredictionItem, ResponseIntelligence,
)
from app.services import prediction_service
from app.ml.predictor import RealPredictor
from app.models.user import User, RoleEnum

router = APIRouter()
real_predictor = RealPredictor()

# Admin, Investigator, Analyst, and Bank Officer can use predictions
_predict_role = deps.require_role(
    RoleEnum.ADMIN.value,
    RoleEnum.I4C_ANALYST.value,
    RoleEnum.LEA_INVESTIGATOR.value,
    RoleEnum.BANK_OFFICER.value
)

@router.post("/predict", response_model=PredictResponse)
def predict(
    request: PredictRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(_predict_role)
):
    """
    Returns a prediction for the given case_id.
    """
    try:
        response = prediction_service.generate_prediction(db, request, real_predictor)
        from app.services.audit_service import log_audit_event
        log_audit_event(db, action="PREDICT", resource=f"case:{request.case_id}", status="SUCCESS", user_id=current_user.id)
        return response
    except Exception as e:
        from app.services.audit_service import log_audit_event
        log_audit_event(db, action="PREDICT", resource=f"case:{request.case_id}", status="FAILED", user_id=current_user.id)
        raise


@router.get("/predict/{case_id}/response-intelligence", response_model=EnrichedPredictResponse)
def get_response_intelligence(
    case_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(_predict_role)
):
    """
    Returns the latest prediction for the given case enriched with:
    - Nearest police station (name, distance)
    - Responsible jurisdiction (from existing routing_service)
    - Recommended action (deterministic, from risk + time_window)

    The existing prediction scores, ranking, and time_window are NEVER modified.
    Enrichment failure for a single candidate returns 'Response unit unavailable.'
    """
    from app.crud import crud_prediction, crud_case
    from app.services.police_station_service import enrich_predictions
    from app.services.audit_service import log_audit_event

    # 1. Verify case exists
    case = crud_case.get_case_by_case_id(db, case_id=case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # 2. Load latest prediction for the case
    db_prediction = crud_prediction.get_latest_prediction_by_case(db, case_id=case_id)
    if not db_prediction:
        raise HTTPException(status_code=404, detail="No prediction found for this case. Run POST /predict first.")

    # 3. Build base prediction items from stored candidates (unchanged scores/ranking)
    base_items = []
    for cand in sorted(db_prediction.candidates, key=lambda c: c.rank):
        atm = cand.atm
        base_items.append({
            "rank": cand.rank,
            "atm_id": cand.atm_id,
            "probability": cand.probability,
            "latitude": float(atm.latitude) if atm else 0.0,
            "longitude": float(atm.longitude) if atm else 0.0,
            "risk": cand.risk,
        })

    # 4. Enrich without touching scores/ranking
    enriched_dicts = enrich_predictions(db, base_items, db_prediction.time_window)

    # 5. Construct typed response
    enriched_items = []
    for d in enriched_dicts:
        r = d.get("response", {})
        enriched_items.append(EnrichedPredictionItem(
            rank=d["rank"],
            atm_id=d["atm_id"],
            probability=d["probability"],
            latitude=d["latitude"],
            longitude=d["longitude"],
            risk=d["risk"],
            response=ResponseIntelligence(
                nearest_station_id=r.get("nearest_station_id"),
                nearest_station_name=r.get("nearest_station_name"),
                station_latitude=r.get("station_latitude"),
                station_longitude=r.get("station_longitude"),
                distance_km=r.get("distance_km"),
                jurisdiction=r.get("jurisdiction"),
                recommended_action=r.get("recommended_action", "Response unit unavailable."),
            )
        ))

    log_audit_event(
        db, action="READ",
        resource=f"response-intelligence:{case_id}",
        status="SUCCESS", user_id=current_user.id
    )

    explanation = db_prediction.explanation or []
    if isinstance(explanation, dict):
        explanation = explanation.get("reasons", [])

    return EnrichedPredictResponse(
        case_id=case_id,
        risk=db_prediction.risk_level,
        time_window=db_prediction.time_window,
        predictions=enriched_items,
        explanation=explanation if isinstance(explanation, list) else [str(explanation)],
    )
