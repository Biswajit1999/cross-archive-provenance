# Validation

| Check | Method | Test | Result (2026-08-28) |
|---|---|---|---|
| Angular separation: hand calculation (1 arcsec offset) | Direct arithmetic | `tests/test_crossmatch.py::test_angular_separation_hand_calculation` | Within 1e-4 arcsec |
| Angular separation: identical points give zero | Analytic limit | `tests/test_crossmatch.py::test_angular_separation_same_point_is_zero` | Exact |
| Angular separation: 180-degree offset gives exactly 180*3600 arcsec | Analytic limit (haversine, not flat-sky approximation) | `tests/test_crossmatch.py::test_angular_separation_antipodal_like_large_offset` | Within 1e-6 relative |
| summarize_crossmatch: resolution rate and match-radius counting | Hand-constructed cases | `tests/test_crossmatch.py` (4 cases) | Pass |
| Live NASA Exoplanet Archive fetch returns real host names/positions | Live TAP query | `tests/test_data.py::test_live_load_host_stars` | Pass, 20/20 rows populated |
| Live SIMBAD resolution of a known real star (HD 209458) returns the correct position | Live TAP query, cross-checked against the well-known HD 209458 system | `tests/test_data.py::test_live_resolve_known_host_in_simbad` | Pass, RA in expected range |
| Live SIMBAD correctly returns "not found" for a fabricated name | Live TAP query | `tests/test_data.py::test_live_resolve_nonexistent_host_returns_none` | Pass |

## Real result, physically interpreted rather than just reported

The default 293-object run (`results/default/summary.json`) gives a 91.5%
SIMBAD resolution rate; nearly all unresolved names are KMTNet microlensing
lens designations, and the largest positional discrepancies (7-20 arcsec)
are all nearby, high-proper-motion M dwarfs. Both patterns have a
physically sensible explanation (faint/unconfirmed lens stars; proper
motion between quoted epochs) that this project states explicitly rather
than leaving as an unexplained anomaly -- see `docs/LIMITATIONS.md`.

## Reproducing these checks

```bash
pytest -q                 # 7 tests, fixture-based, no network, < 1 s
pytest -q -m network        # + 3 live queries to real archives
```

## Explicitly not yet validated

- No fuzzy/alternate-format retry for unresolved names (docs/LIMITATIONS.md).
- No independent proper-motion check to confirm the epoch-difference
  explanation for the flagged position discrepancies.
- No third-archive (Gaia) cross-check.
