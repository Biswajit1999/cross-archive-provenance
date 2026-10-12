# Gaia DR3 proper-motion validation

The default audit flags 13 real exoplanet hosts whose NASA Exoplanet Archive (NEA) and SIMBAD positions differ by more than 5 arcsec. This follow-up tests the documented hypothesis that much of that offset is a reference-epoch effect.

## Observational inputs

- The committed NEA/SIMBAD discrepancy table is the fixed target list.
- `scripts/fetch_gaia_discrepancies.py` queries the official ESA Gaia TAP service and retains the five nearest Gaia DR3 candidates in a 30-arcsec cone.
- The candidate CSV, exact ADQL queries, access timestamp, endpoint and SHA-256 receipt are committed under `data/`.

The nearest Gaia source to each NEA position is accepted only when it is within 1 arcsec and has finite proper motion. `candidate_margin_arcsec` records the distance advantage over the second candidate so ambiguity remains visible. Twelve of 13 flagged hosts pass this gate; the pulsar PSR B1257+12 does not, and remains explicitly unvalidated rather than being assigned a nearby unrelated Gaia source.

## Numerical test and units

For tangent-plane east/north offset $\mathbf{d}$ in arcsec and Gaia motion $\boldsymbol{\mu}$ in arcsec yr$^{-1}$,

$$\Delta t_\mathrm{implied}=\frac{\mathbf{d}\cdot\boldsymbol{\mu}}{\boldsymbol{\mu}\cdot\boldsymbol{\mu}}.$$

The cross-track residual is $\|\mathbf{d}-\Delta t_\mathrm{implied}\boldsymbol{\mu}\|$. A predeclared 16-year propagation tests J2000 to Gaia DR3's reference epoch 2016.0. Gaia `pmra` includes $\cos(\delta)$ and is therefore used directly in the east tangent coordinate.

The reported propagation uncertainty includes Gaia RA/Dec and proper-motion errors plus the matching position--motion correlations. It does not include unknown NEA/SIMBAD positional covariances, and is therefore a Gaia-only uncertainty, not the significance of the archive residual.

For the 12 accepted matches, the median implied epoch span is 15.500 years. A fixed 16-year propagation reduces every offset to below 0.65 arcsec and explains a median 96.8% of the original separation. The near-zero cross-track residuals and common implied span support an epoch difference for this subset, subject to the limits below.

## Limits

This is an archive-consistency test, not a new astrometric solution. A nearest cone match is not a formal identifier cross-match. Perspective acceleration and parallax are omitted; exact NEA and SIMBAD source epochs are not available in the committed records. The fixed 16-year residual is therefore diagnostic rather than an adjudication of either archive.

Regenerate with:

```bash
python scripts/fetch_gaia_discrepancies.py  # networked acquisition
python scripts/analyze_proper_motion.py     # offline from committed candidates
```
