"""Command-line workflow for the cross-archive provenance audit."""
from __future__ import annotations

import json
import time
from pathlib import Path

import click
import pandas as pd

from .crossmatch import angular_separation_arcsec, summarize_crossmatch
from .data import CachePaths, SimbadQueryError, load_host_stars, resolve_in_simbad


@click.group()
def main() -> None:
    """provenance: cross-archive identifier/position consistency audit."""


def _resolve_with_retries(name: str, retries: int = 2, backoff_seconds: float = 1.0):
    """Retry a SIMBAD query on transient failure before giving up.
    Returns (result, status) where status is one of "resolved",
    "not_found" (query completed, genuinely no match), or "query_failed"
    (every attempt failed to complete -- kept distinct from "not_found",
    see SimbadQueryError)."""
    for attempt in range(retries + 1):
        try:
            result = resolve_in_simbad(name)
        except SimbadQueryError:
            if attempt < retries:
                time.sleep(backoff_seconds)
            continue
        return result, ("resolved" if result is not None else "not_found")
    return None, "query_failed"


@main.command("run")
@click.option("--cache-dir", default="data/cache", show_default=True)
@click.option("--out", "out_dir", default="results", show_default=True)
@click.option("--n", default=300, show_default=True, help="Number of real host stars to audit.")
@click.option("--match-radius-arcsec", default=5.0, show_default=True)
def run_cmd(cache_dir: str, out_dir: str, n: int, match_radius_arcsec: float) -> None:
    paths = CachePaths(cache_dir=Path(cache_dir))
    hosts = load_host_stars(paths, n=n)
    click.echo(f"Loaded {len(hosts)} real confirmed-exoplanet host stars from the NASA Exoplanet Archive.")

    rows = []
    for row in hosts.itertuples():
        simbad, status = _resolve_with_retries(row.hostname)
        time.sleep(0.05)  # be polite to the free public SIMBAD TAP service
        if simbad:
            rows.append({
                "hostname": row.hostname, "ra": row.ra, "dec": row.dec,
                "resolved": True, "resolution_status": status, **simbad,
            })
        else:
            rows.append({
                "hostname": row.hostname, "ra": row.ra, "dec": row.dec,
                "resolved": False, "resolution_status": status,
                "simbad_main_id": None, "simbad_ra": None, "simbad_dec": None,
            })

    df = pd.DataFrame(rows)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "crossmatch_results.csv", index=False)

    n_query_failed = int((df["resolution_status"] == "query_failed").sum())
    if n_query_failed:
        df[df["resolution_status"] == "query_failed"].to_csv(out / "query_failures.csv", index=False)
        click.echo(f"Wrote {out/'query_failures.csv'} ({n_query_failed} names SIMBAD could not be "
                   f"queried for after retries -- excluded from resolved/unresolved, not counted "
                   f"as either)")

    summary = summarize_crossmatch(df, match_radius_arcsec=match_radius_arcsec)
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    click.echo(json.dumps(summary, indent=2))

    # "genuinely not found" only -- excludes query_failed rows, which are
    # not evidence of anything about SIMBAD's contents (see data.py's
    # SimbadQueryError docstring for why this distinction matters).
    unresolved = df[df["resolution_status"] == "not_found"]
    unresolved.to_csv(out / "unresolved_hosts.csv", index=False)
    click.echo(f"Wrote {out/'unresolved_hosts.csv'} ({len(unresolved)} host names SIMBAD queried "
               f"successfully but did not resolve)")

    large_offset = df[df["resolved"]].copy()
    if len(large_offset):
        large_offset["separation_arcsec"] = [
            angular_separation_arcsec(r.ra, r.dec, r.simbad_ra, r.simbad_dec)
            for r in large_offset.itertuples()
        ]
        flagged = large_offset[large_offset["separation_arcsec"] > match_radius_arcsec]
        flagged.to_csv(out / "position_discrepancies.csv", index=False)
        click.echo(f"Wrote {out/'position_discrepancies.csv'} ({len(flagged)} objects with "
                   f">{match_radius_arcsec} arcsec disagreement)")


if __name__ == "__main__":
    main()
