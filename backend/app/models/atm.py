from sqlalchemy import Column, Integer, String, Float
from geoalchemy2 import Geometry
from app.db.base import Base

class ATM(Base):
    __tablename__ = "atms"

    id = Column(Integer, primary_key=True, index=True)
    atm_id = Column(String, unique=True, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    address = Column(String, nullable=True)
