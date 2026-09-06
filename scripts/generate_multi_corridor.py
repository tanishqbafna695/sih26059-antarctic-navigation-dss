"""Generate synthetic multi-corridor data for the enhanced UI.

Creates route data, tradeoff comparisons, explanations, and status
for 4 Antarctic corridors. Ice PNGs are shared across corridors
(viewed through different bounding boxes).
"""
import json, math, os, numpy as np

np.random.seed(42)

# ── Corridor definitions ────────────────────────────────────────
CORRIDORS = {
    "bharati_maitri": {
        "name": "Bharati -> Maitri",
        "from": {"name": "Bharati", "lat": -69.41, "lon": 76.19},
        "to": {"name": "Maitri", "lat": -70.77, "lon": 11.73},
        "bbox": [[0.0, -75.0], [95.0, -55.0]],
        "distance_km": 4247,
        "base_time_h": {"fastest": 291.1, "safest": 291.9, "balanced": 291.8},
        "base_fuel_l": {"fastest": 154769, "safest": 153628, "balanced": 153590},
        "base_risk": {"fastest": 0.0010, "safest": 0.00096, "balanced": 0.00096},
        "ice_exp": {"fastest": 0.105, "safest": 0.078, "balanced": 0.078},
        "winner": "safest",
    },
    "mcmurdo_halley": {
        "name": "McMurdo -> Halley VI",
        "from": {"name": "McMurdo", "lat": -77.85, "lon": 166.67},
        "to": {"name": "Halley VI", "lat": -75.58, "lon": -26.65},
        "bbox": [[-35.0, -82.0], [175.0, -58.0]],
        "distance_km": 7850,
        "base_time_h": {"fastest": 502.3, "safest": 518.7, "balanced": 510.2},
        "base_fuel_l": {"fastest": 287450, "safest": 271200, "balanced": 278900},
        "base_risk": {"fastest": 0.0018, "safest": 0.0011, "balanced": 0.0013},
        "ice_exp": {"fastest": 0.223, "safest": 0.165, "balanced": 0.189},
        "winner": "safest",
    },
    "neumayer_syowa": {
        "name": "Neumayer -> Syowa",
        "from": {"name": "Neumayer III", "lat": -70.65, "lon": -8.27},
        "to": {"name": "Syowa", "lat": -69.00, "lon": 39.58},
        "bbox": [[-15.0, -78.0], [50.0, -60.0]],
        "distance_km": 3390,
        "base_time_h": {"fastest": 234.5, "safest": 242.1, "balanced": 238.8},
        "base_fuel_l": {"fastest": 128900, "safest": 124500, "balanced": 126200},
        "base_risk": {"fastest": 0.00085, "safest": 0.00062, "balanced": 0.00071},
        "ice_exp": {"fastest": 0.142, "safest": 0.098, "balanced": 0.118},
        "winner": "safest",
    },
    "mawson_davis": {
        "name": "Mawson -> Davis",
        "from": {"name": "Mawson", "lat": -67.60, "lon": 62.88},
        "to": {"name": "Davis", "lat": -68.58, "lon": 77.97},
        "bbox": [[55.0, -75.0], [85.0, -60.0]],
        "distance_km": 1120,
        "base_time_h": {"fastest": 89.2, "safest": 91.5, "balanced": 90.3},
        "base_fuel_l": {"fastest": 42300, "safest": 40800, "balanced": 41500},
        "base_risk": {"fastest": 0.00042, "safest": 0.00031, "balanced": 0.00036},
        "ice_exp": {"fastest": 0.085, "safest": 0.052, "balanced": 0.067},
        "winner": "fastest",
    },
}

VESSELS = {
    "polar_class_pc7": {"name": "Polar Class PC7", "class": "PC7",
        "speed_kn": 14.5, "fuel_rate_l_h": 531},
    "polar_class_pc1": {"name": "Icebreaker PC1", "class": "PC1",
        "speed_kn": 16.0, "fuel_rate_l_h": 590},
    "open_water_rv": {"name": "Open Water RV", "class": "None",
        "speed_kn": 12.0, "fuel_rate_l_h": 410},
}

PRIORITY_PROFILES = {
    "balanced": {"time": 0.33, "fuel": 0.33, "risk": 0.34},
    "safety_first": {"time": 0.1, "fuel": 0.2, "risk": 0.7},
    "time_first": {"time": 0.7, "fuel": 0.15, "risk": 0.15},
    "fuel_saver": {"time": 0.2, "fuel": 0.6, "risk": 0.2},
}

# ── Route coordinate generation ─────────────────────────────────
def gen_route_coords(frm, to, n=80, curvature=0.15, seed=0):
    """Generate a plausible Antarctic route with curvature."""
    rng = np.random.RandomState(seed)
    lon0, lat0 = frm["lon"], frm["lat"]
    lon1, lat1 = to["lon"], to["lat"]
    t = np.linspace(0, 1, n)
    # Base great-circle approximation with curvature
    mid_lon = (lon0 + lon1) / 2
    mid_lat = min(lat0, lat1) - abs(curvature * (lon1 - lon0) * 0.3)
    # Quadratic bezier
    lons = (1-t)**2 * lon0 + 2*(1-t)*t * mid_lon + t**2 * lon1
    lats = (1-t)**2 * lat0 + 2*(1-t)*t * mid_lat + t**2 * lat1
    # Add small realistic perturbations (ice avoidance)
    lons += rng.normal(0, 0.3, n).cumsum() * 0.02
    lats += rng.normal(0, 0.2, n).cumsum() * 0.015
    return [[float(round(lon, 4)), float(round(lat, 4))] for lon, lat in zip(lons, lats)]

def gen_route_variations(frm, to, base_coords, route_type, seed=0):
    """Generate fastest/safest/balanced variants."""
    rng = np.random.RandomState(seed)
    coords_list = []
    for i, (rtype, shift) in enumerate([
        ("fastest", 0.0),
        ("safest", 0.08),
        ("balanced", 0.04),
    ]):
        n = len(base_coords)
        t = np.linspace(0, 1, n)
        offset = shift * np.sin(t * np.pi) * rng.uniform(0.5, 1.5)
        coords = [[round(c[0] + offset[j] * 0.5, 4),
                    round(c[1] - abs(offset[j]) * 0.3, 4)]
                  for j, c in enumerate(base_coords)]
        coords_list.append(coords)
    return {
        "fastest": {"coords": coords_list[0]},
        "safest": {"coords": coords_list[1]},
        "balanced": {"coords": coords_list[2]},
    }

# ── Generate all data ──────────────────────────────────────────
OUTPUT_DIR = "frontend/src/data/corridors"
os.makedirs(OUTPUT_DIR, exist_ok=True)

all_corridors_summary = []

for cid, cdef in CORRIDORS.items():
    cdir = os.path.join(OUTPUT_DIR, cid)
    os.makedirs(cdir, exist_ok=True)

    frm, to = cdef["from"], cdef["to"]

    # Generate route coordinates
    base = gen_route_coords(frm, to, n=80, seed=hash(cid) % 1000)
    routes = gen_route_variations(frm, to, base, cid, seed=hash(cid) % 1000)

    # Write routes.json
    routes_data = {"plan45": {"polar_class_pc7": routes}}
    with open(os.path.join(cdir, "routes.json"), "w") as f:
        json.dump(routes_data, f, indent=2)

    # Generate tradeoff for all vessels
    tradeoff = {}
    for vid, vdef in VESSELS.items():
        scale = vdef["speed_kn"] / 14.5  # normalize to PC7
        rows = []
        for rtype in ["fastest", "safest", "balanced"]:
            t_h = round(cdef["base_time_h"][rtype] / scale + np.random.uniform(-2, 2), 1)
            f_l = round(cdef["base_fuel_l"][rtype] / scale + np.random.uniform(-500, 500), 1)
            risk = round(cdef["base_risk"][rtype] * scale + np.random.uniform(-0.0001, 0.0001), 6)
            ice = round(cdef["ice_exp"][rtype] * scale + np.random.uniform(-0.01, 0.01), 4)
            berg = round(abs(np.random.uniform(0.0001, 0.0005)), 6)
            rows.append({
                "route": rtype,
                "travel_time_h": t_h,
                "fuel_liters": f_l,
                "mean_hazard": max(risk, 0.0001),
                "max_hazard": max(risk * 2.3, 0.001),
                "ice_exposure_frac": max(ice, 0.01),
                "mean_iceberg_hazard": berg,
            })

        winner = min(rows, key=lambda r: r["mean_hazard"])["route"]
        recs = {}
        for pname in PRIORITY_PROFILES:
            prof = PRIORITY_PROFILES[pname]
            scores = []
            for r in rows:
                score = (prof["time"] * r["travel_time_h"] / 500 +
                         prof["fuel"] * r["fuel_liters"] / 200000 +
                         prof["risk"] * r["mean_hazard"] / 0.002)
                scores.append((score, r["route"]))
            scores.sort()
            recs[pname] = {"recommended": scores[0][1]}

        conf = round(0.10 + np.random.uniform(-0.02, 0.02), 2)
        tradeoff[vid] = {
            "comparison": {
                "routes_available": True,
                "rows": rows,
                "confidence": {
                    "overall_confidence": conf,
                    "status_label": "DEGRADED" if conf < 0.3 else "MODERATE" if conf < 0.6 else "GOOD",
                },
            },
            "recommendations": recs,
        }

        # Also handle no-route for Open Water RV on longer corridors
        if vid == "open_water_rv" and cdef["distance_km"] > 5000:
            tradeoff[vid] = {
                "comparison": {
                    "routes_available": False,
                    "reason": "Open-water vessel exceeds safe operational range for this corridor (>5000 km through heavy ice)",
                    "rows": [],
                    "confidence": {"overall_confidence": 0.0, "status_label": "NO ROUTE"},
                },
                "recommendations": {},
            }

    with open(os.path.join(cdir, "tradeoff.json"), "w") as f:
        json.dump(tradeoff, f, indent=2)

    # Generate explanations
    explanations = {}
    for vid in VESSELS:
        if vid == "open_water_rv" and cdef["distance_km"] > 5000:
            explanations[vid] = {
                "explained": False,
                "reason": "No route found — vessel not rated for this corridor",
            }
            continue
        explanations[vid] = {
            "explained": True,
            "headline": f"The {VESSELS[vid]['name']} should take the safest route on the {cdef['name']} corridor.",
            "strengths": [
                f"Lowest hazard score ({tradeoff[vid]['comparison']['rows'][1]['mean_hazard']:.4f})",
                f"Best ice avoidance ({tradeoff[vid]['comparison']['rows'][1]['ice_exposure_frac']*100:.1f}% exposure)",
                "Passes through known open-water leads",
            ],
            "prices": [
                f"+{tradeoff[vid]['comparison']['rows'][1]['travel_time_h'] - tradeoff[vid]['comparison']['rows'][0]['travel_time_h']:.1f}h vs fastest",
                f"+{abs(tradeoff[vid]['comparison']['rows'][1]['fuel_liters'] - tradeoff[vid]['comparison']['rows'][0]['fuel_liters']):.0f}L vs cheapest fuel option",
            ],
            "vessel_statement": f"The {VESSELS[vid]['name']} ({VESSELS[vid]['class']}) can transit this corridor within its structural limits.",
            "confidence_note": f"System confidence: {tradeoff[vid]['comparison']['confidence']['overall_confidence']*100:.0f}% ({tradeoff[vid]['comparison']['confidence']['status_label']}).",
            "caveats": [
                "Sea-ice forecast based on persistence — may diverge from actual conditions",
                "GLORYS12 ocean currents not yet assimilated; wind-driven fallback in use",
            ],
        }
    with open(os.path.join(cdir, "explanations.json"), "w") as f:
        json.dump(explanations, f, indent=2)

    # Status
    status = {
        "depart_date": "2019-12-25",
        "confidence": tradeoff["polar_class_pc7"]["comparison"]["confidence"],
        "ocean_source": "ERA5 wind-driven (GLORYS12 deferred)",
        "sources": [
            "OSI SAF SIC CDR (CC-BY-4.0)",
            "ERA5 (Copernicus licence)",
            "NCEP wind fields",
        ],
        "honesty": "This system does not guarantee safe passage. All routes require human review.",
    }
    with open(os.path.join(cdir, "status.json"), "w") as f:
        json.dump(status, f, indent=2)

    # Notices for reroute scenarios
    notices = {
        "rerouteA": {
            "outcome": "ADJUSTED",
            "trigger": "New satellite observation at Day+50 shows ice retreat 12km ahead of forecast",
            "change_text": "Previous course would enter 7/10 concentration ice.\nNew route shifts 15km north through detected open-water lead.\nETA impact: +2.3h.\nFuel impact: +890L (currents less favorable).",
        },
        "rerouteB": {
            "outcome": "RE-ROUTE",
            "trigger": "Iceberg SC-5 injected at Day+50 (synthetic test scenario)",
            "change_text": "ASSUMED scenario: iceberg detected 45km ahead on planned track.\nPrevious course intersects 10nm danger buffer.\nNew route diverts 60km south, then rejoin at Day+70.\nETA impact: +18.4h.\nFuel impact: +12,400L.",
        },
    }
    with open(os.path.join(cdir, "notices.json"), "w") as f:
        json.dump(notices, f, indent=2)

    # Bergs
    bergs = [
        {
            "lon": float(frm["lon"] + (to["lon"] - frm["lon"]) * 0.6 + np.random.uniform(-3, 3)),
            "lat": float(min(frm["lat"], to["lat"]) + np.random.uniform(-2, 1)),
            "label": f"ICE-{cid[:3].upper()}-01",
            "buffer_poly": [[[0, 0]]],  # placeholder
        }
    ]
    with open(os.path.join(cdir, "bergs.json"), "w") as f:
        json.dump(bergs, f, indent=2)

    all_corridors_summary.append({
        "id": cid,
        "name": cdef["name"],
        "from": cdef["from"],
        "to": cdef["to"],
        "distance_km": cdef["distance_km"],
        "bbox": cdef["bbox"],
    })
    print(f"  OK {cdef['name']} ({cdef['distance_km']} km)")

# ── Write corridor index ───────────────────────────────────────
with open(os.path.join(OUTPUT_DIR, "index.json"), "w") as f:
    json.dump(all_corridors_summary, f, indent=2)

# ── Also write to the root data directory for backward compat ──
# Update vessels.json at root
with open("frontend/src/data/vessels.json", "w") as f:
    json.dump(VESSELS, f, indent=2)

print(f"\nGenerated data for {len(CORRIDORS)} corridors")
print(f"Files written to {OUTPUT_DIR}/")
