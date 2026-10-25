# Conservative SIMBAD alias retry — 25 October 2026

Addresses issue #1 without changing the existing crossmatch or published results. Only punctuation and whitespace variants are proposed; no edit-distance, wildcard, substring, or nearest-name guesswork. The 25 previously not-found names in `results/default/unresolved_hosts.csv` produce an **offline candidate inventory**, not recovered identifications.

Live queries require explicit `--live` and are rate-limited. A match is accepted only if candidate queries agree on one SIMBAD main ID and the reported position is within a 5-arcsec **review gate**. Conflicting IDs are `ambiguous`, larger offsets are `position_review`, and any network failure is `query_failed`, never `not_found`. Proper motion and mismatched epochs can cause genuine larger offsets. A negative retry does not prove absence from SIMBAD.

Reproduce offline: `PYTHONPATH=src python scripts/alias_retry_audit.py --out /tmp/alias_audit.json`; opt-in live: add `--live --min-interval 1`. Input SHA256 and candidate/status records are included in the JSON. `PYTHONPATH=src pytest tests/test_alias_audit.py -q` runs the no-network regression suite. Never revise published resolution rates until live results and coordinates have been independently validated.
