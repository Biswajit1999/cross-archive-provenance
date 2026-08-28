# Data Sources

## NASA Exoplanet Archive

- **Table**: `pscomppars` (Planetary Systems Composite Parameters),
  queried live via TAP, `https://exoplanetarchive.ipac.caltech.edu/TAP`.
- **Fields used**: `hostname`, `ra`, `dec`, `sy_dist`.
- **Licence**: public domain (U.S. Government work); citation of the
  archive requested.

## SIMBAD

- **Provider**: CDS (Centre de Données astronomiques de Strasbourg).
- **Endpoint**: `https://simbad.u-strasbg.fr/simbad/sim-tap/sync`, ADQL,
  no authentication required.
- **Tables used**: `ident` (identifier aliases) joined to `basic`
  (main record: `main_id`, `ra`, `dec`) -- the standard robust
  name-resolution pattern, since an exoplanet-archive hostname (e.g.
  "Kepler-10") is often an alias rather than SIMBAD's own `main_id`.
- **Licence**: CDS data are freely usable for research with attribution.

## What this project measures

For each of N real confirmed-exoplanet host stars (from the NASA
Exoplanet Archive), this project queries SIMBAD by that exact name string
and records: (a) whether SIMBAD resolves the name at all, and (b) if
resolved, the angular separation between the archive's and SIMBAD's
independently maintained position for that object. Both are real,
directly measured quantities -- not estimates or literature values.
