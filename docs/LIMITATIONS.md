# Limitations and Known Failure Modes

## Exact-string name matching only

SIMBAD resolution uses an exact match against the `ident` alias table.
Of the 25 unresolved names in the default run
(`results/default/unresolved_hosts.csv`), 21 (84%) are microlensing-survey
lens designations (11 `KMT-*-BLG-*L` KMTNet, 9 `OGLE-*-BLG-*L`, 1
`MOA-*-BLG-*L`), consistent with a real, physically sensible explanation:
microlensing-discovered lens stars are often too faint or unconfirmed to
have their own SIMBAD catalog entry at all, independent of any
string-matching issue. An earlier version of this document said "nearly
all ... are KMTNet" specifically, which was true only of a 44% subset and
was not checked against the full breakdown before publishing (an
external review, Codex, caught this); corrected above.

The remaining 4 unresolved names -- `Lupus-TR-3`, `Qatar-5`, `Qatar-8`,
`TIC 320419023` -- are not microlensing objects and do not fit that
explanation. This project does not distinguish "genuinely absent from
SIMBAD" from "present under a differently formatted alias," so these 4
names have not been further investigated; a fuzzy or multi-format retry
is a real, tractable follow-up (tracked as a repository issue) that could
resolve whether they are a genuine gap or a name-format mismatch.

## Position discrepancies are not necessarily errors

The four objects flagged with the largest separation (>5 arcsec) in the
default run (`results/default/position_discrepancies.csv`, sorted by
`separation_arcsec`) are HD 285968 (20.1 arcsec), GJ 876 (18.1 arcsec),
GJ 674 (16.3 arcsec), and GJ 328 (16.2 arcsec) -- all nearby M dwarfs. An
earlier version of this document listed a different four objects (GJ
1061, GJ 3021, GJ 328, GJ 674) that did not match the file it cited
(an external review, Codex, caught this); corrected above. The most
likely explanation for all of these is genuine **proper motion**: nearby,
fast-moving stars have measurably different apparent positions depending
on the observation epoch each archive's position is quoted at, not a
data-entry error in either archive. This project does not fetch or
subtract proper motion (e.g. from Gaia) to test this explanation directly
-- doing so is a natural, real follow-up (tracked as a repository issue)
that would let this project distinguish "epoch-difference-explained" from
"genuinely discrepant" position mismatches.

## Network failures were silently miscounted as "not found" (fixed in v0.2.0)

`resolve_in_simbad` used to catch every exception from the live SIMBAD
query (network error, timeout, malformed response) and return `None` for
all of them -- the same value returned when SIMBAD genuinely has no entry
for a name. A run that hit a transient network failure for some name
would silently record that name as unresolved, with no way to tell the
two cases apart after the fact (an external review, Codex, caught this).
Fixed: such failures now raise `SimbadQueryError`, are retried up to
twice, and if still unresolved after retries are recorded as
`query_failed` in `results/default/query_failures.csv` (when non-empty)
-- excluded from both the resolved and not-found counts, rather than
folded into "not found." The default run committed here happened to have
0 query failures, so the previously reported resolution-rate number was
not itself affected by this bug in that particular run -- but the code
was still wrong, and a different run (e.g. under a flaky connection)
could have given a materially different, silently-corrupted result.

## Only two archives compared

This version compares the NASA Exoplanet Archive against SIMBAD only. A
three-way comparison (adding Gaia DR3 via VizieR, following the pattern
already used elsewhere in this programme) would strengthen the audit and
is tracked as a repository issue.

## Sample is exoplanet host stars only

This audit's conclusions are scoped to confirmed-exoplanet host stars
specifically (many of which are well-studied, bright, nearby systems);
resolution rates and discrepancy patterns could differ for a more general
astronomical object sample.

## Rate limiting is a documented compromise, not a guarantee

`cli.py` sleeps 0.05 s between SIMBAD queries to be considerate of the
free public service; this is not a guarantee against service throttling
under heavier use, and the full 300-object run's exact wall-clock time is
not fixed.
