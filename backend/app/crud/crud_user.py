from sqlalchemy.orm import Session
from typing import Optional
from app.models.user import User

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()
