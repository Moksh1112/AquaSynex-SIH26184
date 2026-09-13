from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.crud.crud_user import get_user_by_username
from app.core.security import verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.auth import TokenResponse
from app.services.audit_service import log_audit_event

def authenticate_user(db: Session, request: OAuth2PasswordRequestForm) -> TokenResponse:
    user = get_user_by_username(db, request.username)
    if not user:
        log_audit_event(db, action="LOGIN", resource=f"username:{request.username}", status="FAILED")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    if not verify_password(request.password, user.hashed_password):
        log_audit_event(db, action="LOGIN", resource=f"username:{request.username}", status="FAILED", user_id=user.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token = create_access_token(data={
        "sub": user.username,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role)
    })
    
    log_audit_event(db, action="LOGIN", resource=f"username:{request.username}", status="SUCCESS", user_id=user.id)
    
    return TokenResponse(access_token=token, token_type="bearer")
