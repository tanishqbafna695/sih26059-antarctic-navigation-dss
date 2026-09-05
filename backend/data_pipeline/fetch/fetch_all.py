"""Pipeline orchestrator (Phase 4): fetch/synthesize -> QC -> regrid -> align
-> processed store -> feature store -> provenance manifests.

Usage:
  python -m backend.data_pipeline.fetch.fetch_all --dry-run
  python -m backend.data_pipeline.fetch.fetch_all --synthetic          # no accounts
  python -m backend.data_pipeline.fetch.fetch_all                      # real downloads
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import xarray as xr

from .. import features, provenance, synthetic as synth
from ..config import (ROOT, Credentials, get_product, get_scenario, load_config,
                      scenario_products)
from ..grid import common_grid_for_box, regrid_product
from ..qc import QCReport, run_qc
from ..temporal import align_time_axis, daily_timestamps, resample_daily
from . import cmems, era5, gebco, icebergs

_RAW_FILES = {
    "sic": ("sic_synthetic.nc", "sic/sic.nc"),
    "drift": ("drift_synthetic.nc", "drift/drift.nc"),
    "era5": ("era5_synthetic.nc", "era5/era5.nc"),
    "glorys12": ("glorys_synthetic.nc", "glorys12/glorys12.nc"),
}


def _open_products(raw_dir: Path, synthetic: bool) -> dict[str, xr.Dataset]:
    out = {}
    for pid, (syn, real) in _RAW_FILES.items():
        p = raw_dir / (syn if synthetic else real)
        if p.exists():
            ds = xr.open_dataset(p, engine="h5netcdf")
            ds = _normalize_raw(ds, pid)
            out[pid] = ds
    return out


def _normalize_raw(ds: xr.Dataset, pid: str) -> xr.Dataset:
    """Adapt real product files to what the pipeline expects.

    - ERA5 ships `valid_time` (and `number`/`expver` singleton coords) -> rename to `time`
    - Real OSI SAF / GLORYS12 files use lat/lon dims (rectilinear), even though the
      config may say `polar`; the regrid step auto-detects from the actual dims.
    """
    if "valid_time" in ds.dims:
        ds = ds.rename({"valid_time": "time"})
    # CDS ships ERA5 pressure as `msl`; pipeline/config uses the `mslp` alias.
    if pid == "era5" and "msl" in ds.data_vars and "mslp" not in ds.data_vars:
        ds = ds.rename({"msl": "mslp"})
    # Drop singleton ensemble/experiment coords that confuse regridding
    for coord in ("number", "expver"):
        if coord in ds.coords and coord not in ds.dims:
            ds = ds.drop_vars(coord)
    return ds


def _fetch_product(pid: str, scen: dict, pcfg: dict, raw_dir: Path,
                   creds: Credentials, dry_run: bool) -> None:
    # Idempotency: if the raw file already exists, skip the (possibly slow,
    # credential-gated) download and reuse what is on disk.
    if _raw_path(raw_dir, pid, synthetic=False).exists():
        print(f"[skip] {pid}: raw file already present")
        return
    access = pcfg["access"]
    if access == "cds":
        era5.fetch_era5(scen, pcfg, raw_dir, creds.cds_url, creds.cds_key, dry_run=dry_run)
    elif access == "cmems":
        if pid == "sic":
            cmems.fetch_osisaf_sic(scen, pcfg, raw_dir, creds, dry_run=dry_run)
        elif pid == "drift":
            cmems.fetch_osisaf_drift(scen, pcfg, raw_dir, creds, dry_run=dry_run)
        else:
            cmems.fetch_glorys12(scen, pcfg, raw_dir, creds, dry_run=dry_run)
    elif access == "http":
        if pid == "iceberg_byu_nic":
            icebergs.fetch_byu_nic(pcfg, raw_dir, dry_run=dry_run)
        else:
            icebergs.fetch_nic_recent(pcfg, raw_dir, dry_run=dry_run)
    elif access == "manual":
        gebco.fetch_gebco(pcfg, raw_dir, dry_run=dry_run)
    elif access == "derived":
        print(f"[skip] {pid}: derived in Phase 6 from {pcfg.get('source')}")
    else:
        raise ValueError(f"unknown access type {access!r} for {pid}")


def process_product(pid: str, ds: xr.Dataset, pcfg: dict, grid,
                    scen: dict) -> tuple[xr.Dataset, QCReport]:
    """Regrid a raw product to the common grid, QC it, align to a daily axis."""
    layout = pcfg["layout"]
    # Real CMEMS/OSI SAF files ship rectilinear lat/lon even when the config says
    # polar (the polar layout applies to the native OSI SAF format); detect from dims.
    probe = next(iter(ds.data_vars.values()))
    if any(d in probe.dims for d in ("latitude", "lat", "longitude", "lon")):
        layout = "rectilinear"
    src_epsg = pcfg.get("crs")
    out: dict = {}
    flags = [f"regridded to EPSG:{grid.epsg} {grid.spacing_km} km"]

    if pid == "sic":
        da = next(ds[k] for k in ("sea_ice_concentration", "sic", "ice_conc") if k in ds)
        vals = regrid_product(da, grid, layout, src_epsg=src_epsg)
        out["sic"] = (["time", "y", "x"], vals)
        if "landmask" in ds:
            lm = regrid_product(ds["landmask"].astype(float), grid, layout, src_epsg=src_epsg)
            out["landmask"] = (["y", "x"], lm > 0.5)
            flags.append("land cells masked")
    elif pid == "drift":
        vx = next(k for k in ("sea_ice_x_displacement", "drift_x", "dX_mean") if k in ds)
        vy = next(k for k in ("sea_ice_y_displacement", "drift_y", "dY_mean") if k in ds)
        out["drift_x"] = (["time", "y", "x"],
                          regrid_product(ds[vx], grid, layout, src_epsg=src_epsg))
        out["drift_y"] = (["time", "y", "x"],
                          regrid_product(ds[vy], grid, layout, src_epsg=src_epsg))
    elif pid == "era5":
        for v in pcfg["variables"]:
            name = v["cds"] if v["cds"] in ds else v["short"]
            out[v["short"]] = (["time", "y", "x"],
                               regrid_product(ds[name], grid, layout))
    elif pid == "glorys12":
        for v in pcfg["variables"]:
            out[v] = (["time", "y", "x"], regrid_product(ds[v], grid, layout))
    else:
        raise ValueError(f"no processing rule for product {pid!r}")

    time_vars = {k: v for k, v in out.items() if "time" in v[0]}
    static_vars = {k: v for k, v in out.items() if "time" not in v[0]}
    new = xr.Dataset(time_vars, coords={"time": ds["time"].values, "y": grid.y, "x": grid.x})

    # sub-daily (ERA5) -> daily means, then fill a continuous daily UTC axis
    # bounded by the ACTUAL data range (not the full scenario window), so
    # truncated windows (e.g. synthetic 5-day runs) stay honest.
    t_min = pd.Timestamp(ds["time"].values.min()).strftime("%Y-%m-%d")
    t_max = pd.Timestamp(ds["time"].values.max()).strftime("%Y-%m-%d")
    new = resample_daily(new)
    new = align_time_axis(new, t_min, t_max, freq="D")
    for k, v in static_vars.items():  # static vars keep their own dims
        new[k] = v

    new = new.assign_coords(lon=(("y", "x"), grid.lons()), lat=(("y", "x"), grid.lats()))
    new.attrs["epsg"] = grid.epsg
    new.attrs["spacing_km"] = grid.spacing_km
    new.attrs["scenario"] = scen["name"]

    qc_cfg = pcfg.get("qc") or {}
    values = new["sic"].values if pid == "sic" else next(iter(new.data_vars.values())).values
    qc = run_qc(pid, values, vmin=qc_cfg.get("vmin"), vmax=qc_cfg.get("vmax"), flags=flags)
    return new, qc


def run_pipeline(scenario_name: str, out_root: Path, product_ids: list[str] | None = None,
                 dry_run: bool = False, synthetic: bool = False,
                 synth_days: int | None = None, drift_period_days: float = 2.0) -> None:
    cfg = load_config()
    scen = get_scenario(cfg, scenario_name)
    grid = common_grid_for_box(scen["box"], **scen["grid"])
    creds = Credentials.from_env()

    raw_dir = out_root / ("synthetic/raw" if synthetic else "raw")
    processed_dir = out_root / "processed" / scenario_name
    manifests_dir = out_root / "manifests"
    ids = product_ids or scenario_products()

    if dry_run and not synthetic:
        print(f"Scenario: {scenario_name} ({scen['name']})")
        print(f"Box: {scen['box']}  Window: {scen['start']}..{scen['end']}")
        print(f"Grid: EPSG:{grid.epsg}, {grid.spacing_km} km, {grid.nx}x{grid.ny} cells")
        for pid in ids:
            pcfg = get_product(cfg, pid)
            ok = creds.for_access(pcfg["access"])
            status = "OK" if ok else ("MANUAL" if pcfg["access"] in ("manual", "derived") else "MISSING CREDS")
            print(f"  {pid:16s} {pcfg['access']:8s} {status}")
        print("\nSet CDSAPI_URL/CDSAPI_KEY (ERA5), CMEMS_USERNAME/CMEMS_PASSWORD "
              "(ocean+ice) env vars, then re-run without --dry-run.")
        return

    if synthetic:
        print(f"[synthetic] generating deterministic scenario {scenario_name!r} "
              f"({synth_days or 'full'} days)")
        synth.make_synthetic_products(scen, out_root / "synthetic", days=synth_days)
        dsets = _open_products(raw_dir, synthetic=True)
        ids = [p for p in ids if p in dsets]
    else:
        for pid in ids:
            pcfg = get_product(cfg, pid)
            _fetch_product(pid, scen, pcfg, raw_dir, creds, dry_run=False)
        dsets = _open_products(raw_dir, synthetic=False)

    processed_dir.mkdir(parents=True, exist_ok=True)
    for pid in ids:
        pcfg = get_product(cfg, pid)
        ds, qc = process_product(pid, dsets[pid], pcfg, grid, scen)
        out_path = processed_dir / f"{pid}.nc"
        ds.to_netcdf(out_path, engine="h5netcdf", invalid_netcdf=True)  # bool landmask
        manifest = provenance.new_manifest(
            pid, pcfg, [_raw_path(raw_dir, pid, synthetic)],
            qc, coverage={"start": scen["start"], "end": scen["end"]},
            preprocessing=["regrid to common grid", "resample to daily UTC",
                           "range/missing QC"],
            repo_root=ROOT, synthetic=synthetic,
        )
        provenance.write_manifest(manifest, manifests_dir)
        print(f"  processed {pid:10s} missing={qc.missing_rate:.3f} "
              f"out-of-range={qc.out_of_range_rate:.3f}")

    feature_path = processed_dir / "features.nc"
    store = features.build_feature_store(processed_dir, feature_path,
                                         product_ids=ids,
                                         drift_period_days=drift_period_days)
    fqc = QCReport(product="features", n_values=int(store.sic.size),
                   missing_rate=float(store.sic.isnull().mean().item()),
                   out_of_range_rate=0.0, flags=["merged product store"])
    provenance.write_manifest(
        provenance.new_manifest(
            "features", {"provider": "merged products (see per-product manifests)",
                         "license": "see per-product manifests"},
            [feature_path], fqc, coverage={"start": scen["start"], "end": scen["end"]},
            preprocessing=["merge processed products", "ice mask + edge distance"],
            repo_root=ROOT, synthetic=synthetic,
        ), manifests_dir)
    print(f"  feature store: {feature_path} ({store.sic.shape})")
    print(f"manifests: {manifests_dir}")


def _raw_path(raw_dir: Path, pid: str, synthetic: bool) -> Path:
    syn, real = _RAW_FILES[pid]
    return raw_dir / (syn if synthetic else real)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="SIH26059 data pipeline (Phase 4)")
    ap.add_argument("--scenario", default="bharati_maitri_2019_20")
    ap.add_argument("--products", nargs="*", default=None,
                    help="subset of product ids (default: sic drift era5 glorys12)")
    ap.add_argument("--dry-run", action="store_true", help="print plan, download nothing")
    ap.add_argument("--synthetic", action="store_true",
                    help="generate deterministic synthetic products (no accounts needed)")
    ap.add_argument("--synth-days", type=int, default=None,
                    help="truncate the synthetic window to N days (tests/demo)")
    ap.add_argument("--out-root", default=str(ROOT / "data"))
    args = ap.parse_args(argv)
    run_pipeline(args.scenario, Path(args.out_root), product_ids=args.products,
                 dry_run=args.dry_run, synthetic=args.synthetic,
                 synth_days=args.synth_days)


if __name__ == "__main__":
    main()