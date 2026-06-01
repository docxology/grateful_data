"""Merge heterogeneous source streams into one reconciled compendium."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..honesty import HonestyBoundary, HonestyViolation
from ..integration.reconcile import Compendium, build_compendium
from ..models import LyricPointer, Person, Recording, Song, normalize_slug
from ..sources import gdshowsdb
from ..sources.alex_allan import parse as parse_song_record
from ..sources.dead_net import parse as parse_person_record
from ..sources.internet_archive import date_from_archive_id, parse as parse_recording
from ..sources.seed_bundle import (
    parse_citation_record,
    parse_lyric_pointer_record,
    parse_review_record,
)
from ..sources.wikipedia import parse_release as parse_release_record
from .fetch_setlistfm import fetch_setlistfm_shows, parse_setlistfm_batch
from .remap_curated_refs import remap_reviews_and_recordings


@dataclass
class MergeInputs:
    gdshows_dump: dict[str, list[dict[str, Any]]] | None = None
    curated_seed_dir: Path | None = None
    online: bool = False
    ia_max_rows: int = 500
    setlistfm_max_pages: int = 5
    skip_cmu: bool = False
    skip_whitegum: bool = False
    skip_dead_net: bool = False
    skip_wikipedia: bool = False
    skip_maximinus: bool = False
    skip_bibliography: bool = False
    skip_cmu_lyrics: bool = False
    skip_truckin: bool = False
    skip_dead_net_songs: bool = False
    skip_gratefulstats: bool = False


@dataclass
class MergeReport:
    sources_used: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    entity_counts: dict[str, int] = field(default_factory=dict)
    ingest_stats: dict[str, int] = field(default_factory=dict)


def _read_json_list(path: Path) -> list[Any]:
    with path.open("r", encoding="utf-8") as fh:
        data: list[Any] = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"{path.name}: expected top-level array")
    return data


def _load_curated_layers(seed_dir: Path) -> dict[str, list[Any]]:
    layers: dict[str, list[Any]] = {}
    for name in (
        "personnel.json",
        "citations.json",
        "lyric_pointers.json",
        "reviews.json",
        "releases.json",
        "songs.json",
    ):
        path = seed_dir / name
        if path.exists():
            layers[name] = _read_json_list(path)
    return layers


def _person_name_key(person: Person) -> str:
    return normalize_slug(person.full_name)


def _merge_people(primary: list[Person], extra: list[Person]) -> None:
    """Append people from secondary sources without duplicate slugs or names."""
    known_slugs = {p.slug for p in primary}
    known_names = {_person_name_key(p) for p in primary}
    for person in extra:
        name_key = _person_name_key(person)
        if person.slug in known_slugs or name_key in known_names:
            continue
        primary.append(person)
        known_slugs.add(person.slug)
        known_names.add(name_key)


def _merge_gap_shows(
    primary_shows: list,
    primary_perfs: list,
    extra_shows: list,
    extra_perfs: list,
) -> None:
    """Append CMU/Setlist.fm rows only for shows missing performances in the primary layer."""
    show_slugs = {s.slug for s in primary_shows}
    shows_with_perf = {p.show_slug for p in primary_perfs}
    for show in extra_shows:
        if show.slug not in show_slugs:
            primary_shows.append(show)
            show_slugs.add(show.slug)
    for perf in extra_perfs:
        if perf.show_slug not in shows_with_perf:
            primary_perfs.append(perf)
            shows_with_perf.add(perf.show_slug)


def merge_archival(inputs: MergeInputs) -> tuple[Compendium, MergeReport]:
    """Build the archival compendium from gdshowsdb + curated seed layers."""
    report = MergeReport()
    shows: list = []
    venues: list = []
    songs: list = []
    perfs: list = []
    people: list = []
    recordings: list = []
    releases: list = []
    citations: list = []
    lyric_pointers: list[LyricPointer] = []
    reviews: list = []

    if inputs.gdshows_dump:
        gd_shows, gd_venues, gd_songs, gd_perfs = gdshowsdb.parse(inputs.gdshows_dump)
        shows.extend(gd_shows)
        venues.extend(gd_venues)
        songs.extend(gd_songs)
        perfs.extend(gd_perfs)
        report.sources_used.append("gdshowsdb")

    curated_dir = inputs.curated_seed_dir
    curated_has_personnel = bool(
        curated_dir and (curated_dir / "personnel.json").is_file()
    )
    if curated_dir and curated_dir.is_dir():
        layers = _load_curated_layers(curated_dir)
        if "personnel.json" in layers:
            people.extend(parse_person_record(r) for r in layers["personnel.json"])
        if "songs.json" in layers:
            songs.extend(parse_song_record(r) for r in layers["songs.json"])
        if "citations.json" in layers:
            citations.extend(parse_citation_record(c) for c in layers["citations.json"])
        if "lyric_pointers.json" in layers:
            lyric_pointers.extend(
                parse_lyric_pointer_record(r) for r in layers["lyric_pointers.json"]
            )
        if "reviews.json" in layers:
            reviews.extend(parse_review_record(r) for r in layers["reviews.json"])
        if "releases.json" in layers:
            releases.extend(parse_release_record(r) for r in layers["releases.json"])
        report.sources_used.append("curated_seed")

    curated_lyric_rows: list[dict[str, Any]] = []
    if curated_dir and curated_dir.is_dir():
        lp_path = curated_dir / "lyric_pointers.json"
        if lp_path.is_file():
            curated_lyric_rows = _read_json_list(lp_path)

    if not inputs.skip_bibliography:
        from .fetch_bibliography import load_all_project_citations

        bib_citations = load_all_project_citations()
        existing_urls = {c.url for c in citations}
        added = 0
        for citation in bib_citations:
            if citation.url not in existing_urls:
                citations.append(citation)
                existing_urls.add(citation.url)
                added += 1
        if added:
            report.sources_used.append("bibliography_combined")

    if inputs.online and not inputs.skip_cmu:
        try:
            from .fetch_cmu import fetch_cmu_shows

            cmu_shows, cmu_venues, cmu_songs, cmu_perfs, cmu_source = fetch_cmu_shows(
                online=True
            )
            venue_slugs = {v.slug for v in venues}
            for v in cmu_venues:
                if v.slug not in venue_slugs:
                    venues.append(v)
                    venue_slugs.add(v.slug)
            song_slugs = {s.slug for s in songs}
            for s in cmu_songs:
                if s.slug not in song_slugs:
                    songs.append(s)
                    song_slugs.add(s.slug)
            _merge_gap_shows(shows, perfs, cmu_shows, cmu_perfs)
            report.sources_used.append(f"cmu_leone_setlists ({cmu_source})")
        except OSError as exc:
            report.skipped.append(f"cmu_leone_setlists: {exc}")

    if inputs.online and not inputs.skip_whitegum:
        try:
            from .fetch_alex_allan import fetch_alex_allan_songs

            aa_songs, aa_pointers = fetch_alex_allan_songs(
                online=True, seed_dir=curated_dir
            )
            song_map: dict[str, Song] = {s.slug: s for s in songs}
            for song in aa_songs:
                if song.slug in song_map:
                    song_map[song.slug] = song_map[song.slug]  # reconcile merges later
                else:
                    songs.append(song)
            existing_lp = {(lp.song_slug, lp.source_url) for lp in lyric_pointers}
            for lp in aa_pointers:
                key = (lp.song_slug, lp.source_url)
                if key not in existing_lp:
                    lyric_pointers.append(lp)
                    existing_lp.add(key)
            report.sources_used.append("whitegum_alex_allan")
        except OSError as exc:
            report.skipped.append(f"whitegum_alex_allan: {exc}")

    if inputs.online and not inputs.skip_cmu_lyrics:
        try:
            from .fetch_cmu_lyrics import fetch_cmu_lyric_pointers

            cmu_pointers, cmu_lyrics_source = fetch_cmu_lyric_pointers(online=True)
            existing_lp = {(lp.song_slug, lp.source_url) for lp in lyric_pointers}
            for lp in cmu_pointers:
                key = (lp.song_slug, lp.source_url)
                if key not in existing_lp:
                    lyric_pointers.append(lp)
                    existing_lp.add(key)
            if cmu_pointers:
                report.sources_used.append(f"cmu_leone_lyrics ({cmu_lyrics_source})")
        except OSError as exc:
            report.skipped.append(f"cmu_leone_lyrics: {exc}")

    if inputs.online and not inputs.skip_maximinus:
        try:
            from .fetch_maximinus_reviews import (
                attach_reviews_to_shows,
                fetch_maximinus_reviews,
            )

            by_date: dict[str, list] = defaultdict(list)
            for show in shows:
                by_date[show.date.isoformat()].append(show)
            maximinus = attach_reviews_to_shows(
                fetch_maximinus_reviews(online=True), by_date
            )
            if maximinus:
                reviews.extend(maximinus)
                report.sources_used.append("maximinus_reviews")
        except OSError as exc:
            report.skipped.append(f"maximinus_reviews: {exc}")

    if inputs.online and not inputs.skip_truckin:
        try:
            from .fetch_truckin_db import fetch_truckin_shows

            perf_before = {p.show_slug for p in perfs}
            tr_shows, tr_venues, tr_songs, tr_perfs, tr_source = fetch_truckin_shows(
                online=True
            )
            venue_slugs = {v.slug for v in venues}
            for v in tr_venues:
                if v.slug not in venue_slugs:
                    venues.append(v)
                    venue_slugs.add(v.slug)
            song_slugs = {s.slug for s in songs}
            for s in tr_songs:
                if s.slug not in song_slugs:
                    songs.append(s)
                    song_slugs.add(s.slug)
            _merge_gap_shows(shows, perfs, tr_shows, tr_perfs)
            gap_added = len({s.slug for s in tr_shows} - perf_before)
            report.ingest_stats["truckin_gap_shows"] = gap_added
            report.sources_used.append(tr_source)
        except OSError as exc:
            report.skipped.append(f"truckin_through_time: {exc}")

    if inputs.online and not inputs.skip_dead_net_songs:
        try:
            from .fetch_dead_net_songs import fetch_dead_net_song_pointers

            dn_pointers, dn_source = fetch_dead_net_song_pointers(online=True)
            existing_lp = {(lp.song_slug, lp.source_url) for lp in lyric_pointers}
            added = 0
            for lp in dn_pointers:
                key = (lp.song_slug, lp.source_url)
                if key not in existing_lp:
                    lyric_pointers.append(lp)
                    existing_lp.add(key)
                    added += 1
            if added:
                report.sources_used.append(f"dead_net_songs ({dn_source})")
                report.ingest_stats["dead_net_song_links"] = added
        except OSError as exc:
            report.skipped.append(f"dead_net_songs: {exc}")

    if inputs.online and not inputs.skip_gratefulstats:
        import os

        if os.environ.get("GRATEFULSTATS_API_KEY"):
            try:
                from .fetch_gratefulstats import fetch_gratefulstats_citation

                gs_citations = fetch_gratefulstats_citation(online=True)
                existing_urls = {c.url for c in citations}
                for citation in gs_citations:
                    if citation.url not in existing_urls:
                        citations.append(citation)
                        existing_urls.add(citation.url)
                report.sources_used.append("gratefulstats_api_probe")
            except OSError as exc:
                report.skipped.append(f"gratefulstats_api: {exc}")
        else:
            report.skipped.append("gratefulstats_api: GRATEFULSTATS_API_KEY not set")

    if inputs.online and not inputs.skip_dead_net and not curated_has_personnel:
        try:
            from .fetch_dead_net import fetch_dead_net_personnel

            dn_people = fetch_dead_net_personnel(online=True, seed_dir=curated_dir)
            _merge_people(people, dn_people)
            report.sources_used.append("dead_net_official")
        except OSError as exc:
            report.skipped.append(f"dead_net_official: {exc}")

    if inputs.online and not inputs.skip_wikipedia:
        try:
            from .fetch_wikipedia import (
                fetch_wikipedia_personnel,
                fetch_wikipedia_releases,
            )

            wiki_releases = fetch_wikipedia_releases(online=True)
            rel_slugs = {r.slug for r in releases}
            for rel in wiki_releases:
                if rel.slug not in rel_slugs:
                    releases.append(rel)
                    rel_slugs.add(rel.slug)
            wiki_people = (
                fetch_wikipedia_personnel(online=True)
                if not curated_has_personnel
                else []
            )
            if not curated_has_personnel:
                _merge_people(people, wiki_people)
            if wiki_releases or wiki_people:
                report.sources_used.append("wikipedia_gd")
        except OSError as exc:
            report.skipped.append(f"wikipedia_gd: {exc}")

    if inputs.online:
        try:
            from .fetch_internet_archive import fetch_lma_recordings

            ia_recs = fetch_lma_recordings(max_rows=inputs.ia_max_rows)
            recordings.extend(ia_recs)
            report.sources_used.append("internet_archive_lma")
        except OSError as exc:
            report.skipped.append(f"internet_archive_lma: {exc}")

        slf_payloads = fetch_setlistfm_shows(max_pages=inputs.setlistfm_max_pages)
        if slf_payloads:
            slf_shows, slf_venues, slf_songs, slf_perfs = parse_setlistfm_batch(
                slf_payloads
            )
            venue_slugs = {v.slug for v in venues}
            for v in slf_venues:
                if v.slug not in venue_slugs:
                    venues.append(v)
                    venue_slugs.add(v.slug)
            song_slugs = {s.slug for s in songs}
            for s in slf_songs:
                if s.slug not in song_slugs:
                    songs.append(s)
                    song_slugs.add(s.slug)
            _merge_gap_shows(shows, perfs, slf_shows, slf_perfs)
            report.sources_used.append("setlistfm_gd")
        elif not __import__("os").environ.get("SETLISTFM_API_KEY"):
            report.skipped.append("setlistfm_gd: SETLISTFM_API_KEY not set")

    if curated_dir:
        rec_path = curated_dir / "recordings.json"
        if rec_path.exists():
            for row in _read_json_list(rec_path):
                try:
                    recordings.append(parse_recording({"metadata": row}))
                except (KeyError, ValueError, TypeError):
                    continue

    rec_map: dict[str, Recording] = {}
    for rec in recordings:
        rec_map[rec.archive_id] = rec
    recordings = list(rec_map.values())

    reviews, recordings = remap_reviews_and_recordings(shows, reviews, recordings)

    from .lyric_pointer_enrich import consolidate_lyric_pointers

    performed_song_slugs = {p.song_slug for p in perfs}
    lyric_pointers, lp_stats = consolidate_lyric_pointers(
        lyric_pointers,
        songs,
        performed_song_slugs=performed_song_slugs,
        curated_rows=curated_lyric_rows or None,
        fill_dead_net=True,
    )
    report.ingest_stats.update(lp_stats)
    if lp_stats.get("overlayed"):
        report.sources_used.append("curated_lyric_overlay")
    if lp_stats.get("dead_net_added"):
        report.sources_used.append(
            f"dead_net_lyric_gaps ({lp_stats['dead_net_added']})"
        )
    if lp_stats.get("lyricists_propagated"):
        report.sources_used.append(
            f"song_lyricist_propagation ({lp_stats['lyricists_propagated']})"
        )

    show_slugs = {s.slug for s in shows}
    show_dates = {s.slug: s.date for s in shows}
    reviews = [r for r in reviews if r.show_slug in show_slugs]
    filtered_recordings: list[Recording] = []
    dropped_show = 0
    dropped_date = 0
    for rec in recordings:
        if rec.show_slug not in show_slugs:
            dropped_show += 1
            continue
        encoded = date_from_archive_id(rec.archive_id)
        if encoded is not None:
            from datetime import date as _date

            if show_dates.get(rec.show_slug) != _date.fromisoformat(encoded):
                dropped_date += 1
                continue
        filtered_recordings.append(rec)
    recordings = filtered_recordings
    report.ingest_stats["recordings_dropped_show"] = dropped_show
    report.ingest_stats["recordings_dropped_date"] = dropped_date

    comp = build_compendium(
        shows=shows,
        venues=venues,
        songs=songs,
        people=people,
        performances=perfs,
        recordings=recordings,
        releases=releases,
        citations=citations,
        lyric_pointers=lyric_pointers,
        reviews=reviews,
    )

    boundary = HonestyBoundary()
    violations = boundary.check_compendium(comp)
    if violations:
        raise HonestyViolation(violations)

    report.entity_counts = {
        "shows": len(comp.shows),
        "venues": len(comp.venues),
        "songs": len(comp.songs),
        "people": len(comp.people),
        "performances": len(comp.performances),
        "recordings": len(comp.recordings),
        "releases": len(comp.releases),
        "citations": len(comp.citations),
        "lyric_pointers": len(comp.lyric_pointers),
        "reviews": len(comp.reviews),
    }
    return comp, report
