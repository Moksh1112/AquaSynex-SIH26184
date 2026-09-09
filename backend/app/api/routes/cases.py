from fastapi import APIRouter

router = APIRouter()

@router.get("/cases")
def get_cases():
    return {"status": "stub", "message": "List of cases not implemented yet"}

@router.get("/cases/{case_id}")
def get_case(case_id: str):
    return {"status": "stub", "message": f"Case {case_id} details not implemented yet"}
