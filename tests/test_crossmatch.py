import numpy as np
import pandas as pd
import pytest

from provenance.crossmatch import angular_separation_arcsec, summarize_crossmatch


def test_angular_separation_hand_calculation():
    # 1 arcsec offset in dec at dec=0 -> exactly 1 arcsec separation
    sep = angular_separation_arcsec(0.0, 0.0, 0.0, 1.0 / 3600.0)
    assert sep == pytest.approx(1.0, rel=1e-4)


def test_angular_separation_same_point_is_zero():
    assert angular_separation_arcsec(150.0, -20.0, 150.0, -20.0) == pytest.approx(0.0, abs=1e-9)


def test_angular_separation_antipodal_like_large_offset():
    # 180 degrees apart on the equator -> exactly 180*3600 arcsec
    sep = angular_separation_arcsec(0.0, 0.0, 180.0, 0.0)
    assert sep == pytest.approx(180 * 3600, rel=1e-6)


def test_summarize_crossmatch_all_resolved_within_radius():
    df = pd.DataFrame({
        "hostname": ["A", "B"], "ra": [10.0, 20.0], "dec": [5.0, 5.0],
        "resolution_status": ["resolved", "resolved"],
        "simbad_ra": [10.0001, 20.0001], "simbad_dec": [5.0001, 5.0001],
    })
    result = summarize_crossmatch(df, match_radius_arcsec=5.0)
    assert result["n_queried"] == 2
    assert result["resolution_rate"] == 1.0
    assert result["n_within_match_radius"] == 2


def test_summarize_crossmatch_handles_unresolved_hosts():
    df = pd.DataFrame({
        "hostname": ["A", "B"], "ra": [10.0, 20.0], "dec": [5.0, 5.0],
        "resolution_status": ["resolved", "not_found"],
        "simbad_ra": [10.0, np.nan], "simbad_dec": [5.0, np.nan],
    })
    result = summarize_crossmatch(df, match_radius_arcsec=5.0)
    assert result["n_resolved_in_simbad"] == 1
    assert result["n_not_found_in_simbad"] == 1
    assert result["resolution_rate"] == 0.5


def test_summarize_crossmatch_detects_large_offset():
    df = pd.DataFrame({
        "hostname": ["A"], "ra": [10.0], "dec": [5.0],
        "resolution_status": ["resolved"], "simbad_ra": [10.5], "simbad_dec": [5.0],  # ~0.5 deg = 1800 arcsec off
    })
    result = summarize_crossmatch(df, match_radius_arcsec=5.0)
    assert result["n_within_match_radius"] == 0
    assert result["max_separation_arcsec"] > 1000


def test_summarize_crossmatch_excludes_query_failures_from_resolution_rate():
    """Regression test: an earlier version had only a boolean `resolved`
    column, which conflated "SIMBAD queried successfully, no match" with
    "the query itself failed" -- silently letting unrelated network
    conditions change the reported resolution rate and unresolved-name
    list (an external review, Codex, caught this). A query_failed row
    should be excluded from the resolution_rate denominator and reported
    separately, not counted as either resolved or not_found."""
    df = pd.DataFrame({
        "hostname": ["A", "B", "C"], "ra": [10.0, 20.0, 30.0], "dec": [5.0, 5.0, 5.0],
        "resolution_status": ["resolved", "not_found", "query_failed"],
        "simbad_ra": [10.0, np.nan, np.nan], "simbad_dec": [5.0, np.nan, np.nan],
    })
    result = summarize_crossmatch(df, match_radius_arcsec=5.0)
    assert result["n_queried"] == 3
    assert result["n_query_failed"] == 1
    assert result["n_resolved_in_simbad"] == 1
    assert result["n_not_found_in_simbad"] == 1
    assert result["resolution_rate"] == pytest.approx(0.5)  # 1/(1+1), the query_failed row excluded
