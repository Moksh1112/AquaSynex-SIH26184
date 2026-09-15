from sqlalchemy import Column, Integer, String, Float
from app.db.base import Base


class PoliceStation(Base):
    """
    Represents a local police station used for Response Intelligence enrichment.
    Coordinates are stored as plain Float columns (same pattern as ATM).
    Distance to predicted ATM locations is computed on-the-fly via PostGIS
    ST_DistanceSphere, which accepts plain lat/lon values.
    """
    __tablename__ = "police_stations"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, unique=True, index=True, nullable=False)
    station_name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    jurisdiction_code = Column(String, nullable=True)   # mirrors routing_service codes
    address = Column(String, nullable=True)
