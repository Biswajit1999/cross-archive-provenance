"""Regenerate results/figures/*.png from the committed results/default/
CSVs and JSON -- not from any uncommitted per-object cache. An external
review (Codex) found this repo declared ``matplotlib`` as a dependency
but never imported it anywhere, and had a committed figure with no
script that reproduced it. Run: ``python scripts/make_figures.py``.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from provenance.crossmatch import angular_separation_arcsec

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results" / "default"
FIGURES = ROOT / "results" / "figures"


def plot_resolution_breakdown() -> Path:
    """Resolved / not-found / query-failed counts, built directly from
    the committed ``crossmatch_results.csv`` -- distinguishing "SIMBAD
    queried successfully, no match" from "the query itself failed" is
    the fix at the heart of this project's v0.2.0 (data.py's
    SimbadQueryError docstring)."""
    df = pd.read_csv(RESULTS / "crossmatch_results.csv")
    counts = df["resolution_status"].value_counts()
    order = [s for s in ("resolved", "not_found", "query_failed") if s in counts.index]
    colors = {"resolved": "#4477AA", "not_found": "#CC6677", "query_failed": "#DDCC77"}

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(order, [counts[s] for s in order], color=[colors[s] for s in order])
    for i, s in enumerate(order):
        ax.text(i, counts[s], str(counts[s]), ha="center", va="bottom")
    ax.set_ylabel("host stars")
    ax.set_title(f"SIMBAD resolution outcome (n={len(df)} real host stars)")
    fig.tight_layout()

    out = FIGURES / "resolution_breakdown.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_separation_histogram() -> Path:
    """Angular separation (log-scale) for every resolved object, built
    directly from the committed ``crossmatch_results.csv``."""
    df = pd.read_csv(RESULTS / "crossmatch_results.csv")
    resolved = df[df["resolution_status"] == "resolved"].copy()
    seps = np.array([
        angular_separation_arcsec(r.ra, r.dec, r.simbad_ra, r.simbad_dec)
        for r in resolved.itertuples()
    ])
    seps = np.clip(seps, 1e-3, None)  # avoid log(0) for exact-zero separations

    fig, ax = plt.subplots(figsize=(7, 4))
    bins = np.logspace(np.log10(seps.min()), np.log10(seps.max()), 30)
    ax.hist(seps, bins=bins, color="#4477AA", edgecolor="white")
    ax.set_xscale("log")
    ax.axvline(5.0, color="black", linewidth=0.8, linestyle="--", label="5 arcsec match radius")
    ax.set_xlabel("angular separation, archive vs. SIMBAD position (arcsec, log scale)")
    ax.set_ylabel("resolved objects")
    ax.set_title(f"Positional agreement for {len(resolved)} resolved objects")
    ax.legend(frameon=False)
    fig.tight_layout()

    out = FIGURES / "separation_histogram.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    for path in (plot_resolution_breakdown(), plot_separation_histogram()):
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
