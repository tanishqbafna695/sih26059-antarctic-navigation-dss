"""Export the offline UI data bundle (Phase 17).

Reads RECORDED artifacts (routing / tradeoff / explanation / rerouting
reports + the real feature store for grid geometry) and writes everything
the frontend needs under frontend/src/data/:
  vessels.json, corridor.json, routes.json, tradeoff.json,
  explanations.json, status.json, bergs.json, ice_*.png (lon/lat
  plate-carree, transparent where no satellite data), hazard_45_pc7.png.

Usage:
    python scripts/ui/export_bundle.py [--out frontend/src/data]

Every number in the bundle traces to a recorded report or the feature
store. Map PNGs are reprojected from EPSG:3412 to lon/lat with linear
resampling so MapLibre (a lon/lat renderer) can overlay them exactly.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import xarray as xr
from PIL import Image
from scipy.interpolate import griddata

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STORE = ROOT / "data" / "processed" / "bharati_maitri_2019_20" / "features.nc"

LON_W, LON_E, LAT_S, LAT_N = 0.0, 95.0, -75.0, -55.0
PX_W, PX_H = 380, 80  # 0.25 deg plate-carree
EARTH_R_KM = 6371.0


def _load(name: str) -> dict:
    p = ROOT / "data" / name / "latest.json"
    if not p.exists():
        raise FileError(f"missing recorded report: {p}") from None
    return json.loads(p.read_text(encoding="utf-8"))


class FileError(Exception):
    pass


def _reproject_to_lonlat(values_2d: np.ndarray, lon2d: np.ndarray,
                         lat2d: np.ndarray) -> np.ndarray:
    """Scattered linear resample of a grid field onto plate-carree lon/lat."""
    ok = np.isfinite(values_2d) & np.isfinite(lon2d) & np.isfinite(lat2d)
    gx = np.linspace(LON_W, LON_E, PX_W)
    gy = np.linspace(LAT_S, LAT_N, PX_H)
    tx, ty = np.meshgrid(gx, gy)
    pts = np.stack([lon2d[ok], lat2d[ok]], axis=-1)
    out = griddata(pts, values_2d[ok].ravel(), (tx, ty), method="linear",
                   fill_value=np.nan)
    return out  # rows south -> north


def _ice_png(sic_ll: np.ndarray, path: Path) -> None:
    """White ice over transparent background; grey where no data."""
    img = Image.new("RGBA", (PX_W, PX_H), (58, 63, 77, 255))  # no-data grey
    px = img.load()
    for j in range(PX_H):
        for i in range(PX_W):
            v = sic_ll[PX_H - 1 - j, i]  # PNG row 0 = north
            if not np.isfinite(v):
                continue
            t = float(np.clip(v, 0.0, 1.0))
            r = round(29 + (238 - 29) * t)
            g = round(78 + (246 - 78) * t)
            b = round(137 + (255 - 137) * t)
            px[i, j] = (r, g, b, 255)
    img.save(path)


def _hazard_png(hz_ll: np.ndarray, path: Path) -> None:
    """Transparent green->red risk overlay."""
    img = Image.new("RGBA", (PX_W, PX_H), (0, 0, 0, 0))
    px = img.load()
    for j in range(PX_H):
        for i in range(PX_W):
            v = hz_ll[PX_H - 1 - j, i]
            if not np.isfinite(v):
                continue
            t = float(np.clip(v, 0.0, 1.0))
            px[i, j] = (round(255 * t), round(200 * (1 - t)), 60, 110)
    img.save(path)


def _circle_poly(lon: float, lat: float, radius_km: float, n: int = 48) -> list:
    pts = []
    for k in range(n + 1):
        a = 2 * math.pi * k / n
        dn, de = radius_km * math.cos(a), radius_km * math.sin(a)
        la = lat + math.degrees(dn / EARTH_R_KM)
        lo = lon + math.degrees(de / (EARTH_R_KM * math.cos(math.radians(lat))))
        pts.append([round(lo, 4), round(la, 4)])
    return pts


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description="Phase 17 UI bundle export")
    ap.add_argument("--out", default=str(ROOT / "frontend" / "src" / "data"))
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    routing = _load("routing")
    tradeoff = _load("tradeoff")
    explanation = _load("explanation")
    rerouting = _load("rerouting")

    ds = xr.open_dataset(STORE, engine="h5netcdf")
    lon2d = np.asarray(ds["lon"].values)
    lat2d = np.asarray(ds["lat"].values)

    def cell_lonlat(y: int, x: int) -> list:
        return [round(float(lon2d[y, x]), 4), round(float(lat2d[y, x]), 4)]

    # ---- vessels + corridor ----
    vessels = {
        "open_water_rv": {"name": "Open Water RV", "class": "Open Water"},
        "polar_class_pc7": {"name": "Polar Class PC7", "class": "PC7"},
        "polar_class_pc1": {"name": "Icebreaker PC1", "class": "PC1"},
    }
    (out / "vessels.json").write_text(json.dumps(vessels, indent=1))
    (out / "corridor.json").write_text(json.dumps({
        "from": {"name": "Bharati", "lat": -69.41, "lon": 76.19},
        "to": {"name": "Maitri", "lat": -70.77, "lon": 11.73},
        "bbox": [[LON_W, LAT_S], [LON_E, LAT_N]],
        "note": "Demo corridor is fixed in Phase 17; free origin/destination "
                "selection arrives with the Phase 18 API.",
    }, indent=1))

    # ---- routes (GeoJSON LineStrings in lon/lat) ----
    routes: dict = {"plan45": {}, "rerouteA": {}, "rerouteB": {}}
    vplan = routing["vessels"]
    for vid in ("polar_class_pc7", "polar_class_pc1"):
        routes["plan45"][vid] = {}
        for name, r in vplan[vid]["routes"].items():
            routes["plan45"][vid][name] = {
                "coords": [cell_lonlat(y, x) for y, x in r["path_xy"]],
                "time_h": r["travel_time_h"], "fuel_l": r["fuel_liters"],
                "risk": r["mean_hazard"], "ice_exp": r["ice_exposure_frac"],
            }
    for case, key in (("A. CONTROL (observations only)", "rerouteA"),
                      ("B. SC-5 (fresh iceberg fix on course, ASSUMED)", "rerouteB")):
        c = rerouting["cases"][case]
        entry: dict = {"outcome": c["outcome"], "trigger": c["changes"]["trigger_text"]}
        if c.get("outcome") not in ("COMPLETE", "NO_ROUTE"):
            full_old = [cell_lonlat(y, x) for y, x in
                        vplan["polar_class_pc7"]["routes"]["safest"]["path_xy"]]
            cur_ll = cell_lonlat(*c["current_cell"])
            entry["old_remaining"] = full_old[full_old.index(cur_ll):]
            entry["new"] = {}
            for name, r in c["new_routes"].items():
                entry["new"][name] = {
                    "coords": [cell_lonlat(y, x) for y, x in r["path_xy"]],
                    "time_h": r["travel_time_h"], "fuel_l": r["fuel_liters"],
                    "risk": r["mean_hazard"], "ice_exp": r["ice_exposure_frac"],
                }
            entry["winner"] = c["new_recommendation"]["recommended"]
        routes[key] = entry
    (out / "routes.json").write_text(json.dumps(routes, indent=1))

    # ---- tradeoff + explanations + status ----
    (out / "tradeoff.json").write_text(json.dumps(tradeoff["vessels"], indent=1))
    (out / "explanations.json").write_text(json.dumps(
        {v: t["explanation"] for v, t in explanation["vessels"].items()}, indent=1))
    notices = {}
    for case, key in (("A. CONTROL (observations only)", "rerouteA"),
                      ("B. SC-5 (fresh iceberg fix on course, ASSUMED)", "rerouteB")):
        c = rerouting["cases"][case]
        notices[key] = {
            "outcome": c.get("outcome"),
            "trigger": c.get("changes", {}).get("trigger_text", ""),
            "change_text": (c.get("change_explanation") or {}).get("text", ""),
            "new_headline": (c.get("new_explanation") or {}).get("headline", ""),
        }
    (out / "notices.json").write_text(json.dumps(notices, indent=1))
    pc7 = tradeoff["vessels"]["polar_class_pc7"]["comparison"]
    (out / "status.json").write_text(json.dumps({
        "depart_date": pc7["depart_date"],
        "confidence": pc7["confidence"],
        "ocean_source": vplan["polar_class_pc7"]["ocean_source_day0"],
        "sources": ["OSI SAF SIC (CC-BY-4.0)", "ERA5 (Copernicus licence)",
                    "GLORYS12 fallback: wind-driven estimate (documented gap)"],
        "honesty": ("Research prototype decision support. Modeled risk is "
                    "not a guarantee of safe navigation."),
    }, indent=1))

    # ---- icebergs: fixes + danger-buffer polygons ----
    bergs = []
    for b in routing.get("icebergs_assumed", []):
        unc = float(b.get("uncertainty_km", 1.0))
        bergs.append({"lon": b["lon"], "lat": b["lat"],
                      "label": "assumed demo fix",
                      "buffer_poly": [_circle_poly(b["lon"], b["lat"], 5.0 + 3.0 * unc)]})
    inj = rerouting.get("injected_fix_assumed")
    if inj:
        bergs.append({"lon": inj["lon"], "lat": inj["lat"],
                      "label": "ASSUMED SC-5 injection (day 50)",
                      "buffer_poly": [_circle_poly(inj["lon"], inj["lat"],
                                                  5.0 + 3.0 * float(inj["uncertainty_km"]))]})
    (out / "bergs.json").write_text(json.dumps(bergs, indent=1))

    # ---- map PNGs ----
    for day, fname in ((45, "ice_45.png"), (50, "ice_50.png"),
                       (65, "ice_65.png"), (70, "ice_70.png")):
        sic = np.asarray(ds["sic"].values[int(day)], dtype=float)
        _ice_png(_reproject_to_lonlat(sic, lon2d, lat2d), out / fname)
    # hazard day-45 PC7 (recompute via backend for exactness)
    from backend.routing.costs import build_day_fields
    from backend.vessel import VesselRegistry
    prof = VesselRegistry().get_profile("polar_class_pc7")
    hf = build_day_fields(ds, 45, prof,
                          icebergs=routing.get("icebergs_assumed", []))
    _hazard_png(_reproject_to_lonlat(hf["hazard_total"], lon2d, lat2d),
                out / "hazard_45_pc7.png")
    ds.close()
    print(f"bundle written to {out} "
          f"({len(list(out.iterdir()))} files)")


if __name__ == "__main__":
    main()
