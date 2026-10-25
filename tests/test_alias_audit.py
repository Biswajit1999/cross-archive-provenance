import pytest

from provenance.alias_audit import alias_variants, audit_aliases
from provenance.data import SimbadQueryError


def _match(main_id="TIC 320419023", ra=118.0726215, dec=11.8241773):
    return {"simbad_main_id": main_id, "simbad_ra": ra, "simbad_dec": dec}


def test_variants_are_bounded_and_deduplicated():
    assert alias_variants("TIC 320419023") == ("TIC320419023", "TIC-320419023")
    assert alias_variants("Qatar-5") == ("Qatar 5",)
    assert alias_variants("OGLE-2017-BLG-1049L") == ("OGLE 2017 BLG 1049L",)


def test_empty_name_rejected():
    with pytest.raises(ValueError):
        alias_variants("  ")


def test_resolved_only_with_unique_nearby_id():
    calls = []

    def resolve(alias):
        calls.append(alias)
        return _match() if alias == "TIC320419023" else None

    result = audit_aliases("TIC 320419023", 118.0726215, 11.8241773, resolve)
    assert result.status == "resolved"
    assert result.main_id == "TIC 320419023"
    assert calls == ["TIC320419023", "TIC-320419023"]


def test_out_of_radius_is_review_not_match():
    result = audit_aliases("Qatar-5", 7.05, 42.06, lambda _: _match("Qatar 5", 8, 42))
    assert result.status == "position_review"
    assert result.separation_arcsec > 5


def test_conflicting_ids_ambiguous():
    result = audit_aliases(
        "TIC 320419023", 118.0726215, 11.8241773, lambda alias: _match(alias)
    )
    assert result.status == "ambiguous"


def test_no_candidates_does_not_query():
    result = audit_aliases("HD 2", 0, 0, lambda _: pytest.fail("unexpected network"))
    assert result.status == "not_found"
    assert result.attempted == ()


def test_query_failure_never_counted_as_not_found():
    def broken(_):
        raise SimbadQueryError("offline")

    result = audit_aliases("Qatar-5", 7.05, 42.06, broken)
    assert result.status == "query_failed"


def test_partial_failure_never_claims_resolved():
    def resolve(alias):
        if alias == "TIC-320419023":
            raise SimbadQueryError("timeout")
        return _match()

    result = audit_aliases("TIC 320419023", 118.0726215, 11.8241773, resolve)
    assert result.status == "query_failed"


def test_nonmatches_not_found():
    result = audit_aliases("Qatar-5", 7.05, 42.06, lambda _: None)
    assert result.status == "not_found"


@pytest.mark.parametrize("ra,dec,gate", [(360, 0, 5), (0, 91, 5), (0, 0, 0)])
def test_bad_coordinates_or_gate(ra, dec, gate):
    with pytest.raises(ValueError):
        audit_aliases("Qatar-5", ra, dec, lambda _: None, gate)


def test_nonfinite_resolved_position_rejected():
    with pytest.raises(SimbadQueryError):
        audit_aliases(
            "Qatar-5", 7.05, 42.06, lambda _: _match("Qatar 5", float("nan"), 42)
        )
