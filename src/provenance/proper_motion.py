"""Gaia DR3 proper-motion checks for flagged cross-archive positions."""

from __future__ import annotations

import numpy as np
import pandas as pd


def tangent_offset_arcsec(ra0, dec0, ra1, dec1) -> tuple[float, float]:
    """Small-angle east/north offset from position 0 to 1 in arcseconds."""
    mean_dec = np.radians((float(dec0) + float(dec1)) / 2)
    east = (float(ra1) - float(ra0)) * np.cos(mean_dec) * 3600
    north = (float(dec1) - float(dec0)) * 3600
    return float(east), float(north)


def motion_diagnostics(row: pd.Series, epoch_span_years: float = 16.0) -> dict:
    """Compare a SIMBAD-to-NEA offset with a Gaia DR3 proper-motion vector."""
    east, north = tangent_offset_arcsec(row.simbad_ra, row.simbad_dec, row.nea_ra, row.nea_dec)
    original = float(np.hypot(east, north))
    plausible = (
        row.candidate_separation_arcsec <= 1 and np.isfinite(row.pmra) and np.isfinite(row.pmdec)
    )
    if not plausible:
        return {
            "hostname": row.hostname,
            "source_id": int(row.source_id),
            "status": "no_plausible_gaia_motion",
            "original_separation_arcsec": original,
            "gaia_total_pm_mas_per_year": np.nan,
            "implied_epoch_span_years": np.nan,
            "fixed_16yr_residual_arcsec": np.nan,
            "cross_track_residual_arcsec": np.nan,
            "offset_explained_fraction": np.nan,
            "gaia_only_propagation_sigma_arcsec": np.nan,
            "candidate_separation_arcsec": float(row.candidate_separation_arcsec),
            "candidate_margin_arcsec": float(row.candidate_margin_arcsec),
        }
    motion = np.array([row.pmra, row.pmdec], dtype=float) / 1000
    offset = np.array([east, north])
    speed2 = float(motion @ motion)
    implied_span = float(offset @ motion / speed2) if speed2 else np.nan
    fixed_residual = offset - epoch_span_years * motion
    cross_track = offset - implied_span * motion
    residual = float(np.linalg.norm(fixed_residual))

    dt = epoch_span_years
    var_east = (
        row.ra_error**2
        + (dt * row.pmra_error) ** 2
        + 2 * dt * (row.ra_pmra_corr * row.ra_error * row.pmra_error)
    )
    var_north = (
        row.dec_error**2
        + (dt * row.pmdec_error) ** 2
        + 2 * dt * (row.dec_pmdec_corr * row.dec_error * row.pmdec_error)
    )
    gaia_sigma = float(np.sqrt(max(0.0, var_east + var_north)) / 1000)
    return {
        "hostname": row.hostname,
        "source_id": int(row.source_id),
        "status": "validated",
        "original_separation_arcsec": original,
        "gaia_total_pm_mas_per_year": float(np.sqrt(speed2) * 1000),
        "implied_epoch_span_years": implied_span,
        "fixed_16yr_residual_arcsec": residual,
        "cross_track_residual_arcsec": float(np.linalg.norm(cross_track)),
        "offset_explained_fraction": 1 - residual / original if original else np.nan,
        "gaia_only_propagation_sigma_arcsec": gaia_sigma,
        "candidate_separation_arcsec": float(row.candidate_separation_arcsec),
        "candidate_margin_arcsec": float(row.candidate_margin_arcsec),
    }


def analyze_discrepancies(discrepancies: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    """Join the nearest Gaia candidate to every flagged real archive object."""
    selected = candidates[candidates["candidate_rank"] == 1].copy()
    second = candidates[candidates["candidate_rank"] == 2][
        ["hostname", "candidate_separation_arcsec"]
    ].rename(columns={"candidate_separation_arcsec": "second_separation_arcsec"})
    selected = selected.merge(second, on="hostname", how="left")
    selected["candidate_margin_arcsec"] = (
        selected["second_separation_arcsec"] - selected["candidate_separation_arcsec"]
    )
    discrepancies = discrepancies.rename(columns={"ra": "nea_ra", "dec": "nea_dec"})
    selected = selected.rename(columns={"ra": "gaia_ra", "dec": "gaia_dec"})
    joined = discrepancies.merge(selected, on="hostname", validate="one_to_one")
    return pd.DataFrame([motion_diagnostics(row) for _, row in joined.iterrows()])
