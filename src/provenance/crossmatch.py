"""Positional and identifier provenance-consistency statistics between the
NASA Exoplanet Archive and SIMBAD for the same real host stars."""
from __future__ import annotations

import numpy as np
import pandas as pd


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if trials <= 0 or not 0 <= successes <= trials:
        raise ValueError("require 0 <= successes <= trials and trials > 0")
    p = successes / trials
    denominator = 1 + z**2 / trials
    centre = (p + z**2 / (2 * trials)) / denominator
    half_width = z * ((p * (1 - p) / trials + z**2 / (4 * trials**2)) ** 0.5) / denominator
    return max(0.0, centre - half_width), min(1.0, centre + half_width)


def angular_separation_arcsec(ra1, dec1, ra2, dec2) -> float:
    """Exact great-circle (haversine) angular separation, arcsec -- unlike
    the flat-sky approximation used in some other projects in this
    programme, real archive positions can differ by degrees on rare
    mismatches, where the flat-sky approximation breaks down."""
    ra1, dec1, ra2, dec2 = map(np.radians, (ra1, dec1, ra2, dec2))
    dra = ra2 - ra1
    ddec = dec2 - dec1
    a = np.sin(ddec / 2) ** 2 + np.cos(dec1) * np.cos(dec2) * np.sin(dra / 2) ** 2
    return float(2 * np.arcsin(np.sqrt(np.clip(a, 0, 1))) * 206264.80625)  # rad -> arcsec


def summarize_crossmatch(df: pd.DataFrame, match_radius_arcsec: float = 5.0) -> dict:
    """``df`` must have columns ra, dec, simbad_ra, simbad_dec (NaN where
    SIMBAD resolution failed) and a ``resolution_status`` column with
    values "resolved", "not_found", or "query_failed".

    ``resolution_rate`` and ``unresolved_rate`` are computed over
    successfully-queried names only (excluding ``query_failed``): an
    earlier version used a single boolean ``resolved`` column, which
    conflated "SIMBAD queried successfully and found no match" with "the
    query itself could not be completed" (network error, timeout) --
    silently letting unrelated network conditions during a given run
    change the reported unresolved-name count and, downstream, which
    names got flagged as unresolved (an external review, Codex, caught
    this; see ``data.py::SimbadQueryError``). ``n_query_failed`` is
    reported separately so a reader can see how many names this run
    could not determine an answer for at all.
    """
    if match_radius_arcsec < 0:
        raise ValueError("match_radius_arcsec must be non-negative")
    allowed = {"resolved", "not_found", "query_failed"}
    unexpected = set(df["resolution_status"].dropna()) - allowed
    if unexpected or df["resolution_status"].isna().any():
        raise ValueError(f"unexpected resolution_status values: {sorted(unexpected)}")
    n = len(df)
    n_resolved = int((df["resolution_status"] == "resolved").sum())
    n_not_found = int((df["resolution_status"] == "not_found").sum())
    n_query_failed = int((df["resolution_status"] == "query_failed").sum())
    n_queryable = n_resolved + n_not_found
    resolved = df[df["resolution_status"] == "resolved"]

    seps = [
        angular_separation_arcsec(r.ra, r.dec, r.simbad_ra, r.simbad_dec)
        for r in resolved.itertuples()
    ]
    seps = np.array(seps)
    n_within_radius = int(np.sum(seps <= match_radius_arcsec)) if seps.size else 0

    resolution_ci = wilson_interval(n_resolved, n_queryable) if n_queryable else (float("nan"), float("nan"))
    position_ci = wilson_interval(n_within_radius, n_resolved) if n_resolved else (float("nan"), float("nan"))
    return {
        "n_queried": n,
        "n_query_failed": n_query_failed,
        "n_resolved_in_simbad": n_resolved,
        "n_not_found_in_simbad": n_not_found,
        "resolution_rate": n_resolved / n_queryable if n_queryable else float("nan"),
        "resolution_rate_ci95_low": resolution_ci[0],
        "resolution_rate_ci95_high": resolution_ci[1],
        "n_within_match_radius": n_within_radius,
        "fraction_within_match_radius_of_resolved": (
            n_within_radius / n_resolved if n_resolved else float("nan")
        ),
        "fraction_within_match_radius_ci95_low": position_ci[0],
        "fraction_within_match_radius_ci95_high": position_ci[1],
        "median_separation_arcsec": float(np.median(seps)) if seps.size else float("nan"),
        "max_separation_arcsec": float(np.max(seps)) if seps.size else float("nan"),
    }
