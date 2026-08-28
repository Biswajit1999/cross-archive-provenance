# Limitations and Known Failure Modes

## Exact-string name matching only

SIMBAD resolution uses an exact match against the `ident` alias table.
Nearly all unresolved names in the default run (`results/default/unresolved_hosts.csv`)
are `KMT-*-BLG-*L`-style microlensing event/lens designations (KMTNet
Bulge survey), consistent with a real, physically sensible explanation:
microlensing-discovered lens stars are often too faint or unconfirmed to
have their own SIMBAD catalog entry at all, independent of any string-
matching issue. This project does not distinguish "genuinely absent from
SIMBAD" from "present under a differently formatted alias" -- a fuzzy or
multi-format retry is a real, tractable follow-up (tracked as a
repository issue).

## Position discrepancies are not necessarily errors

The four objects flagged with >5 arcsec separation in the default run
(`results/default/position_discrepancies.csv`) are all nearby M dwarfs
(GJ 1061, GJ 3021, GJ 328, GJ 674) with separations of 7-20 arcsec. The
most likely explanation is genuine **proper motion**: nearby, fast-moving
stars have measurably different apparent positions depending on the
observation epoch each archive's position is quoted at, not a data-entry
error in either archive. This project does not fetch or subtract proper
motion (e.g. from Gaia) to test this explanation directly -- doing so is
a natural, real follow-up (tracked as a repository issue) that would let
this project distinguish "epoch-difference-explained" from "genuinely
discrepant" position mismatches.

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
