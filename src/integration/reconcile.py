"""Reconcile entities from multiple sources into one ``Compendium``.

The merge rule is simple and total:

* ``Show`` joins on ``slug`` (which is ``date@venue``).
* ``Venue`` joins on ``slug``; conflicts on name/city are resolved by
  preferring the first non-empty value (sources_priority order).
* ``Song`` joins on ``slug`` (canonical from the title); composer/lyricist
  tuples are unioned across sources; ``first_performed`` / ``last_performed``
  take the min/max across sources.
* ``Person`` joins on ``slug``; intervals are unioned.
* ``Performance`` joins on (show_slug, song_slug, set_number, position).
* ``Recording`` joins on ``archive_id``.
* ``Release`` joins on ``slug``.

This is a small enough merge that we can express it directly without a heavy
ETL framework. Determinism — the merged compendium is byte-identical across
runs given the same inputs — is enforced by sorted iteration on the slug
keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as _date
from typing import Iterable

from ..models import (
    Citation,
    LyricPointer,
    Performance,
    Person,
    Recording,
    Release,
    Review,
    Show,
    Song,
    Venue,
    lineup_on,
)
from .aliases import canonicalize_alias


@dataclass(frozen=True)
class Compendium:
    """A reconciled, immutable snapshot of the compendium."""

    shows: tuple[Show, ...] = field(default_factory=tuple)
    venues: tuple[Venue, ...] = field(default_factory=tuple)
    songs: tuple[Song, ...] = field(default_factory=tuple)
    people: tuple[Person, ...] = field(default_factory=tuple)
    performances: tuple[Performance, ...] = field(default_factory=tuple)
    recordings: tuple[Recording, ...] = field(default_factory=tuple)
    releases: tuple[Release, ...] = field(default_factory=tuple)
    citations: tuple[Citation, ...] = field(default_factory=tuple)
    lyric_pointers: tuple[LyricPointer, ...] = field(default_factory=tuple)
    reviews: tuple[Review, ...] = field(default_factory=tuple)

    @property
    def show_by_slug(self) -> dict[str, Show]:
        return {s.slug: s for s in self.shows}

    @property
    def song_by_slug(self) -> dict[str, Song]:
        return {s.slug: s for s in self.songs}

    @property
    def venue_by_slug(self) -> dict[str, Venue]:
        return {v.slug: v for v in self.venues}

    @property
    def person_by_slug(self) -> dict[str, Person]:
        return {p.slug: p for p in self.people}

    def lineup_on(self, day: _date):
        return lineup_on(self.people, day)


def _merge_song(a: Song, b: Song) -> Song:
    composers = tuple(sorted(set(a.composers) | set(b.composers)))
    lyricists = tuple(sorted(set(a.lyricists) | set(b.lyricists)))
    aliases = tuple(sorted(set(a.aliases) | set(b.aliases)))
    first = a.first_performed or b.first_performed
    if a.first_performed and b.first_performed:
        first = min(a.first_performed, b.first_performed)
    last = a.last_performed or b.last_performed
    if a.last_performed and b.last_performed:
        last = max(a.last_performed, b.last_performed)
    return Song(
        slug=a.slug,
        title=a.title,
        composers=composers,
        lyricists=lyricists,
        first_performed=first,
        last_performed=last,
        aliases=aliases,
    )


def _merge_venue(a: Venue, b: Venue) -> Venue:
    return Venue(
        slug=a.slug,
        name=a.name or b.name,
        city=a.city or b.city,
        state_or_region=a.state_or_region or b.state_or_region,
        country=a.country or b.country,
    )


def _merge_person(a: Person, b: Person) -> Person:
    merged_intervals = tuple(
        sorted(set(a.intervals) | set(b.intervals), key=lambda t: (t[0], t[2]))
    )
    return Person(
        slug=a.slug,
        full_name=a.full_name or b.full_name,
        intervals=merged_intervals,
    )


def build_compendium(
    *,
    shows: Iterable[Show] = (),
    venues: Iterable[Venue] = (),
    songs: Iterable[Song] = (),
    people: Iterable[Person] = (),
    performances: Iterable[Performance] = (),
    recordings: Iterable[Recording] = (),
    releases: Iterable[Release] = (),
    citations: Iterable[Citation] = (),
    lyric_pointers: Iterable[LyricPointer] = (),
    reviews: Iterable[Review] = (),
) -> Compendium:
    """Build a reconciled, sorted compendium from heterogeneous source streams."""
    show_map: dict[str, Show] = {}
    for show in shows:
        show_map[show.slug] = show  # later sources overwrite — Show is identity-only
    venue_map: dict[str, Venue] = {}
    for v in venues:
        venue_map[v.slug] = (
            _merge_venue(venue_map[v.slug], v) if v.slug in venue_map else v
        )
    song_map: dict[str, Song] = {}
    for song in songs:
        canonical_slug = canonicalize_alias(song.slug)
        if canonical_slug != song.slug:
            # Carry the alias forward so downstream code can find the original.
            song = Song(
                slug=canonical_slug,
                title=song.title,
                composers=song.composers,
                lyricists=song.lyricists,
                first_performed=song.first_performed,
                last_performed=song.last_performed,
                aliases=tuple(sorted(set(song.aliases) | {song.slug, song.title})),
            )
        song_map[song.slug] = (
            _merge_song(song_map[song.slug], song) if song.slug in song_map else song
        )
    person_map: dict[str, Person] = {}
    for person in people:
        person_map[person.slug] = (
            _merge_person(person_map[person.slug], person)
            if person.slug in person_map
            else person
        )
    # Apply alias resolution to performance song slugs too.
    perf_set: set[Performance] = set()
    for perf in performances:
        canonical = canonicalize_alias(perf.song_slug)
        if canonical != perf.song_slug:
            perf = Performance(
                show_slug=perf.show_slug,
                song_slug=canonical,
                set_number=perf.set_number,
                position=perf.position,
                segue_into=canonicalize_alias(perf.segue_into)
                if perf.segue_into
                else None,
                notes=perf.notes,
            )
        perf_set.add(perf)
    recording_map: dict[str, Recording] = {r.archive_id: r for r in recordings}
    release_map: dict[str, Release] = {r.slug: r for r in releases}
    citation_map: dict[str, Citation] = {c.key: c for c in citations}

    lyric_map: dict[str, LyricPointer] = {}
    for lp in lyric_pointers:
        canonical = canonicalize_alias(lp.song_slug)
        if canonical != lp.song_slug:
            lp = LyricPointer(
                song_slug=canonical,
                lyricist=lp.lyricist,
                source_url=lp.source_url,
                themes=lp.themes,
            )
        lyric_map[lp.song_slug] = lp
    review_list: list[Review] = list(reviews)
    return Compendium(
        shows=tuple(sorted(show_map.values(), key=lambda s: s.slug)),
        venues=tuple(sorted(venue_map.values(), key=lambda v: v.slug)),
        songs=tuple(sorted(song_map.values(), key=lambda s: s.slug)),
        people=tuple(sorted(person_map.values(), key=lambda p: p.slug)),
        performances=tuple(
            sorted(perf_set, key=lambda p: (p.show_slug, p.set_number, p.position))
        ),
        recordings=tuple(sorted(recording_map.values(), key=lambda r: r.archive_id)),
        releases=tuple(sorted(release_map.values(), key=lambda r: r.slug)),
        citations=tuple(sorted(citation_map.values(), key=lambda c: c.key)),
        lyric_pointers=tuple(sorted(lyric_map.values(), key=lambda lp: lp.song_slug)),
        reviews=tuple(sorted(review_list, key=lambda r: (r.show_slug, r.author))),
    )
