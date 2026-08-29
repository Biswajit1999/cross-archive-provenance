# Reproducibility

```bash
git clone https://github.com/Biswajit1999/cross-archive-provenance.git
cd cross-archive-provenance
python -m pip install -e ".[dev]"

pytest -q
provenance run --out results/default --n 300 --match-radius-arcsec 5.0
```

Regenerates `results/default/crossmatch_results.csv`, `summary.json`,
`unresolved_hosts.csv`, `position_discrepancies.csv`, and (only if any
name's SIMBAD query still failed after retries) `query_failures.csv`;
every number in `README.md`, `CHANGELOG.md`, and `paper/manuscript.md`
traces to these files. The full 300-object run takes a few minutes
(rate-limited SIMBAD queries, plus up to 2 retries per name on a
transient failure).

## Determinism

`load_host_stars` and `resolve_in_simbad` query live services and are not
seeded; results reflect the archives' current live content and may change
slightly (e.g. as SIMBAD adds new entries) between runs. A name whose
SIMBAD query fails to complete (network error, timeout, malformed
response) is retried up to twice (`cli.py::_resolve_with_retries`) before
being recorded as `query_failed`, distinct from a genuine "not found" --
see `docs/LIMITATIONS.md` for why that distinction matters and
`docs/CLAIMS.md` for the bug this fixed. Fetched data is checksummed and
timestamped in `data/cache/manifest.json` (git-ignored).
