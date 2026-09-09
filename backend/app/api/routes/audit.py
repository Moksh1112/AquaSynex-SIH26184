from fastapi import APIRouter

router = APIRouter()

@router.get("/audit")
def get_audit():
    return {"status": "stub", "message": "Audit logs not implemented yet"}
