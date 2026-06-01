"""Tests for cattheory.colimits, normalize_slug properties, diagnostics CLI."""

from __future__ import annotations

import io
import json
import sys

from hypothesis import given, strategies as st

from src.cattheory import colimit_cone_factors, colimit_of_setlist_functor, coproduct
from src.cli import main as cli_main
from src.integration.reconcile import build_compendium
from src.models import canonical_song_id, normalize_slug
from src.seed import load_seed_compendium


def test_normalize_slug_idempotent():
    """Slug of a slug is itself."""
    for raw in ("Box of Rain", "Mr. Charlie", "Mississippi Half-Step Uptown Toodeloo"):
        slug = normalize_slug(raw)
        assert normalize_slug(slug) == slug


def test_canonical_song_id_collapses_punctuation():
    a = canonical_song_id("St. Stephen")
    b = canonical_song_id("St Stephen")
    assert a == b
    assert canonical_song_id("Truckin'") == "truckin"


@given(st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd", "Zs"))))
def test_normalize_slug_only_emits_safe_chars(s):
    out = normalize_slug(s)
    assert all(c.isalnum() or c == "_" for c in out)
    if out:
        assert not out.startswith("_")
        assert not out.endswith("_")


@given(st.text(min_size=1, max_size=20).filter(lambda x: x.strip()))
def test_canonical_song_id_total_for_nonblank(title):
    slug = canonical_song_id(title)
    if slug:  # may be empty if title was pure punctuation
        assert isinstance(slug, str)
        assert slug.islower() or slug.isdigit() or "_" in slug


def test_coproduct_disjoint_union(compendium):
    half_a = build_compendium(shows=compendium.shows[: len(compendium.shows) // 2])
    half_b = build_compendium(shows=compendium.shows[len(compendium.shows) // 2 :])
    merged = coproduct(half_a, half_b)
    # Disjoint union, then deduplicated by reconcile — should equal the full set.
    assert {s.slug for s in merged.shows} == {s.slug for s in compendium.shows}


def test_colimit_of_setlist_functor(compendium):
    apex = colimit_of_setlist_functor(compendium)
    # The colimit is the union of every cumulative setlist, i.e. all played songs.
    played = {p.song_slug for p in compendium.performances}
    assert apex == frozenset(played)


def test_colimit_of_empty_compendium():
    empty = build_compendium()
    assert colimit_of_setlist_functor(empty) == frozenset()


def test_colimit_cone_factors_on_seed(compendium):
    from src.cattheory.functors import setlist_functor

    assert colimit_cone_factors(setlist_functor(compendium))


def test_colimit_cone_factors_handles_empty():
    assert colimit_cone_factors({})


def test_cli_diagnostics():
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        cli_main(["diagnostics"])
    finally:
        sys.stdout = old
    parsed = json.loads(buf.getvalue())
    assert parsed["honesty_boundary"]["ok"] is True
    assert parsed["seed_schema"]["ok"] is True
    assert parsed["totals"]["shows"] >= 80


def test_seed_loader_with_honesty_off():
    """The escape hatch path exists for boundary-testing only."""
    comp = load_seed_compendium(enforce_honesty=False)
    assert comp is not None
