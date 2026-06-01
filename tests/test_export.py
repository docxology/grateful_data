"""Tests for the complete raw-data export."""

from __future__ import annotations

import csv
import json

from src.export import export_all

EXPECTED_ENTITIES = (
    "shows",
    "performances",
    "songs",
    "venues",
    "personnel",
    "recordings",
    "releases",
    "citations",
    "reviews",
    "lyric_pointers",
    "venue_geo",
    "segues",
)

# Pinned baseline cardinalities (ISA Constraints).
PINNED = {
    "shows": 83,
    "performances": 341,
    "songs": 88,
    "venues": 25,
    "personnel": 14,
    "recordings": 6,
    "releases": 30,
    "citations": 26,
    "reviews": 12,
    "lyric_pointers": 25,
    "venue_geo": 25,
}


def _csv_rows(path):
    with path.open(encoding="utf-8") as fh:
        return list(csv.reader(fh))


def test_export_writes_all_entities(tmp_path, compendium):
    written = export_all(compendium, tmp_path)
    for entity in EXPECTED_ENTITIES:
        assert entity in written
        assert (tmp_path / f"{entity}.csv").exists()
    assert (tmp_path / "compendium_full.json").exists()


def test_csv_row_counts_match_cardinalities(tmp_path, compendium):
    export_all(compendium, tmp_path)
    for entity, n in PINNED.items():
        rows = _csv_rows(tmp_path / f"{entity}.csv")
        assert len(rows) - 1 == n, f"{entity}: {len(rows) - 1} data rows != pinned {n}"


def test_full_json_contains_all_records(tmp_path, compendium):
    export_all(compendium, tmp_path)
    payload = json.loads(
        (tmp_path / "compendium_full.json").read_text(encoding="utf-8")
    )
    for entity, n in PINNED.items():
        assert payload["counts"][entity] == n
        assert len(payload["records"][entity]) == n


def test_export_introduces_no_forbidden_keys(tmp_path, compendium):
    """Honesty: the export must not invent lyric-text or audio-feature fields."""
    export_all(compendium, tmp_path)
    blob = (tmp_path / "compendium_full.json").read_text(encoding="utf-8").lower()
    for forbidden in ("lyric_text", "audio_feature_", '"lyrics"', "verse", "chorus"):
        assert forbidden not in blob


def test_csv_round_trips_with_special_characters(tmp_path, compendium):
    """Dead song titles have apostrophes/commas/parens — CSV must round-trip them.

    Re-reading songs.csv with the csv module must recover exactly the titles
    written, proving the export quotes special characters correctly.
    """
    export_all(compendium, tmp_path)
    with (tmp_path / "songs.csv").open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    titles_from_csv = {r["title"] for r in rows}
    titles_from_comp = {s.title for s in compendium.songs}
    assert titles_from_csv == titles_from_comp
    # at least one title with a comma or apostrophe exists and survived intact
    tricky = [t for t in titles_from_comp if ("," in t or "'" in t or "(" in t)]
    for t in tricky:
        assert t in titles_from_csv


def test_full_json_round_trips_every_field_not_just_titles(tmp_path, compendium):
    """VALUE round-trip (RedTeam iter-8 CE-4): re-read compendium_full.json and
    compare field-by-field against the live compendium for the high-risk
    entities — venues (city/state/country), performances (set/position/segue),
    citations (url/kind), recordings (show_slug/url). The prior suite only
    value-checked song titles, so a corrupted venue city or recording url
    exported clean and passed."""
    export_all(compendium, tmp_path)
    payload = json.loads(
        (tmp_path / "compendium_full.json").read_text(encoding="utf-8")
    )
    rec = payload["records"]

    venues_json = {
        v["slug"]: (v["city"], v["state_or_region"], v["country"])
        for v in rec["venues"]
    }
    venues_comp = {
        v.slug: (v.city, v.state_or_region, v.country) for v in compendium.venues
    }
    assert venues_json == venues_comp

    perf_json = {
        (p["show_slug"], p["song_slug"], p["set_number"], p["position"], p["segue_into"])
        for p in rec["performances"]
    }
    perf_comp = {
        (p.show_slug, p.song_slug, p.set_number, p.position, p.segue_into)
        for p in compendium.performances
    }
    assert perf_json == perf_comp

    cit_json = {c["key"]: (c["url"], c["kind"]) for c in rec["citations"]}
    cit_comp = {c.key: (c.url, c.kind) for c in compendium.citations}
    assert cit_json == cit_comp

    recs_json = {
        r["archive_id"]: (r["show_slug"], r["url"]) for r in rec["recordings"]
    }
    recs_comp = {
        r.archive_id: (r.show_slug, r.url) for r in compendium.recordings
    }
    assert recs_json == recs_comp


def test_export_is_deterministic(tmp_path, compendium):
    a = tmp_path / "a"
    b = tmp_path / "b"
    export_all(compendium, a)
    export_all(compendium, b)
    for entity in EXPECTED_ENTITIES:
        assert (a / f"{entity}.csv").read_bytes() == (b / f"{entity}.csv").read_bytes()
    assert (a / "compendium_full.json").read_bytes() == (
        b / "compendium_full.json"
    ).read_bytes()
