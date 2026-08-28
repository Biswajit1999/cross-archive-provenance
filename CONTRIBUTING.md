# Contributing

## Development setup

```bash
git clone https://github.com/Biswajit1999/cross-archive-provenance.git
cd cross-archive-provenance
python -m pip install -e ".[dev]"
pytest -q
```

## Before opening a pull request

- Run `pytest -q` and `ruff check src tests`; both must pass.
- Live-network tests hit real public services (NASA Exoplanet Archive,
  SIMBAD) -- be considerate of query volume; the CLI already rate-limits
  itself (`time.sleep` between SIMBAD queries).

## Good first issues

See the repository Issues tab, including adding a third archive (e.g.
Gaia DR3 via VizieR, following the pattern already used in
`hwo-target-evidence-atlas` and `gaia-exoplanet-astrometry-readiness` in
this programme) for a three-way consistency check.
