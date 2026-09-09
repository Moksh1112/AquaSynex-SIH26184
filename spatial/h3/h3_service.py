def lat_lon_to_h3(lat: float, lon: float, resolution: int = 8) -> str:
    """Convert latitude and longitude to an H3 cell index."""
    raise NotImplementedError("Not implemented")

def get_nearby_cells(h3_index: str, k: int = 1) -> list:
    """Get k-ring of nearby H3 cells."""
    raise NotImplementedError("Not implemented")
