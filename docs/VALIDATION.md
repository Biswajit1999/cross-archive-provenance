# Validation

| Check | Method | Test | Result |
|---|---|---|---|
| Angular separation: hand calculation (1 arcsec offset) | Direct arithmetic | `tests/test_crossmatch.py::test_angular_separation_hand_calculation` | Within 1e-4 arcsec |
| Angular separation: identical points give zero | Analytic limit | `tests/test_crossmatch.py::test_angular_separation_same_point_is_zero` | Exact |
| Angular separation: 180-degree offset gives exactly 180*3600 arcsec | Analytic limit (haversine, not flat-sky approximation) | `tests/test_crossmatch.py::test_angular_separation_antipodal_like_large_offset` | Within 1e-6 relative |
| summarize_crossmatch: resolution rate and match-radius counting | Hand-constructed cases | `tests/test_crossmatch.py` (4 cases) | Pass |
| summarize_crossmatch excludes query_failed rows from resolution_rate | Hand-constructed case with a query_failed row | `tests/test_crossmatch.py::test_summarize_crossmatch_excludes_query_failures_from_resolution_rate` | Pass |
| resolve_in_simbad raises SimbadQueryError (not None) on a network failure | Monkeypatched `urlopen` failure | `tests/test_data.py::test_resolve_in_simbad_raises_on_network_failure_not_returns_none` | Pass |
| `_resolve_with_retries` resolves immediately, doesn't retry a genuine not-found, recovers after one transient failure, and reports `query_failed` after exhausting retries | Monkeypatched `resolve_in_simbad` | `tests/test_cli.py` (4 cases) | Pass |
| Live NASA Exoplanet Archive fetch returns real host names/positions | Live TAP query | `tests/test_data.py::test_live_load_host_stars` | Pass, 20/20 rows populated |
| Live SIMBAD resolution of a known real star (HD 209458) returns the correct position | Live TAP query, cross-checked against the well-known HD 209458 system | `tests/test_data.py::test_live_resolve_known_host_in_simbad` | Pass, RA in expected range |
| Live SIMBAD correctly returns "not found" for a fabricated name | Live TAP query | `tests/test_data.py::test_live_resolve_nonexistent_host_returns_none` | Pass |

## Real result, physically interpreted rather than just reported

The default 293-object run (`results/default/summary.json`, regenerated
2026-08-29 with the query-failure fix, 0 query failures this run) gives a
91.5% SIMBAD resolution rate; of the 25 unresolved names, 84% (21/25) are
microlensing-survey lens designations (KMTNet, OGLE, MOA), and the
largest positional discrepancies (6-20 arcsec) are all nearby,
high-proper-motion M dwarfs. Both patterns have a physically sensible
explanation (faint/unconfirmed lens stars; proper motion between quoted
epochs) that this project states explicitly rather than leaving as an
unexplained anomaly -- see `docs/LIMITATIONS.md`. Two prior claims about
this same result were checked directly against the committed CSVs while
regenerating this release and found to be wrong: "nearly all unresolved
are KMTNet" (true of only 44%, not 84%+) and a stated top-4
position-discrepancy list that did not match the actual sorted CSV --
both corrected (`docs/CLAIMS.md` "Superseded / corrected claims").

## Reproducing these checks

```bash
pytest -q                 # 13 tests, fixture/logic-based, no network, < 1 s
pytest -q -m network        # + 3 live queries to real archives
```

## Explicitly not yet validated

- No fuzzy/alternate-format retry for unresolved names (docs/LIMITATIONS.md).
- No independent proper-motion check to confirm the epoch-difference
  explanation for the flagged position discrepancies.
- No third-archive (Gaia) cross-check.
- The retry logic's real-world behavior under an actual live network
  failure (as opposed to a monkeypatched one) has not been observed --
  the regenerated default run had 0 query failures.
