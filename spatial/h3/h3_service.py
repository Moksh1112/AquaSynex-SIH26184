import logging

logger = logging.getLogger(__name__)

# Try to import h3, provide safe fallback if unavailable or API differs
try:
    import h3
    H3_AVAILABLE = True
except ImportError:
    H3_AVAILABLE = False
    logger.warning("H3 library not found. Falling back to mock H3 resolution.")

def lat_lon_to_h3(lat: float, lon: float, resolution: int = 8) -> str:
    """Convert latitude and longitude to an H3 cell index."""
    if H3_AVAILABLE:
        try:
            # Depending on h3 version, the function might be h3_to_geo or geo_to_h3 or latlng_to_cell
            if hasattr(h3, 'latlng_to_cell'):
                return h3.latlng_to_cell(lat, lon, resolution)
            else:
                return h3.geo_to_h3(lat, lon, resolution)
        except Exception as e:
            logger.error(f"H3 error: {e}")
            # Fall through to fallback
            
    # Safe fallback: create a string grid based on rounded lat/lon
    # A resolution of 8 is roughly 0.01 degrees in grid size
    grid_lat = round(lat, 2)
    grid_lon = round(lon, 2)
    return f"fallback_{grid_lat}_{grid_lon}"

def get_nearby_cells(h3_index: str, k: int = 1) -> list:
    """Get k-ring of nearby H3 cells."""
    if H3_AVAILABLE and not h3_index.startswith("fallback_"):
        try:
            if hasattr(h3, 'k_ring'):
                return list(h3.k_ring(h3_index, k))
            else:
                return list(h3.grid_disk(h3_index, k))
        except Exception as e:
            logger.error(f"H3 k-ring error: {e}")
            
    # Safe fallback for fallback indices: just return the index itself
    # and maybe some mocked neighbors if we wanted, but returning the index itself
    # will at least pull ATMs in the exact same 0.01 degree grid box.
    return [h3_index]
