# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/).

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
