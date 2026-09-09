from fastapi import APIRouter

router = APIRouter()

@router.get("/alerts")
def get_alerts():
    return {"status": "stub", "message": "Alerts list not implemented yet"}

@router.post("/alerts")
def create_alert():
    return {"status": "stub", "message": "Create alert not implemented yet"}
