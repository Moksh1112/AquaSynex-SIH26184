from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geometry
from app.db.base import Base

class H3Cell(Base):
    __tablename__ = "h3_cells"

    id = Column(Integer, primary_key=True, index=True)
    h3_index = Column(String, unique=True, index=True, nullable=False)
    boundary = Column(Geometry(geometry_type='POLYGON', srid=4326), nullable=True)
