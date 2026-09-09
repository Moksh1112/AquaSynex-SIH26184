from fastapi import APIRouter

router = APIRouter()

@router.get("/locations")
def get_locations():
    return {"status": "stub", "message": "Locations not implemented yet"}
