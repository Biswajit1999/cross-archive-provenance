"""Live adapters for two real, public astronomical archives, no
authentication required for either:

1. NASA Exoplanet Archive TAP (``pscomppars``, the composite planetary
   systems parameters table): confirmed exoplanet host-star names and
   positions.
2. SIMBAD TAP (CDS, Strasbourg): identifier-alias resolution and
   independently maintained positions for the same real host stars.

See docs/DATA_SOURCES.md for full provenance.
"""
from __future__ import annotations

import hashlib
import io
import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

NEA_TAP_SYNC = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
NEA_QUERY = (
    "select distinct top {n} hostname, ra, dec, sy_dist "
    "from pscomppars where hostname is not null order by hostname"
)

SIMBAD_TAP_SYNC = "https://simbad.u-strasbg.fr/simbad/sim-tap/sync"


@dataclass(frozen=True)
class CachePaths:
    cache_dir: Path

    @property
    def manifest(self) -> Path:
        return self.cache_dir / "manifest.json"


def _record_manifest(name: str, url: str, data: bytes, paths: CachePaths) -> None:
    paths.cache_dir.mkdir(parents=True, exist_ok=True)
    entry = {"url": url, "sha256": hashlib.sha256(data).hexdigest(), "n_bytes": len(data),
              "accessed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    manifest = json.loads(paths.manifest.read_text()) if paths.manifest.exists() else {}
    manifest[name] = entry
    paths.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True))


def load_host_stars(paths: CachePaths, n: int = 500, force: bool = False) -> pd.DataFrame:
    """Fetch (or read cached) real confirmed-exoplanet host-star names and
    positions from the NASA Exoplanet Archive."""
    cache_file = paths.cache_dir / f"host_stars_{n}.csv"
    if cache_file.exists() and not force:
        return pd.read_csv(cache_file)

    query = NEA_QUERY.format(n=n)
    url = NEA_TAP_SYNC + "?" + urllib.parse.urlencode({"query": query, "format": "csv"})
    with urllib.request.urlopen(url, timeout=60) as resp:
        raw = resp.read()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(raw)
    _record_manifest(cache_file.name, url, raw, paths)
    return pd.read_csv(io.BytesIO(raw))


def resolve_in_simbad(name: str) -> dict | None:
    """Resolve a real host-star name to a SIMBAD main_id + position via
    the identifier-alias table (``ident`` joined to ``basic``), the
    standard robust SIMBAD name-resolution pattern (a name may be an
    alias, not the ``main_id`` itself)."""
    query = (
        "SELECT b.main_id, b.ra, b.dec FROM ident i JOIN basic b ON i.oidref=b.oid "
        f"WHERE i.id = '{name.replace(chr(39), '')}'"
    )
    params = {"request": "doQuery", "lang": "adql", "query": query, "format": "csv"}
    url = SIMBAD_TAP_SYNC + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
    except Exception:  # noqa: BLE001 - any network/service failure means "could not resolve"
        return None

    lines = [l for l in raw.splitlines() if l.strip()]
    if len(lines) < 2:
        return None
    import csv as _csv
    row = next(_csv.reader([lines[1]]))
    if len(row) < 3:
        return None
    try:
        return {"simbad_main_id": row[0], "simbad_ra": float(row[1]), "simbad_dec": float(row[2])}
    except ValueError:
        return None
