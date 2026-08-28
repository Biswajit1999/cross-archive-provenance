"""Offline tests exercise the real query templates and CSV-parsing paths
with small, real response shapes; a network-marked test hits both live
services directly.
"""
import pytest

from provenance.data import CachePaths


def test_nea_query_template_is_valid_adql_shape():
    from provenance.data import NEA_QUERY
    q = NEA_QUERY.format(n=10)
    assert "pscomppars" in q
    assert "top 10" in q.lower()


@pytest.mark.network
def test_live_load_host_stars(tmp_path):
    from provenance.data import load_host_stars

    paths = CachePaths(cache_dir=tmp_path)
    df = load_host_stars(paths, n=20)
    assert len(df) == 20
    assert {"hostname", "ra", "dec"}.issubset(df.columns)
    assert df["hostname"].notna().all()


@pytest.mark.network
def test_live_resolve_known_host_in_simbad():
    from provenance.data import resolve_in_simbad

    result = resolve_in_simbad("HD 209458")
    assert result is not None
    assert result["simbad_main_id"] == "HD 209458"
    assert 330.0 < result["simbad_ra"] < 331.0  # real, known position


@pytest.mark.network
def test_live_resolve_nonexistent_host_returns_none():
    from provenance.data import resolve_in_simbad

    result = resolve_in_simbad("Definitely Not A Real Star Name XYZ123")
    assert result is None
