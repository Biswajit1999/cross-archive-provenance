import numpy as np
import pytest

from provenance.astrometric_evidence import (
    candidate_posteriors, fit_epoch_span, propagate_position_covariance,
)


def test_propagation_retains_position_motion_correlation():
    cov = np.diag([4., 9., 1., 1.])
    cov[0, 2] = cov[2, 0] = 1.5
    result = propagate_position_covariance(cov, 2)
    assert result[0, 0] == pytest.approx((4 + 4 + 6) / 1e6)
    assert result[1, 1] == pytest.approx((9 + 4) / 1e6)


def test_propagation_cross_axis_covariance():
    cov = np.eye(4)
    cov[0, 1] = cov[1, 0] = 0.25
    assert propagate_position_covariance(cov, 0)[0, 1] == pytest.approx(2.5e-7)


def test_propagation_rejects_non_positive_definite_covariance():
    with pytest.raises(ValueError):
        propagate_position_covariance(np.zeros((4, 4)), 1)


def test_epoch_recovery_with_cross_track_residual():
    fit = fit_epoch_span([3.0, 0.2], [200., 0.], np.diag([0.01, 0.04]))
    assert fit["epoch_years"] == pytest.approx(15)
    assert fit["epoch_sigma_years"] == pytest.approx(0.5)
    assert fit["cross_track_chi2"] == pytest.approx(1.0)


def test_epoch_covariance_is_not_confused_with_gaia_only_uncertainty():
    fit = fit_epoch_span([1, 0], [100, 0], np.diag([0.01, 0.01]))
    assert fit["epoch_years"] == pytest.approx(10)
    assert fit["epoch_sigma_years"] == pytest.approx(1)


def test_zero_motion_rejected():
    with pytest.raises(ValueError):
        fit_epoch_span([1, 0], [0, 0], np.eye(2))


def test_candidate_weights_normalize_and_prefer_closer_object():
    fit = candidate_posteriors([[0, 0], [2, 0]], np.array([np.eye(2)] * 2),
                               [0.01, 0.01], 0.9)
    assert fit["p_no_counterpart"] + fit["p_candidates"].sum() == pytest.approx(1)
    assert fit["p_candidates"][0] > fit["p_candidates"][1]


def test_candidate_posterior_respects_background_density():
    fit = candidate_posteriors([[0, 0], [0, 0]], np.array([np.eye(2)] * 2),
                               [0.01, 0.1], 0.5)
    assert fit["p_candidates"][0] / fit["p_candidates"][1] == pytest.approx(10)


def test_no_counterpart_can_dominate_for_distant_candidates():
    fit = candidate_posteriors([[100, 100]], np.array([np.eye(2)]), [0.1], 0.5)
    assert fit["p_no_counterpart"] == pytest.approx(1)


def test_invalid_candidate_covariance_rejected():
    with pytest.raises(ValueError):
        candidate_posteriors([[0, 0]], np.array([np.zeros((2, 2))]), [0.1], 0.5)
