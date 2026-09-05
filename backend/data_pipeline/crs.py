"""Coordinate reference helpers: WGS84 <-> Antarctic Polar Stereographic (EPSG:3412)."""
from __future__ import annotations

import numpy as np
from pyproj import Transformer

WGS84 = "EPSG:4326"
PS_SOUTH = "EPSG:3412"  # Antarctic Polar Stereographic (standard parallel 71S)

_wgs_to_ps = Transformer.from_crs(WGS84, PS_SOUTH, always_xy=True)
_ps_to_wgs = Transformer.from_crs(PS_SOUTH, WGS84, always_xy=True)


def lonlat_to_ps(lon, lat):
    """WGS84 lon/lat (degrees) -> EPSG:3412 metres (x easting, y northing)."""
    x, y = _wgs_to_ps.transform(lon, lat)
    return np.asarray(x), np.asarray(y)


def ps_to_lonlat(x, y):
    """EPSG:3412 metres -> WGS84 lon/lat (degrees)."""
    lon, lat = _ps_to_wgs.transform(x, y)
    return np.asarray(lon), np.asarray(lat)


def ps_to_lonlat_crs(x, y, from_epsg: int):
    """Convert from an arbitrary polar-stereographic CRS (e.g. 3413) to WGS84."""
    t = Transformer.from_crs(f"EPSG:{from_epsg}", WGS84, always_xy=True)
    lon, lat = t.transform(x, y)
    return np.asarray(lon), np.asarray(lat)


def box_to_ps_extent(box: dict, margin_km: float = 0.0):
    """Approx EPSG:3412 extent (x0, x1, y0, y1 in metres) covering a lon/lat box.

    Samples corners plus edge midpoints so curved polar-stereographic edges
    are roughly captured; the result is a bounding rectangle, which is fine
    for a routing domain.
    """
    south, north = box["south"], box["north"]
    west, east = box["west"], box["east"]
    lons = [west, (west + east) / 2.0, east]
    lats = [south, (south + north) / 2.0, north]
    xs, ys = [], []
    for lo in lons:
        for la in lats:
            x, y = lonlat_to_ps(lo, la)
            xs.extend(np.atleast_1d(x))
            ys.extend(np.atleast_1d(y))
    margin = margin_km * 1000.0
    return min(xs) - margin, max(xs) + margin, min(ys) - margin, max(ys) + margin