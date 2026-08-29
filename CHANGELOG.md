# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/).

## [0.2.0] - 2026-08-29

Fixes for issues raised by an external review (Codex); no repository
rename or package-name change in this release (kept as a separate,
later decision).

### Fixed

- **Silent network-failure-as-unresolved bug**: `resolve_in_simbad`
  caught every exception (network error, timeout, malformed response)
  and returned `None` for all of them, indistinguishable from "SIMBAD
  queried successfully and genuinely has no entry for this name." A
  transient failure could silently miscount a name as unresolved. Fixed:
  a failed query now raises `SimbadQueryError`; `cli.py` retries such
  failures up to twice before recording them separately as
  `query_failed` in `results/default/query_failures.csv` (when
  non-empty), excluded from both the resolved and not-found counts.
- **Overstated "nearly all KMTNet" claim**: only 44% (11/25) of unresolved
  names in the committed default run are specifically KMTNet
  designations, not "nearly all" -- the claim was not checked against
  the full breakdown of the CSV it cited before publishing. Corrected to
  the real breakdown: 84% (21/25) are *any* microlensing-survey
  designation (KMTNet, OGLE, or MOA); the remaining 4 names are called
  out separately as unexplained by that pattern.
- **Manuscript/CSV contradiction on the top-4 position discrepancies**:
  `paper/manuscript.md` and `docs/LIMITATIONS.md` both listed GJ 1061,
  GJ 3021, GJ 328, and GJ 674 as the four largest discrepancies, which
  did not match `results/default/position_discrepancies.csv` when sorted
  by separation (the real top 4 are HD 285968, GJ 876, GJ 674, GJ 328).
  Both fixed to match the sorted CSV.
- Ambiguous variable name `l` in `data.py` (ruff `E741`, not selected by
  default but a real code-smell) renamed to `line`.
- Unused `matplotlib` dependency with a stale, non-reproducible committed
  figure: added `scripts/make_figures.py`, regenerating
  `results/figures/*.png` from committed `results/default/` data.

### Results

Regenerated live against the real 293-host-star sample
(`results/default/summary.json`; this run had 0 query failures, so the
headline resolution-rate number is numerically unchanged from v0.1.0 --
the code bug above was real regardless, and the two documentation errors
above were independent of it):

- 91.5% resolve in SIMBAD by exact name (268/293); of those, 95.1% agree
  in position within 5 arcsec (median 0.28 arcsec, max 20.1 arcsec).
- Of 25 unresolved names: 84% (21/25) are microlensing-survey lens
  designations (11 KMTNet, 9 OGLE, 1 MOA); 4 are not (`Lupus-TR-3`,
  `Qatar-5`, `Qatar-8`, `TIC 320419023`).
- Four largest position discrepancies: HD 285968 (20.1"), GJ 876
  (18.1"), GJ 674 (16.3"), GJ 328 (16.2") -- all nearby M dwarfs.

## [0.1.0] - 2026-08-28

### Added

- Live adapters for the NASA Exoplanet Archive (`pscomppars`) and SIMBAD
  (identifier-alias resolution) TAP services, no authentication required
  for either (`src/provenance/data.py`).
- Exact (haversine) angular-separation and cross-match summary statistics
  (`src/provenance/crossmatch.py`).
- CLI (`provenance run`) and 7 fast tests + 3 live-network tests.

### Results

- 293 real confirmed-exoplanet host stars audited: 91.5% resolve in
  SIMBAD by exact name; of those, 95.1% agree in position within 5 arcsec
  (median separation 0.28 arcsec, max 20.1 arcsec).
- Nearly all unresolved names are KMTNet microlensing lens designations
  (`KMT-*-BLG-*L`), consistent with those lens stars being too
  faint/unconfirmed to have their own SIMBAD entry.
- The four largest position discrepancies are all nearby, high-proper-
  motion M dwarfs, consistent with an epoch-difference (proper motion)
  explanation rather than a data error in either archive.
