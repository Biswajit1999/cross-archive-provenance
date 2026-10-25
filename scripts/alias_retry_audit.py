"""Offline alias inventory, optional live SIMBAD retry with explicit rate limit.

PYTHONPATH=src python scripts/alias_retry_audit.py --out /tmp/aliases.json
Add --live only when permitted. This never overwrites published results.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from provenance.alias_audit import alias_variants, audit_aliases
from provenance.data import resolve_in_simbad


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("results/default/unresolved_hosts.csv"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--min-interval", type=float, default=1.0)
    args = parser.parse_args()
    if args.min_interval < 0:
        parser.error("--min-interval must be nonnegative")
    raw = args.input.read_bytes()
    df = pd.read_csv(args.input)
    required = {"hostname", "ra", "dec", "resolution_status"}
    if not required.issubset(df.columns):
        parser.error("input missing required columns")
    if not set(df.resolution_status).issubset({"not_found"}):
        parser.error("input must contain only previously completed not_found queries")
    rows = []
    last_query = [0.0]

    def throttled_resolver(alias):
        wait = args.min_interval - (time.monotonic() - last_query[0])
        if wait > 0:
            time.sleep(wait)
        try:
            return resolve_in_simbad(alias)
        finally:
            last_query[0] = time.monotonic()

    for row in df.itertuples():
        if args.live:
            record = asdict(
                audit_aliases(row.hostname, float(row.ra), float(row.dec), throttled_resolver)
            )
        else:
            record = {
                "original_name": row.hostname, "status": "not_queried",
                "candidates": alias_variants(row.hostname), "attempted": [],
            }
        rows.append(record)
    result = {
        "source_sha256": hashlib.sha256(raw).hexdigest(), "source_rows": len(df),
        "live": args.live, "position_gate_arcsec": 5.0, "results": rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_rows": len(df), "live": args.live,
        "candidate_names": sum(len(row["candidates"]) for row in rows),
    }, indent=2))


if __name__ == "__main__":
    main()
