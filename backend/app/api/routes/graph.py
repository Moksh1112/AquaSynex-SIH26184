from fastapi import APIRouter

router = APIRouter()

@router.get("/graph/{case_id}")
def get_graph(case_id: str):
    return {"status": "stub", "message": "Graph data not implemented yet"}
