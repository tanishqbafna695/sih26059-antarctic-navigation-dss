"""Physics-guided and ML iceberg trajectory prediction models (FR-8, FR-9, FR-10, FR-11).

Combines kinematic history (last observed velocity), atmospheric wind forcing
(ERA5 10m wind with Southern Hemisphere leeway deflection), surface ocean current
or sea-ice drift forcing (GLORYS12 / OSI SAF), and momentum decay to predict
future iceberg positions at 24h, 48h, and 72h horizons.

Outputs predicted coordinates along with probabilistic uncertainty bounds
(1-sigma radius, ellipse axes, orientation, and confidence score) that widen
with forecast horizon and observation staleness (FR-11).
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from backend.baselines.metrics import position_error_km

EARTH_R_KM = 6371.0


def _dx_km_per_deg_lon(lat_deg: float) -> float:
    """km per degree of longitude at a given latitude (spherical approx)."""
    return (np.pi / 180.0) * EARTH_R_KM * np.cos(np.deg2rad(lat_deg))


def _estimate_kinematic_velocity(track: pd.DataFrame) -> Tuple[float, float, float, float, pd.Timestamp]:
    """Estimate kinematic velocity (km/h east & north) and last fix from a track DataFrame."""
    if len(track) < 2:
        last = track.iloc[-1]
        return 0.0, 0.0, float(last["lon"]), float(last["lat"]), pd.Timestamp(last["time"])

    p0, p1 = track.iloc[-2], track.iloc[-1]
    t0 = pd.Timestamp(p0["time"])
    t1 = pd.Timestamp(p1["time"])
    dt_h = (t1 - t0).total_seconds() / 3600.0

    lat1 = float(p1["lat"])
    lon1 = float(p1["lon"])

    if dt_h <= 0:
        return 0.0, 0.0, lon1, lat1, t1

    km_deg_lon = _dx_km_per_deg_lon(0.5 * (float(p0["lat"]) + lat1))
    de_km = (lon1 - float(p0["lon"])) * km_deg_lon
    dn_km = (lat1 - float(p0["lat"])) * (np.pi / 180.0) * EARTH_R_KM

    v_east_kmh = de_km / dt_h
    v_north_kmh = dn_km / dt_h
    return v_east_kmh, v_north_kmh, lon1, lat1, t1


def _rotate_wind_vector(u_wind: float, v_wind: float, deflection_deg: float = -20.0) -> Tuple[float, float]:
    """Rotate wind vector by leeway deflection angle (default -20 deg leftward for Southern Hemisphere)."""
    rad = np.deg2rad(deflection_deg)
    cos_a, sin_a = np.cos(rad), np.sin(rad)
    u_rot = cos_a * u_wind - sin_a * v_wind
    v_rot = sin_a * u_wind + cos_a * v_wind
    return float(u_rot), float(v_rot)


class IcebergPhysicsDriftModel:
    """Physics-guided empirical iceberg drift model.

    Drift velocity equation:
        v_berg(h) = w_kin(h) * v_kin + w_ocean * v_ocean + C_w * R(theta_wind) * v_wind

    where:
        - v_kin is the initial kinematic velocity (decaying exponentially over tau_kin = 24h)
        - v_ocean is ocean current / drift velocity in km/h
        - v_wind is 10m wind velocity in km/h
        - C_w is wind leeway drag coefficient (~0.025)
        - theta_wind is Coriolis leeway angle (~-20 deg leftward in Southern Hemisphere)
    """

    def __init__(self,
                 wind_drag_coeff: float = 0.025,
                 wind_deflection_deg: float = -20.0,
                 ocean_drag_weight: float = 0.85,
                 momentum_decay_h: float = 24.0):
        self.wind_drag_coeff = wind_drag_coeff
        self.wind_deflection_deg = wind_deflection_deg
        self.ocean_drag_weight = ocean_drag_weight
        self.momentum_decay_h = momentum_decay_h

    def predict_drift_velocity(self,
                               v_kin_east: float,
                               v_kin_north: float,
                               horizon_h: float,
                               u_wind_m_s: float = 0.0,
                               v_wind_m_s: float = 0.0,
                               u_ocean_m_s: float = 0.0,
                               v_ocean_m_s: float = 0.0,
                               has_forcing: bool = True) -> Tuple[float, float]:
        """Compute predicted iceberg drift velocity (km/h east & north) at horizon h."""
        if not has_forcing:
            return v_kin_east, v_kin_north

        # Convert m/s forcing velocities to km/h (1 m/s = 3.6 km/h)
        u_wind_kmh = u_wind_m_s * 3.6
        v_wind_kmh = v_wind_m_s * 3.6
        u_ocean_kmh = u_ocean_m_s * 3.6
        v_ocean_kmh = v_ocean_m_s * 3.6

        # Momentum weight decays exponentially with horizon
        w_kin = math.exp(-horizon_h / self.momentum_decay_h)

        # Wind leeway with Southern Hemisphere deflection
        u_wind_rot, v_wind_rot = _rotate_wind_vector(u_wind_kmh, v_wind_kmh, self.wind_deflection_deg)
        u_leeway = self.wind_drag_coeff * u_wind_rot
        v_leeway = self.wind_drag_coeff * v_wind_rot

        # Ocean velocity contribution
        u_ocean_contrib = self.ocean_drag_weight * u_ocean_kmh
        v_ocean_contrib = self.ocean_drag_weight * v_ocean_kmh

        # Total forcing equilibrium velocity
        u_forcing = u_ocean_contrib + u_leeway
        v_forcing = v_ocean_contrib + v_leeway

        # Smooth transition from initial kinematic velocity to forcing equilibrium
        v_east = w_kin * v_kin_east + (1.0 - w_kin) * u_forcing
        v_north = w_kin * v_kin_north + (1.0 - w_kin) * v_forcing

        return v_east, v_north

    def predict_position(self,
                         lon0: float,
                         lat0: float,
                         v_kin_east: float,
                         v_kin_north: float,
                         horizon_h: float,
                         u_wind_m_s: float = 0.0,
                         v_wind_m_s: float = 0.0,
                         u_ocean_m_s: float = 0.0,
                         v_ocean_m_s: float = 0.0,
                         obs_staleness_h: float = 0.0,
                         has_forcing: bool = True) -> Dict[str, Any]:
        """Predict iceberg position and uncertainty ellipse at horizon h.

        Returns dict with keys:
            - lon, lat: predicted coordinates
            - horizon_h: forecast horizon in hours
            - v_east_kmh, v_north_kmh: mean predicted drift velocity
            - uncertainty_km: 1-sigma overall position uncertainty radius (km)
            - semi_major_km, semi_minor_km: 1-sigma uncertainty ellipse axes (km)
            - orientation_deg: uncertainty ellipse orientation angle (degrees)
            - confidence: confidence score in [0.0, 1.0]
        """
        v_east, v_north = self.predict_drift_velocity(
            v_kin_east, v_kin_north, horizon_h,
            u_wind_m_s, v_wind_m_s, u_ocean_m_s, v_ocean_m_s,
            has_forcing=has_forcing
        )

        dlat_km = v_north * horizon_h
        dlat_deg = dlat_km / ((np.pi / 180.0) * EARTH_R_KM)
        lat1 = lat0 + dlat_deg

        km_deg_lon = _dx_km_per_deg_lon(0.5 * (lat0 + lat1))
        dlon_km = v_east * horizon_h
        lon1 = lon0 + (dlon_km / km_deg_lon if km_deg_lon > 0 else 0.0)

        # Calculate uncertainty ellipse parameters (FR-8, FR-11)
        sigma_base = 0.5  # km base fix error
        sigma_rate = 0.12  # km/h growth rate with horizon
        sigma_stale = 0.15  # km/h growth rate with staleness

        unc_km = math.sqrt(sigma_base ** 2 + (sigma_rate * horizon_h) ** 2 + (sigma_stale * obs_staleness_h) ** 2)

        # Ellipse anisotropy aligned with drift heading
        heading_rad = math.atan2(v_north, v_east) if (abs(v_east) > 1e-4 or abs(v_north) > 1e-4) else 0.0
        heading_deg = math.degrees(heading_rad) % 360.0

        semi_major_km = 1.25 * unc_km
        semi_minor_km = 0.80 * unc_km

        # Confidence degrades with horizon and staleness (FR-13)
        confidence = max(0.1, min(1.0, 1.0 - 0.006 * horizon_h - 0.012 * obs_staleness_h))

        return {
            "lon": float(lon1),
            "lat": float(lat1),
            "horizon_h": float(horizon_h),
            "v_east_kmh": float(v_east),
            "v_north_kmh": float(v_north),
            "uncertainty_km": float(unc_km),
            "semi_major_km": float(semi_major_km),
            "semi_minor_km": float(semi_minor_km),
            "orientation_deg": float(heading_deg),
            "confidence": float(confidence),
        }

    def predict_track(self,
                      track: pd.DataFrame,
                      horizons_h: Tuple[float, ...] = (24.0, 48.0, 72.0),
                      forcing_data: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        """Predict trajectory for a single iceberg track given past observations."""
        v_kin_east, v_kin_north, lon0, lat0, last_t = _estimate_kinematic_velocity(track)

        forcing = forcing_data or {}
        u_wind = forcing.get("u10", 0.0)
        v_wind = forcing.get("v10", 0.0)
        u_ocean = forcing.get("uo", 0.0)
        v_ocean = forcing.get("vo", 0.0)

        preds = []
        for h in horizons_h:
            pred = self.predict_position(
                lon0, lat0, v_kin_east, v_kin_north, h,
                u_wind_m_s=u_wind, v_wind_m_s=v_wind,
                u_ocean_m_s=u_ocean, v_ocean_m_s=v_ocean
            )
            pred["base_time"] = last_t.isoformat()
            pred["target_time"] = (last_t + pd.Timedelta(hours=h)).isoformat()
            preds.append(pred)
        return preds


class IcebergMLDriftModel:
    """Machine-learning / data-driven iceberg drift model.

    Fits empirical weights (or Ridge regression) to predict velocity adjustment
    delta_v = (delta_v_east, delta_v_north) from kinematic velocity, wind, and
    ocean current inputs across historical track intervals.
    """

    def __init__(self, ridge_alpha: float = 1.0):
        self.ridge_alpha = ridge_alpha
        self.weights_east: Optional[np.ndarray] = None
        self.weights_north: Optional[np.ndarray] = None
        self.is_fitted = False
        self.physics_fallback = IcebergPhysicsDriftModel()

    def fit(self,
            tracks: pd.DataFrame,
            forcing_provider: Optional[Any] = None) -> IcebergMLDriftModel:
        """Fit empirical weights on historical iceberg track segments."""
        X_list, y_east_list, y_north_list = [], [], []

        for _, berg in tracks.groupby("berg_id", sort=False):
            berg = berg.sort_values("time").reset_index(drop=True)
            if len(berg) < 3:
                continue

            times = pd.to_datetime(berg["time"])
            for i in range(1, len(berg) - 1):
                track_sub = berg.iloc[: i + 1]
                v_kin_east, v_kin_north, lon0, lat0, _ = _estimate_kinematic_velocity(track_sub)

                t_curr = times.iloc[i]
                t_next = times.iloc[i + 1]
                dt_h = (t_next - t_curr).total_seconds() / 3600.0
                if dt_h <= 0 or dt_h > 96.0:
                    continue

                km_deg_lon = _dx_km_per_deg_lon(0.5 * (lat0 + float(berg.iloc[i + 1]["lat"])))
                obs_v_east = (float(berg.iloc[i + 1]["lon"]) - lon0) * km_deg_lon / dt_h
                obs_v_north = (float(berg.iloc[i + 1]["lat"]) - lat0) * (np.pi / 180.0) * EARTH_R_KM / dt_h

                u_wind, v_wind, u_ocean, v_ocean = 0.0, 0.0, 0.0, 0.0
                if forcing_provider is not None:
                    f = forcing_provider(lon0, lat0, t_curr)
                    u_wind = f.get("u10", 0.0)
                    v_wind = f.get("v10", 0.0)
                    u_ocean = f.get("uo", 0.0)
                    v_ocean = f.get("vo", 0.0)

                u_wind_rot, v_wind_rot = _rotate_wind_vector(u_wind * 3.6, v_wind * 3.6, -20.0)

                feat = [v_kin_east, v_kin_north, u_wind_rot, v_wind_rot, u_ocean * 3.6, v_ocean * 3.6]
                X_list.append(feat)
                y_east_list.append(obs_v_east)
                y_north_list.append(obs_v_north)

        if len(X_list) >= 3:
            X = np.array(X_list)
            y_e = np.array(y_east_list)
            y_n = np.array(y_north_list)

            n_features = X.shape[1]
            eye = self.ridge_alpha * np.eye(n_features)
            self.weights_east = np.linalg.solve(X.T @ X + eye, X.T @ y_e)
            self.weights_north = np.linalg.solve(X.T @ X + eye, X.T @ y_n)
            self.is_fitted = True

        return self

    def predict_position(self,
                         lon0: float,
                         lat0: float,
                         v_kin_east: float,
                         v_kin_north: float,
                         horizon_h: float,
                         u_wind_m_s: float = 0.0,
                         v_wind_m_s: float = 0.0,
                         u_ocean_m_s: float = 0.0,
                         v_ocean_m_s: float = 0.0,
                         obs_staleness_h: float = 0.0) -> Dict[str, Any]:
        """Predict iceberg position using fitted ML weights or physics fallback."""
        if not self.is_fitted or self.weights_east is None or self.weights_north is None:
            return self.physics_fallback.predict_position(
                lon0, lat0, v_kin_east, v_kin_north, horizon_h,
                u_wind_m_s, v_wind_m_s, u_ocean_m_s, v_ocean_m_s, obs_staleness_h
            )

        u_wind_rot, v_wind_rot = _rotate_wind_vector(u_wind_m_s * 3.6, v_wind_m_s * 3.6, -20.0)
        feat = np.array([v_kin_east, v_kin_north, u_wind_rot, v_wind_rot, u_ocean_m_s * 3.6, v_ocean_m_s * 3.6])

        v_east = float(feat @ self.weights_east)
        v_north = float(feat @ self.weights_north)

        dlat_km = v_north * horizon_h
        dlat_deg = dlat_km / ((np.pi / 180.0) * EARTH_R_KM)
        lat1 = lat0 + dlat_deg

        km_deg_lon = _dx_km_per_deg_lon(0.5 * (lat0 + lat1))
        dlon_km = v_east * horizon_h
        lon1 = lon0 + (dlon_km / km_deg_lon if km_deg_lon > 0 else 0.0)

        unc_km = math.sqrt(0.5 ** 2 + (0.11 * horizon_h) ** 2 + (0.15 * obs_staleness_h) ** 2)
        heading_rad = math.atan2(v_north, v_east) if (abs(v_east) > 1e-4 or abs(v_north) > 1e-4) else 0.0
        confidence = max(0.1, min(1.0, 1.0 - 0.005 * horizon_h - 0.012 * obs_staleness_h))

        return {
            "lon": float(lon1),
            "lat": float(lat1),
            "horizon_h": float(horizon_h),
            "v_east_kmh": float(v_east),
            "v_north_kmh": float(v_north),
            "uncertainty_km": float(unc_km),
            "semi_major_km": float(1.2 * unc_km),
            "semi_minor_km": float(0.85 * unc_km),
            "orientation_deg": float(math.degrees(heading_rad) % 360.0),
            "confidence": float(confidence),
        }
