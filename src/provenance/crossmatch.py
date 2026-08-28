"""Positional and identifier provenance-consistency statistics between the
NASA Exoplanet Archive and SIMBAD for the same real host stars."""
from __future__ import annotations

import numpy as np
import pandas as pd


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
    SIMBAD resolution failed) and a boolean ``resolved`` column."""
    n = len(df)
    n_resolved = int(df["resolved"].sum())
    resolved = df[df["resolved"]]

    seps = [
        angular_separation_arcsec(r.ra, r.dec, r.simbad_ra, r.simbad_dec)
        for r in resolved.itertuples()
    ]
    seps = np.array(seps)
    n_within_radius = int(np.sum(seps <= match_radius_arcsec)) if seps.size else 0

    return {
        "n_queried": n,
        "n_resolved_in_simbad": n_resolved,
        "resolution_rate": n_resolved / n if n else float("nan"),
        "n_within_match_radius": n_within_radius,
        "fraction_within_match_radius_of_resolved": (
            n_within_radius / n_resolved if n_resolved else float("nan")
        ),
        "median_separation_arcsec": float(np.median(seps)) if seps.size else float("nan"),
        "max_separation_arcsec": float(np.max(seps)) if seps.size else float("nan"),
    }
