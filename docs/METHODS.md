# Methods

## Research question

How reliably can a real object (a confirmed exoplanet host star) be
cross-identified and positionally cross-matched between two independently
maintained astronomical archives, and where does that cross-identification
fail or disagree?

## Null hypothesis

H0: Every confirmed-exoplanet host-star name from the NASA Exoplanet
Archive resolves in SIMBAD, and every resolved position agrees with the
archive's position within a small (5 arcsec) tolerance.

Tested on a real sample (`results/default/summary.json`); see
`paper/manuscript.md` Section 4 for the generated resolution rate and
positional-agreement fraction, and whether H0 is rejected.

## Method

1. **Host-star sample** (`data.py::load_host_stars`): a real, live query
   of the NASA Exoplanet Archive's composite parameters table.
2. **Cross-archive resolution** (`data.py::resolve_in_simbad`): for each
   host name, a live SIMBAD identifier-alias query, following the
   standard robust name-resolution pattern (join `ident` to `basic`
   rather than requiring an exact `main_id` match). A query that fails to
   complete (network error, timeout, malformed response) raises
   `SimbadQueryError` rather than being treated as "not found";
   `cli.py::_resolve_with_retries` retries such failures up to twice
   before recording them separately as `query_failed`, excluded from
   both the resolved and not-found counts (`docs/LIMITATIONS.md`).
3. **Positional consistency** (`crossmatch.py`): exact (haversine)
   angular separation between the two archives' independently maintained
   positions for the same resolved object, and a fixed match-radius
   threshold (default 5 arcsec) for flagging discrepancies.

## What this project does not do

- Does not determine *why* a name fails to resolve or a position
  disagrees (e.g. typo, alias not yet in SIMBAD, genuine astrometric
  update) -- it quantifies the rate and flags the specific cases for
  follow-up, per `docs/LIMITATIONS.md`.
- Does not attempt fuzzy/approximate name matching -- an exact-string
  SIMBAD alias lookup, which is itself informative (it shows what a
  literal-minded downstream tool would experience).
- Does not cross-match a third archive (e.g. Gaia) in this version.
