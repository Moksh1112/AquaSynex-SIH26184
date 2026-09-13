from typing import Generator, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.security import decode_access_token
from app.crud.crud_user import get_user_by_username
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Decode the JWT and return the authenticated User. Raises 401 on failure."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    return user

def require_role(*allowed_roles: str):
    """
    Returns a dependency that checks the current user's role against the allowed list.
    Raises 403 Forbidden if the user's role is not permitted.
    """
    def role_checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        user_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        if user_role not in allowed_roles:
            from app.services.audit_service import log_audit_event
            log_audit_event(db, action="ACCESS_DENIED", resource=f"role_required:{allowed_roles}", status="DENIED", user_id=current_user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker
