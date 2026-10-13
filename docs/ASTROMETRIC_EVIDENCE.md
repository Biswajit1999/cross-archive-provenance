# Covariance-aware astrometric evidence (synthetic diagnostics)

`provenance.astrometric_evidence` adds three **independent** checks to the existing Gaia proper-motion comparison:

1. Propagate a full 4×4 tangent-plane position/proper-motion covariance using `J C Jᵀ`. Inputs are mas and mas/yr; output arcsec². The module does **not** convert Gaia catalog RA uncertainties into east coordinates; callers must perform that transformation correctly.
2. Fit an unknown epoch span with generalized least squares, retaining the cross-track residual and a *conditional* 1σ uncertainty. Covariance is assumed fixed during the fit; for realistic Gaia epoch propagation the covariance itself depends on the epoch and the nonlinear problem must be refitted.
3. Compare positional counterpart hypotheses with a Gaussian/Poisson likelihood ratio, explicitly allowing **no counterpart**. Posterior weights require a specified counterpart prior, local background density, a complete candidate list, and at most one true counterpart; do not interpret these numbers as validated catalog-identification probabilities.

Run `python scripts/analyze_astrometric_evidence.py --trials 2000 --seed 20261013` to produce a seeded **synthetic** coverage summary. `PYTHONPATH=src pytest -q tests/test_astrometric_evidence.py` exercises deterministic edge cases. These checks do not close the live-archive Gaia cross-identification issues and do not replace the existing Gaia DR3 source-ID evidence.
