"""
Police Station Response Intelligence Service
============================================
Provides three reusable, additive functions:

1. find_nearest_station  — PostGIS nearest-station lookup (same ST_DistanceSphere
                           pattern used in feature_engineering.py and
                           candidate_generation.py).
2. build_recommended_action — Deterministic, transparent text from existing
                               risk level + time_window. No ML model.
3. enrich_predictions   — Wraps each PredictionItem with a ResponseIntelligence
                           block. Failure in one candidate is isolated; the
                           full prediction is never aborted.

IMPORTANT: This module NEVER modifies prediction scores, ranking, or time_window.
           It reads routing_service.determine_jurisdiction() read-only.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.police_station import PoliceStation
from app.services.routing_service import determine_jurisdiction

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. Nearest Station
# ---------------------------------------------------------------------------

def find_nearest_station(
    db: Session,
    lat: float,
    lng: float,
) -> Optional[dict]:
    """
    Returns the geographically nearest police station to the given coordinates,
    using PostGIS ST_DistanceSphere — the same pattern as feature_engineering.py
    (L112-117) and candidate_generation.py (L82-86).

    Returns a dict with keys:
        station_id, station_name, latitude, longitude,
        jurisdiction_code, distance_km

    Returns None if no stations are seeded or the DB is unavailable.
    """
    try:
        target_point = func.ST_MakePoint(lng, lat)

        # Query all stations and compute distance to each, then order & take first
        stations = db.query(PoliceStation).all()
        if not stations:
            return None

        best: Optional[PoliceStation] = None
        best_dist_m: float = float('inf')

        for station in stations:
            dist_m = db.query(
                func.ST_DistanceSphere(
                    func.ST_MakePoint(station.longitude, station.latitude),
                    target_point
                )
            ).scalar()
            if dist_m is not None and dist_m < best_dist_m:
                best_dist_m = dist_m
                best = station

        if best is None:
            return None

        return {
            "station_id": best.station_id,
            "station_name": best.station_name,
            "latitude": best.latitude,
            "longitude": best.longitude,
            "jurisdiction_code": best.jurisdiction_code,
            "distance_km": round(best_dist_m / 1000.0, 2),
        }

    except Exception as exc:
        db.rollback()
        logger.warning("find_nearest_station failed for (%.4f, %.4f): %s", lat, lng, exc)
        return None


# ---------------------------------------------------------------------------
# 2. Recommended Action (deterministic — no ML)
# ---------------------------------------------------------------------------

def build_recommended_action(
    risk: str,
    time_window: str,
    station_name: Optional[str] = None,
) -> str:
    """
    Returns a human-readable recommended action string derived solely from the
    existing risk level and existing time_window.  No new ML model is used.

    risk values follow the existing convention: HIGH, CRITICAL, MEDIUM, LOW, UNKNOWN.
    time_window is the existing string from predict_time_window(), e.g. "18:00-20:00".
    station_name is inserted for clarity if available.
    """
    unit = station_name or "nearest response unit"
    risk_upper = (risk or "").upper()

    if risk_upper in ("HIGH", "CRITICAL"):
        return (
            f"Dispatch rapid response unit to {unit}. "
            f"Monitor predicted ATM during window {time_window}. "
            "Coordinate with cybercrime cell for real-time interception."
        )
    elif risk_upper == "MEDIUM":
        return (
            f"Alert {unit}. Increase ATM surveillance during window {time_window}. "
            "Prepare for potential intervention."
        )
    elif risk_upper == "LOW":
        return (
            f"Enhanced intelligence monitoring via {unit}. "
            f"Review suspicious activity during window {time_window}."
        )
    else:
        return "Response unit unavailable."


# ---------------------------------------------------------------------------
# 3. Enrichment — wraps Top-5 candidates without altering scores or ranking
# ---------------------------------------------------------------------------

def enrich_predictions(
    db: Session,
    predictions: list,
    time_window: str,
) -> list:
    """
    Accepts the existing list of prediction dicts/items (each having atm_id,
    probability, rank, latitude, longitude, risk) and returns a new list of
    dicts with an added 'response' key.

    Existing fields are NEVER modified.  If enrichment fails for a single
    candidate the candidate is still returned with a fallback response block.

    Args:
        db:          SQLAlchemy session (used for PostGIS nearest-station query)
        predictions: list of PredictionItem objects or dicts from predictor output
        time_window: existing time_window string from prediction

    Returns:
        list of dicts — original fields preserved + 'response' added
    """
    enriched = []

    for item in predictions:
        # Support both Pydantic models and plain dicts
        if hasattr(item, '__dict__'):
            base = {k: v for k, v in item.__dict__.items() if not k.startswith('_')}
        else:
            base = dict(item)

        lat = base.get('latitude', 0.0)
        lng = base.get('longitude', 0.0)
        risk = base.get('risk', 'UNKNOWN')

        response_block = {
            "nearest_station_id": None,
            "nearest_station_name": None,
            "station_latitude": None,
            "station_longitude": None,
            "distance_km": None,
            "jurisdiction": None,
            "recommended_action": "Response unit unavailable.",
        }

        try:
            station = find_nearest_station(db, lat, lng)
            jurisdiction = determine_jurisdiction(lat, lng)

            if station:
                response_block["nearest_station_id"] = station["station_id"]
                response_block["nearest_station_name"] = station["station_name"]
                response_block["station_latitude"] = station["latitude"]
                response_block["station_longitude"] = station["longitude"]
                response_block["distance_km"] = station["distance_km"]
                response_block["recommended_action"] = build_recommended_action(
                    risk=risk,
                    time_window=time_window,
                    station_name=station["station_name"],
                )

            response_block["jurisdiction"] = jurisdiction
        except Exception as exc:
            logger.warning(
                "enrich_predictions: enrichment failed for atm_id=%s: %s",
                base.get('atm_id', '?'), exc
            )
            # Leave fallback response_block as-is

        base["response"] = response_block
        enriched.append(base)

    return enriched
