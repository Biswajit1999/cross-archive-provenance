"""Fetch Gaia DR3 candidates around committed NEA discrepancy positions."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path
import time
import urllib.parse
import urllib.request
from urllib.error import HTTPError

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://gea.esac.esa.int/tap-server/tap/sync"
INPUT = ROOT / "results/default/position_discrepancies.csv"
OUTPUT = ROOT / "data/gaia_dr3_discrepancy_candidates.csv"
MANIFEST = ROOT / "data/gaia_dr3_discrepancy_manifest.json"
COLUMNS = (
    "source_id,ra,dec,pmra,pmdec,ref_epoch,ra_error,dec_error,pmra_error,"
    "pmdec_error,ra_pmra_corr,dec_pmdec_corr,phot_g_mean_mag"
)


def query_for(ra: float, dec: float) -> str:
    return (
        f"SELECT TOP 5 {COLUMNS},"
        "DISTANCE(POINT('ICRS',ra,dec),"
        f"POINT('ICRS',{ra:.10f},{dec:.10f})) AS target_distance_deg "
        "FROM gaiadr3.gaia_source "
        "WHERE 1=CONTAINS(POINT('ICRS',ra,dec),"
        f"CIRCLE('ICRS',{ra:.10f},{dec:.10f},0.0083333333)) "
        "ORDER BY target_distance_deg"
    )


def main() -> None:
    targets = pd.read_csv(INPUT)
    records, queries = [], []
    for target in targets.itertuples():
        query = query_for(target.ra, target.dec)
        url = (
            ENDPOINT
            + "?"
            + urllib.parse.urlencode(
                {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": query}
            )
        )
        try:
            with urllib.request.urlopen(url, timeout=90) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Gaia query failed for {target.hostname}: {detail}") from error
        rows = list(csv.DictReader(io.StringIO(raw)))
        for rank, row in enumerate(rows, start=1):
            dra = (float(row["ra"]) - target.ra) * math.cos(math.radians(target.dec)) * 3600
            ddec = (float(row["dec"]) - target.dec) * 3600
            row.update(
                hostname=target.hostname,
                candidate_rank=rank,
                candidate_separation_arcsec=math.hypot(dra, ddec),
            )
            records.append(row)
        queries.append({"hostname": target.hostname, "query": query, "rows": len(rows)})
        time.sleep(0.15)

    frame = pd.DataFrame(records)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUTPUT, index=False)
    MANIFEST.write_text(
        json.dumps(
            {
                "archive": "ESA Gaia Archive",
                "release_table": "gaiadr3.gaia_source",
                "endpoint": ENDPOINT,
                "accessed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "input": str(INPUT.relative_to(ROOT)).replace("\\", "/"),
                "output_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
                "cone_radius_arcsec": 30,
                "queries": queries,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
