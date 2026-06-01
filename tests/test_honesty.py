"""Tests for the runtime honesty boundary."""

from __future__ import annotations

import json
import shutil

import pytest

from src.honesty import HonestyBoundary, HonestyViolation
from src.integration.reconcile import Compendium
from src.models import Citation, Recording, Review
from src.seed import load_seed_compendium

SEED_DIR = (
    __import__("pathlib").Path(__file__).resolve().parent.parent / "data" / "seed"
)


def test_honesty_boundary_passes_on_bundled_seed(compendium):
    boundary = HonestyBoundary()
    assert boundary.check_compendium(compendium) == ()


def test_forbidden_lyric_key_in_raw_payload():
    boundary = HonestyBoundary()
    payload = {"song_slug": "dark_star", "lyrics": "forbidden text"}
    violations = boundary.check_raw_seed(payload)
    assert any("forbidden lyric-text key" in v for v in violations)


def test_forbidden_audio_feature_prefix_in_raw_payload():
    boundary = HonestyBoundary()
    payload = {"audio_feature_mfcc": [1.0, 2.0]}
    violations = boundary.check_raw_seed(payload)
    assert any("forbidden prefix" in v for v in violations)


def test_review_positive_sentiment_without_source_url():
    boundary = HonestyBoundary()
    comp = Compendium(
        shows=(),
        venues=(),
        songs=(),
        people=(),
        performances=(),
        recordings=(),
        releases=(),
        citations=(),
        lyric_pointers=(),
        reviews=(
            Review(
                show_slug="1977-05-08@barton_hall_ithaca",
                author="anon",
                sentiment=0.8,
                summary="great show",
                source_url="",
                kind="fan",
            ),
        ),
    )
    violations = boundary.check_compendium(comp)
    assert any("positive sentiment" in v and "no source_url" in v for v in violations)


def test_citation_non_http_url():
    boundary = HonestyBoundary()
    comp = Compendium(
        shows=(),
        venues=(),
        songs=(),
        people=(),
        performances=(),
        recordings=(),
        releases=(),
        citations=(
            Citation(key="bad", title="Bad", url="ftp://example.com", kind="web"),
        ),
        lyric_pointers=(),
        reviews=(),
    )
    violations = boundary.check_compendium(comp)
    assert any("citation 'bad'" in v for v in violations)


def test_recording_gd_prefix_without_archive_url():
    boundary = HonestyBoundary()
    comp = Compendium(
        shows=(),
        venues=(),
        songs=(),
        people=(),
        performances=(),
        recordings=(
            Recording(
                archive_id="gd1977-05-08.sbd",
                show_slug="1977-05-08@barton_hall_ithaca",
                source_type="SBD",
                url="https://example.com/not-archive",
            ),
        ),
        releases=(),
        citations=(),
        lyric_pointers=(),
        reviews=(),
    )
    violations = boundary.check_compendium(comp)
    assert any("archive.org" in v for v in violations)


def test_load_seed_raises_on_forbidden_raw_key(tmp_path):
    shutil.copytree(SEED_DIR, tmp_path / "seed")
    songs_path = tmp_path / "seed" / "songs.json"
    songs = json.loads(songs_path.read_text(encoding="utf-8"))
    songs[0]["lyrics"] = "bundled lyric text"
    songs_path.write_text(json.dumps(songs), encoding="utf-8")
    with pytest.raises(HonestyViolation):
        load_seed_compendium(tmp_path / "seed")
