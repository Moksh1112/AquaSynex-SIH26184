import pytest

# --- Tests that REQUIRE PostgreSQL/PostGIS (Blocked) ---

@pytest.mark.skip(reason="Requires live PostgreSQL/PostGIS environment. Database is not available on this host.")
def test_create_prediction_integration():
    """Integration test: actual database insert for Prediction and Candidates."""
    pass

@pytest.mark.skip(reason="Requires live PostgreSQL/PostGIS environment. Database is not available on this host.")
def test_read_prediction_integration():
    """Integration test: actual database read for Prediction and Candidates."""
    pass
