# Security utilities (JWT, password hashing)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    raise NotImplementedError("Password verification not implemented yet")

def create_access_token(data: dict) -> str:
    raise NotImplementedError("Token generation not implemented yet")
