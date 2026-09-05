"""Common routing grid (EPSG:3412 polar stereographic) and regridding helpers.

All environmental products are regridded onto this one grid before feature
generation (Phase 4) and routing (Phase 12). Products in rectilinear
lon/lat (ERA5, GLORYS12) use RegularGridInterpolator; products already on a
polar-stereographic grid (OSI SAF SIC/drift) use scattered griddata over
their transformed lon/lat.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import xarray as xr
from scipy.interpolate import RegularGridInterpolator, griddata

from . import crs

DIM_ALIASES = {
    "latitude": ("latitude", "lat"),
    "longitude": ("longitude", "lon"),
    "y": ("y", "yc"),
    "x": ("x", "xc"),
}


def find_dim(da: xr.DataArray, candidates) -> str | None:
    for c in candidates:
        if c in da.dims:
            return c
    return None


@dataclass
class CommonGrid:
    epsg: int
    spacing_km: float
    x: np.ndarray  # 1-D metres, EPSG:3412 easting
    y: np.ndarray  # 1-D metres, EPSG:3412 northing

    @property
    def nx(self) -> int:
        return len(self.x)

    @property
    def ny(self) -> int:
        return len(self.y)

    def lons(self) -> np.ndarray:
        xx, yy = np.meshgrid(self.x, self.y)
        lon, _ = crs.ps_to_lonlat(xx, yy)
        return lon

    def lats(self) -> np.ndarray:
        xx, yy = np.meshgrid(self.x, self.y)
        _, lat = crs.ps_to_lonlat(xx, yy)
        return lat

    def as_dataset(self, time=None) -> xr.Dataset:
        ds = xr.Dataset(coords={"x": self.x, "y": self.y})
        ds = ds.assign_coords(lon=(("y", "x"), self.lons()),
                              lat=(("y", "x"), self.lats()))
        ds.attrs["epsg"] = self.epsg
        ds.attrs["spacing_km"] = self.spacing_km
        if time is not None:
            ds = ds.assign_coords(time=time)
        return ds


def common_grid_for_box(box: dict, spacing_km: float = 25.0, margin_km: float = 50.0,
                        epsg: int = 3412) -> CommonGrid:
    """Build the common routing grid covering a lon/lat box."""
    x0, x1, y0, y1 = crs.box_to_ps_extent(box, margin_km=margin_km)
    step = spacing_km * 1000.0
    x = np.arange(x0, x1 + step / 2.0, step)
    y = np.arange(y0, y1 + step / 2.0, step)
    return CommonGrid(epsg=epsg, spacing_km=spacing_km, x=x, y=y)


def regrid_rectilinear(values: np.ndarray, lat_1d: np.ndarray, lon_1d: np.ndarray,
                       grid: CommonGrid, method: str = "linear") -> np.ndarray:
    """values shape (..., nlat, nlon) on rectilinear lat/lon -> (..., ny, nx).

    Handles descending axes (CDS/ERA5 and CMEMS files commonly ship latitude
    descending north-to-south) by flipping them to ascending order.
    """
    values = np.asarray(values)
    lat = np.asarray(lat_1d)
    lon = np.asarray(lon_1d)
    flip_lat = lat[0] > lat[-1]
    flip_lon = lon[0] > lon[-1]
    if flip_lat:
        lat = lat[::-1]
        values = values[..., ::-1, :]
    if flip_lon:
        lon = lon[::-1]
        values = values[..., :, ::-1]
    lead = values.shape[:-2]
    if lead:  # RGI only allows trailing extra dims -> move leading dims to the back
        values = np.moveaxis(values, 0, -1)  # (lat, lon, T, ...)
    interp = RegularGridInterpolator(
        (lat, lon), values, method=method, bounds_error=False, fill_value=np.nan)
    pts = np.stack([grid.lats().ravel(), grid.lons().ravel()], axis=-1)
    out = interp(pts)  # (npts,) + lead
    if lead:
        out = np.moveaxis(out, -1, 0)  # lead + (npts,)
    return out.reshape(*lead, grid.ny, grid.nx)


def regrid_scattered(values: np.ndarray, src_lon: np.ndarray, src_lat: np.ndarray,
                     grid: CommonGrid, method: str = "linear") -> np.ndarray:
    """values 2-D on arbitrary (lon, lat) points -> (ny, nx). Loops over leading dims."""
    points = np.stack([np.asarray(src_lon).ravel(), np.asarray(src_lat).ravel()], axis=-1)
    xi = np.stack([grid.lons().ravel(), grid.lats().ravel()], axis=-1)
    vals = np.asarray(values)
    lead_shape = vals.shape[:-2]
    flat = vals.reshape(-1, vals.shape[-2] * vals.shape[-1])
    out = np.stack([griddata(points, row, xi, method=method, fill_value=np.nan)
                    for row in flat])
    return out.reshape(*lead_shape, grid.ny, grid.nx)


def regrid_product(da: xr.DataArray, grid: CommonGrid, layout: str,
                   src_epsg: int | None = None, method: str = "linear") -> np.ndarray:
    """Regrid a product DataArray onto the common grid.

    layout="rectilinear": 1-D latitude/longitude dims expected.
    layout="polar":       y/x dims on a polar-stereographic CRS (src_epsg).
    """
    if layout == "rectilinear":
        lat_dim = find_dim(da, DIM_ALIASES["latitude"])
        lon_dim = find_dim(da, DIM_ALIASES["longitude"])
        if lat_dim is None or lon_dim is None:
            raise ValueError(f"rectilinear layout needs lat/lon dims; got {list(da.dims)}")
        values = da.transpose(..., lat_dim, lon_dim)
        return regrid_rectilinear(values.values, da[lat_dim].values,
                                  da[lon_dim].values, grid, method=method)
    if layout == "polar":
        y_dim = find_dim(da, DIM_ALIASES["y"])
        x_dim = find_dim(da, DIM_ALIASES["x"])
        if y_dim is None or x_dim is None:
            raise ValueError(f"polar layout needs y/x dims; got {list(da.dims)}")
        if src_epsg is None:
            src_epsg = int(da.attrs.get("epsg", 3412))
        values = da.transpose(..., y_dim, x_dim)
        yy, xx = np.meshgrid(da[y_dim].values, da[x_dim].values, indexing="ij")
        if src_epsg == 3412:
            lon, lat = crs.ps_to_lonlat(xx, yy)
        else:
            lon, lat = crs.ps_to_lonlat_crs(xx, yy, src_epsg)
        return regrid_scattered(values.values, lon, lat, grid, method=method)
    raise ValueError(f"unknown layout {layout!r}")