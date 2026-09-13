import pytest
from app.core.config import settings
from sqlalchemy import create_engine

def is_postgres_available():
    if not settings.DATABASE_URL.startswith("postgresql"):
        return False
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect():
            return True
    except Exception:
        return False

require_postgres = pytest.mark.skipif(
    not is_postgres_available(),
    reason="Requires live PostgreSQL/PostGIS environment. Database is not available on this host."
)
