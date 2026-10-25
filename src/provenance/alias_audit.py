"""Conservative SIMBAD alias-format retry with independent positional veto.

No fuzzy astronomical identification: punctuation and spacing only.
Out-of-radius candidates require review, not automatic rejection.
"""
from __future__ import annotations

import math
import re
from collections.abc import Callable
from dataclasses import dataclass

from .crossmatch import angular_separation_arcsec
from .data import SimbadQueryError


@dataclass(frozen=True)
class AliasAudit:
    original_name: str
    status: str
    candidates: tuple[str, ...]
    attempted: tuple[str, ...]
    main_id: str | None = None
    separation_arcsec: float | None = None
    reason: str | None = None


def alias_variants(name: str) -> tuple[str, ...]:
    """Bounded, deterministic punctuation/spacing variants only."""
    original = name.strip()
    if not original:
        raise ValueError("empty identifier")
    variants = []
    spaced = re.sub(r"\s+", " ", original.replace("_", " "))
    variants.append(spaced)
    variants.append(re.sub(r"\s*-\s*", " ", spaced))
    variants.append(re.sub(r"\s*-\s*", "-", spaced))
    match = re.fullmatch(r"([A-Za-z]{2,6})\s+(\d{3,})", spaced)
    if match:
        variants.append(match.group(1) + match.group(2))
        variants.append(match.group(1) + "-" + match.group(2))
    return tuple(dict.fromkeys(v for v in variants if v and v != original))


def audit_aliases(
    name: str,
    ra_deg: float,
    dec_deg: float,
    resolver: Callable[[str], dict | None],
    max_separation_arcsec: float = 5.0,
) -> AliasAudit:
    """Retry formatting variants after the original exact query returned no match.

    Accept only one consistent SIMBAD main ID within the declared
    positional review gate. Network failures cannot count as not-found.
    """
    if not (-90 <= dec_deg <= 90) or not (0 <= ra_deg < 360):
        raise ValueError("invalid ICRS coordinates")
    if not (0 < max_separation_arcsec < 3600):
        raise ValueError("invalid positional gate")
    variants = alias_variants(name)
    attempted = []
    found = []
    failed = False
    for candidate in variants:
        attempted.append(candidate)
        try:
            result = resolver(candidate)
        except SimbadQueryError:
            failed = True
            continue
        if result is None:
            continue
        try:
            mid = str(result["simbad_main_id"])
            sep = angular_separation_arcsec(
                ra_deg, dec_deg, float(result["simbad_ra"]), float(result["simbad_dec"])
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise SimbadQueryError(f"malformed alias result for {candidate!r}") from exc
        if not mid.strip() or not math.isfinite(sep):
            raise SimbadQueryError(f"invalid alias coordinates/ID for {candidate!r}")
        found.append((mid, float(sep)))
    base = {"original_name": name, "candidates": variants, "attempted": tuple(attempted)}
    if failed:
        return AliasAudit(**base, status="query_failed", reason="at least one alias query failed")
    if not found:
        return AliasAudit(**base, status="not_found")
    if len({mid for mid, _ in found}) != 1:
        return AliasAudit(**base, status="ambiguous", reason="multiple distinct SIMBAD IDs")
    if any(sep > max_separation_arcsec for _, sep in found):
        return AliasAudit(
            **base, status="position_review", main_id=found[0][0],
            separation_arcsec=max(sep for _, sep in found),
            reason="position exceeds gate; epoch/proper motion may matter",
        )
    return AliasAudit(
        **base, status="resolved", main_id=found[0][0],
        separation_arcsec=max(sep for _, sep in found),
    )
