from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.prediction import PredictRequest, PredictResponse
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
    except Exception:
        from app.services.audit_service import log_audit_event
        log_audit_event(db, action="PREDICT", resource=f"case:{request.case_id}", status="FAILED", user_id=current_user.id)
        raise
