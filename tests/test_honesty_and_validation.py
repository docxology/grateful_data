"""Tests for honesty boundary, schema validation, opposite/Yoneda category theory."""

from __future__ import annotations


import pytest

from src.cattheory import (
    opposite,
    representable_at,
    yoneda_bijection_count,
    yoneda_embed,
)
from src.cattheory.categories import build_show_category
from src.honesty import (
    FORBIDDEN_LYRIC_KEYS,
    HonestyBoundary,
    HonestyViolation,
    assert_honesty,
)
from src.integration.reconcile import build_compendium
from src.models import Recording, Review
from src.seed import load_seed_compendium
from src.validation import SeedValidationError, assert_valid, validate_seed


def test_seed_loader_passes_honesty():
    # The shipped seed must pass enforce_honesty=True.
    comp = load_seed_compendium()
    assert comp is not None


def test_honesty_rejects_lyric_text_key():
    boundary = HonestyBoundary()
    payload = {"song": "Ripple", "lyric_text": "If my words did glow..."}
    violations = boundary.check_raw_seed(payload)
    assert any("forbidden lyric-text key" in v for v in violations)


def test_honesty_rejects_audio_feature_key():
    boundary = HonestyBoundary()
    payload = [{"audio_feature_tempo": 120.0}]
    violations = boundary.check_raw_seed(payload)
    assert any("forbidden prefix" in v for v in violations)


def test_honesty_rejects_positive_review_without_source():
    # The Review dataclass accepts an empty source_url (content-level honesty
    # lives in HonestyBoundary, not the schema). A positive-sentiment review
    # with no source is the "we claim something good happened with no way to
    # verify it" over-claim shape the boundary must reject.
    review = Review(
        show_slug="s",
        author="a",
        sentiment=1.0,
        summary="great",
        source_url="",
        kind="fan",
    )
    comp = build_compendium(reviews=[review])
    boundary = HonestyBoundary()
    violations = boundary.check_compendium(comp)
    assert any("positive sentiment" in v for v in violations)


def test_honesty_rejects_recording_id_url_mismatch():
    rec = Recording(
        archive_id="gd1977-05-08.sbd.miller.110987.flac16",
        show_slug="x",
        source_type="SBD",
        url="https://example.com/not-archive",
    )
    comp = build_compendium(recordings=[rec])
    boundary = HonestyBoundary()
    violations = boundary.check_compendium(comp)
    assert any("archive.org" in v for v in violations)


def test_assert_honesty_raises_on_violation():
    rec = Recording(
        archive_id="gd1977-05-08.x",
        show_slug="x",
        source_type="SBD",
        url="https://nope.com",
    )
    comp = build_compendium(recordings=[rec])
    with pytest.raises(HonestyViolation):
        assert_honesty(comp)


def test_assert_honesty_passes_clean():
    comp = build_compendium()
    assert_honesty(comp)  # no violations on empty compendium


def test_forbidden_lyric_keys_are_lowercased():
    for k in FORBIDDEN_LYRIC_KEYS:
        assert k == k.lower()


def test_seed_validation_passes_on_shipped_seed():
    assert_valid()  # raises on failure


def test_seed_validation_rejects_missing_required(tmp_path):
    (tmp_path / "shows.json").write_text("[]", encoding="utf-8")
    violations = validate_seed(seed_dir=tmp_path)
    # All other contract files are missing.
    assert any("missing" in v for v in violations)


def test_seed_validation_rejects_extra_keys(tmp_path):
    bad = '[{"slug": "x", "name": "X", "city": "Y", "state": "Z", "extra": 1}]'
    (tmp_path / "venues.json").write_text(bad, encoding="utf-8")
    violations = validate_seed(seed_dir=tmp_path)
    assert any("unexpected key" in v for v in violations)


def test_seed_validation_rejects_non_array(tmp_path):
    (tmp_path / "venues.json").write_text('{"a": 1}', encoding="utf-8")
    violations = validate_seed(seed_dir=tmp_path)
    assert any("top-level must be an array" in v for v in violations)


def test_seed_validation_invalid_json(tmp_path):
    (tmp_path / "venues.json").write_text("not json", encoding="utf-8")
    violations = validate_seed(seed_dir=tmp_path)
    assert any("invalid JSON" in v for v in violations)


def test_seed_validation_error_message():
    err = SeedValidationError(("a", "b"))
    assert "seed validation failed" in str(err)


def test_opposite_category_swaps_arrows(compendium):
    cat = build_show_category(compendium)
    op = opposite(cat)
    assert op.objects == cat.objects
    # Every arrow appears with swapped direction.
    for a, b in cat.arrows:
        assert (b, a) in op.arrows


def test_yoneda_representable_at(compendium):
    slugs = tuple(s.slug for s in compendium.shows[:5])
    pre = representable_at(slugs[0], slugs)
    assert len(pre[slugs[0]]) == 1
    for other in slugs[1:]:
        assert pre[other] == frozenset()


def test_yoneda_bijection_count(compendium):
    cnt = yoneda_bijection_count(compendium)
    assert cnt == len(compendium.shows)


def test_yoneda_embed_has_one_presheaf_per_show(compendium):
    embed = yoneda_embed(compendium)
    assert len(embed) == len(compendium.shows)
