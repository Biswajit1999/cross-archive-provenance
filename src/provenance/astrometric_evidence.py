"""Independent astrometric consistency diagnostics; angles use tangent-plane arcseconds.

The caller must supply covariance in east/north tangent-plane coordinates. Gaia
catalogue RA errors cannot be used as east errors without coordinate conversion.
These functions are diagnostics, not a validated catalog cross-identification.
"""
from __future__ import annotations

import numpy as np


def _positive_covariance(cov: np.ndarray, size: int) -> np.ndarray:
    matrix = np.asarray(cov, dtype=float)
    if matrix.shape != (size, size) or not np.all(np.isfinite(matrix)):
        raise ValueError(f"covariance must be a finite {size}x{size} matrix")
    if not np.allclose(matrix, matrix.T, rtol=1e-10, atol=1e-12):
        raise ValueError("covariance must be symmetric")
    if np.linalg.eigvalsh(matrix).min() <= 0:
        raise ValueError("covariance must be positive definite")
    return matrix


def propagate_position_covariance(cov4_mas2: np.ndarray, years: float) -> np.ndarray:
    """Propagate [east, north, pm_east, pm_north] covariance to epoch dt.

    Position in mas, proper motion in mas/yr. Full cross-covariance retained.
    Output is in arcsec^2. No perspective acceleration/parallax model.
    """
    cov = _positive_covariance(cov4_mas2, 4)
    if not np.isfinite(years):
        raise ValueError("years must be finite")
    jacobian = np.array([[1, 0, years, 0], [0, 1, 0, years]], dtype=float)
    return jacobian @ cov @ jacobian.T / 1e6


def fit_epoch_span(
    observed_offset_arcsec: np.ndarray,
    proper_motion_mas_per_year: np.ndarray,
    covariance_arcsec2: np.ndarray,
) -> dict:
    """GLS estimate of epoch separation under *fixed* 2D positional covariance.

    The sign of dt follows observed_offset = dt * proper_motion / 1000.
    The returned chi2 has one nominal degree of freedom only if the input
    covariance is complete and fixed independently of dt.
    """
    y = np.asarray(observed_offset_arcsec, dtype=float)
    pm = np.asarray(proper_motion_mas_per_year, dtype=float) / 1000
    cov = _positive_covariance(covariance_arcsec2, 2)
    if (
        y.shape != (2,) or pm.shape != (2,)
        or not np.all(np.isfinite(y)) or not np.all(np.isfinite(pm))
    ):
        raise ValueError("offset and proper motion must be finite two-vectors")
    inv_pm = np.linalg.solve(cov, pm)
    information = float(pm @ inv_pm)
    if information <= 1e-20:
        raise ValueError("proper motion is too small to estimate an epoch span")
    dt = float(y @ inv_pm / information)
    residual = y - dt * pm
    return {
        "epoch_years": dt,
        "epoch_sigma_years": float(1 / np.sqrt(information)),
        "cross_track_chi2": float(residual @ np.linalg.solve(cov, residual)),
        "residual_east_arcsec": float(residual[0]),
        "residual_north_arcsec": float(residual[1]),
    }


def candidate_posteriors(
    offsets_arcsec: np.ndarray,
    covariances_arcsec2: np.ndarray,
    background_density_arcsec2: np.ndarray,
    counterpart_prior: float,
) -> dict:
    """Likelihood-ratio counterpart weights vs a local uniform Poisson background.

    Each candidate's LR is the 2D Gaussian positional density divided by
    the local background surface density. Assumes at most one counterpart,
    independent positional errors, and a complete candidate search region.
    The no-counterpart hypothesis is explicitly retained. These are model
    probabilities, NOT calibrated probabilities of true astrophysical IDs.
    """
    offsets = np.asarray(offsets_arcsec, dtype=float)
    covs = np.asarray(covariances_arcsec2, dtype=float)
    rho = np.asarray(background_density_arcsec2, dtype=float)
    if offsets.ndim != 2 or offsets.shape[1] != 2 or len(offsets) == 0:
        raise ValueError("offsets must have shape (n, 2) with n > 0")
    n = len(offsets)
    if covs.shape != (n, 2, 2) or rho.shape != (n,):
        raise ValueError("covariances and densities must match candidate count")
    if not np.all(np.isfinite(offsets)) or not np.all(np.isfinite(rho)) or np.any(rho <= 0):
        raise ValueError("offsets must be finite and background densities positive")
    if not 0 < counterpart_prior < 1:
        raise ValueError("counterpart_prior must lie strictly between zero and one")
    log_lr = np.empty(n)
    for i in range(n):
        cov = _positive_covariance(covs[i], 2)
        sign, logdet = np.linalg.slogdet(cov)
        if sign <= 0:
            raise ValueError("covariance determinant must be positive")
        mahal = offsets[i] @ np.linalg.solve(cov, offsets[i])
        log_lr[i] = -np.log(2 * np.pi) - 0.5 * logdet - 0.5 * mahal - np.log(rho[i])
    # Stable softmax includes the no-match hypothesis with log-weight 0.
    log_weights = np.r_[0.0, np.log(counterpart_prior / (1 - counterpart_prior)) + log_lr]
    scaled = np.exp(log_weights - np.max(log_weights))
    posterior = scaled / scaled.sum()
    return {"p_no_counterpart": float(posterior[0]), "p_candidates": posterior[1:]}
