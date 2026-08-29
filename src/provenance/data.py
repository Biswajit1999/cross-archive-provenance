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


class SimbadQueryError(Exception):
    """Raised when a SIMBAD query could not be completed (network error,
    timeout, or a malformed/error response) -- distinct from a query that
    completed and genuinely found no match. An earlier version of
    ``resolve_in_simbad`` caught every exception and returned ``None`` for
    all of them, silently conflating "this object has no SIMBAD entry"
    (a real astrophysical result) with "the query itself failed" (an
    external review, Codex, flagged this as a correctness bug, since it
    can inflate or deflate the unresolved-name count depending on
    unrelated network conditions during a given run). Callers that want
    to retry transient failures should catch this specifically -- see
    ``cli.py::_resolve_with_retries``."""


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
    alias, not the ``main_id`` itself).

    Returns a match dict, or ``None`` if the query completed and SIMBAD
    genuinely returned no match. Raises ``SimbadQueryError`` if the query
    could not be completed at all (network error, timeout, or a
    malformed/error response) -- see that class's docstring for why this
    distinction matters."""
    query = (
        "SELECT b.main_id, b.ra, b.dec FROM ident i JOIN basic b ON i.oidref=b.oid "
        f"WHERE i.id = '{name.replace(chr(39), '')}'"
    )
    params = {"request": "doQuery", "lang": "adql", "query": query, "format": "csv"}
    url = SIMBAD_TAP_SYNC + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:
            raw = resp.read().decode("utf-8")
    except Exception as exc:
        raise SimbadQueryError(f"SIMBAD query failed for {name!r}: {exc}") from exc

    lines = [line for line in raw.splitlines() if line.strip()]
    if len(lines) < 2:
        return None  # query completed successfully; zero data rows means genuinely not found
    import csv as _csv
    row = next(_csv.reader([lines[1]]))
    if len(row) < 3:
        raise SimbadQueryError(f"Malformed SIMBAD response for {name!r}: {row!r}")
    try:
        return {"simbad_main_id": row[0], "simbad_ra": float(row[1]), "simbad_dec": float(row[2])}
    except ValueError as exc:
        raise SimbadQueryError(f"Malformed SIMBAD response for {name!r}: {row!r}") from exc
