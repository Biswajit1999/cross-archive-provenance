import pandas as pd
import pytest

from provenance.proper_motion import motion_diagnostics, tangent_offset_arcsec


def test_tangent_offset_applies_cos_dec():
    east, north = tangent_offset_arcsec(10, 60, 10.001, 60.002)
    assert east == pytest.approx(1.8, rel=4e-5)
    assert north == pytest.approx(7.2)


def test_motion_diagnostics_recovers_known_epoch_span():
    row = pd.Series(
        {
            "hostname": "synthetic",
            "source_id": 1,
            "simbad_ra": 10.0,
            "simbad_dec": 0.0,
            "nea_ra": 10.0 + 16 / 3600,
            "nea_dec": 0.0,
            "pmra": 1000.0,
            "pmdec": 0.0,
            "ra_error": 0.1,
            "dec_error": 0.1,
            "pmra_error": 0.01,
            "pmdec_error": 0.01,
            "ra_pmra_corr": 0.0,
            "dec_pmdec_corr": 0.0,
            "candidate_separation_arcsec": 0.1,
            "candidate_margin_arcsec": 5.0,
        }
    )
    result = motion_diagnostics(row)
    assert result["implied_epoch_span_years"] == pytest.approx(16)
    assert result["fixed_16yr_residual_arcsec"] < 1e-8
    assert result["offset_explained_fraction"] == pytest.approx(1)
