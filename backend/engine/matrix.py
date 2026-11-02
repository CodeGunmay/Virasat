"""Walking-time matrix for Virasat.

Precomputed site-to-site walking times, stored per city.
Used by the route optimizer to determine travel times between stops.

The matrix is read-only per city; adding a city is a data-only change.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import json

# In-production: this would be a database table or Redis cache.
# For the hackathon demo, we store it as a module-level dict and seed it
# from a computed source during setup.

# Matrix format: matrix[from_site_id][to_site_id] = minutes
# We also have a special entry for "start" and "end" points.

matrix: Dict[int, Dict[int, int]] = {}
start_legs: Dict[int, int] = {}  # from start point to site_id -> minutes


def init_matrix(site_ids: List[int]) -> None:
    """Initialize the walking-time matrix for a set of sites.

    In a production system, this would be precomputed using a routing service
    (OpenRouteService, OSRM, GraphHopper) and stored in the database.
    For the demo, we compute straight-line distances × detour factor and
    mark them as "estimated" in the UI.

    The detour factor accounts for the walled city's dense lane network
    (pols) where straight-line distance is a poor walking-time estimator.
    """
    # Compute pairwise walking times
    for i, from_site in enumerate(site_ids):
        matrix[from_site] = {}
        for j, to_site in enumerate(site_ids):
            if i == j:
                matrix[from_site][to_site] = 0
            else:
                # Use estimated walking time (straight-line × detour factor)
                # In production, this would call a routing API
                minutes = _estimate_walking_time(from_site, to_site)
                matrix[from_site][to_site] = minutes

    # Start-point legs are marked as estimated
    for site_id in site_ids:
        start_legs[site_id] = _estimate_walking_time(0, site_id)  # 0 = start point


def _estimate_walking_time(from_site_id: int, to_site_id: int) -> int:
    """Estimate walking time between two sites in minutes.

    Uses Haversine distance with a detour factor of 3.5 for pols.
    """
    from math import radians, sin, cos, sqrt, atan2
    from ..db.models import Site as SiteModel

    # Get coordinates
    from_stmt = select(SiteModel).where(SiteModel.id == from_site_id)
    from_result = db_execute(from_stmt)
    from_site = from_result.scalar_one_or_none()

    to_stmt = select(SiteModel).where(SiteModel.id == to_site_id)
    to_result = db_execute(to_stmt)
    to_site = to_result.scalar_one_or_none()

    if not from_site or not to_site:
        return 5  # fallback minimum

    lat1, lng1 = float(from_site.location.y), float(from_site.location.x)
    lat2, lng2 = float(to_site.location.y), float(to_site.location.x)

    # Haversine distance
    R = 6371000  # Earth radius in meters
    lat1_r, lng1_r = radians(lat1), radians(lng1)
    lat2_r, lng2_r = radians(lat2), radians(lng2)
    dlat = lat2_r - lat1_r
    dlng = lng2_r - lng1_r

    a = sin(dlat / 2) ** 2 + cos(lat1_r) * cos(lat2_r) * sin(dlng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance_m = R * c

    # Apply detour factor for pols (walled city lanes)
    # Straight-line is rarely walkable; real paths are 2-5× longer
    detour_factor = 3.5
    walked_m = distance_m * detour_factor

    # Walking speed: 5 km/h = 83.3 m/min
    speed_mpm = 83.3
    minutes = walked_m / speed_mpm
    return max(round(minutes), 2)  # minimum 2 minutes


def db_execute(stmt) -> any:
    """Execute a SQLAlchemy statement (mock for standalone usage).

    In production, this would use the actual DB session.
    """
    # This is a placeholder; the real engine passes a session
    pass


def get_walking_time(from_site_id: int, to_site_id: int) -> int:
    """Get precomputed walking time between two sites in minutes.

    Args:
        from_site_id: Site ID (0 = start point)
        to_site_id: Site ID

    Returns:
        Walking time in minutes.
    """
    if from_site_id == 0:
        # Start point to site
        return start_legs.get(to_site_id, 5)
    if to_site_id == 0:
        # Site to start point (return)
        return start_legs.get(from_site_id, 5)
    return matrix.get(from_site_id, {}).get(to_site_id, 5)


def is_cached() -> bool:
    """Check whether the matrix has been initialized (seeded from real data)."""
    return len(matrix) > 0