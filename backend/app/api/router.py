from fastapi import APIRouter
from app.api.routes import cases, predictions, locations, graph, alerts, auth, audit, evidence

api_router = APIRouter()
api_router.include_router(cases.router, tags=["cases"])
api_router.include_router(predictions.router, tags=["predictions"])
api_router.include_router(locations.router, tags=["locations"])
api_router.include_router(graph.router, tags=["graph"])
api_router.include_router(alerts.router, tags=["alerts"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(audit.router, tags=["audit"])
api_router.include_router(evidence.router, tags=["evidence"])
