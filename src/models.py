"""Canonical schema for the Grateful Dead compendium.

Every entity here is a frozen dataclass with explicit validation in
``__post_init__``. The schema is the contract every source parser must satisfy
and every analysis module consumes. Keeping the schema small and total makes
the category-theoretic constructions in ``cattheory/`` honest: objects of the
categories ARE instances of these dataclasses, not paraphrases of them.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date as _date
from typing import Iterable

_VALID_ROLE = {
    "lead guitar",
    "rhythm guitar",
    "bass",
    "drums",
    "percussion",
    "keyboards",
    "harmonica",
    "vocals",
    "lyricist",
}


def normalize_slug(text: str) -> str:
    """Lower-case ASCII slug; deterministic across runs."""
    normalized = unicodedata.normalize("NFKD", text)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    return re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")


def _slugify(text: str) -> str:
    """Alias for :func:`normalize_slug` (internal callers)."""
    return normalize_slug(text)


def canonical_song_id(title: str) -> str:
    """Canonical song ID is the slug of the title.

    Aliases (handled in ``integration.reconcile``) collapse to the same slug.
    """
    if not title or not title.strip():
        raise ValueError("song title must be non-empty")
    return _slugify(title)


def canonical_show_id(show_date: _date, venue_slug: str, *, show_index: int = 0) -> str:
    """Canonical show ID is ``YYYY-MM-DD@<venue-slug>`` (``#N`` when same-day duplicates)."""
    if not venue_slug:
        raise ValueError("venue slug must be non-empty")
    base = f"{show_date.isoformat()}@{venue_slug}"
    if show_index:
        return f"{base}#{show_index}"
    return base


@dataclass(frozen=True)
class Venue:
    """A physical performance location."""

    slug: str
    name: str
    city: str
    state_or_region: str
    country: str = "USA"

    def __post_init__(self) -> None:
        if not self.slug:
            raise ValueError("Venue.slug must be non-empty")
        if not self.name:
            raise ValueError("Venue.name must be non-empty")


@dataclass(frozen=True)
class Person:
    """A musician, lyricist, or production role.

    ``intervals`` is a sequence of (start, end, role) tuples. ``end`` may be
    ``None`` for ongoing or unknown end-dates. Multiple intervals support roles
    like Mickey Hart, who was in the band 1967-1971, away, and back in 1974+.
    """

    slug: str
    full_name: str
    intervals: tuple[tuple[_date, _date | None, str], ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        if not self.slug:
            raise ValueError("Person.slug must be non-empty")
        for start, end, role in self.intervals:
            if end is not None and end < start:
                raise ValueError(f"Person.intervals: end {end} precedes start {start}")
            if role not in _VALID_ROLE:
                raise ValueError(f"Person.intervals: unknown role {role!r}")

    def active_on(self, day: _date) -> bool:
        """True iff at least one interval covers ``day``."""
        for start, end, _role in self.intervals:
            if start <= day and (end is None or day <= end):
                return True
        return False


@dataclass(frozen=True)
class Song:
    """A composition with composer/lyricist attribution."""

    slug: str
    title: str
    composers: tuple[str, ...] = field(default_factory=tuple)
    lyricists: tuple[str, ...] = field(default_factory=tuple)
    first_performed: _date | None = None
    last_performed: _date | None = None
    aliases: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.slug:
            raise ValueError("Song.slug must be non-empty")
        if not self.title:
            raise ValueError("Song.title must be non-empty")
        if (
            self.first_performed
            and self.last_performed
            and self.last_performed < self.first_performed
        ):
            raise ValueError("Song.last_performed precedes Song.first_performed")


@dataclass(frozen=True)
class Show:
    """A single performance event at a venue on a date."""

    slug: str
    date: _date
    venue_slug: str
    tour: str | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.slug:
            raise ValueError("Show.slug must be non-empty")
        if not self.venue_slug:
            raise ValueError("Show.venue_slug must be non-empty")
        show_index = 0
        if "#" in self.slug:
            _base, idx = self.slug.rsplit("#", 1)
            if idx.isdigit():
                show_index = int(idx)
        expected = canonical_show_id(self.date, self.venue_slug, show_index=show_index)
        if self.slug != expected:
            raise ValueError(
                f"Show.slug {self.slug!r} does not match canonical {expected!r}"
            )


@dataclass(frozen=True)
class Performance:
    """One song instance inside one show.

    ``Performance`` is the central primitive — it's the span apex linking
    ``Show`` and ``Song`` in the categorical interpretation.
    """

    show_slug: str
    song_slug: str
    set_number: int
    position: int
    segue_into: str | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if self.set_number < 1:
            raise ValueError("Performance.set_number must be >= 1")
        if self.position < 1:
            raise ValueError("Performance.position must be >= 1")


@dataclass(frozen=True)
class Recording:
    """A recorded artifact of a show (or part of one)."""

    archive_id: str
    show_slug: str
    source_type: str  # SBD | AUD | MTX | FM | UNKNOWN
    url: str = ""

    _VALID_SOURCES = frozenset({"SBD", "AUD", "MTX", "FM", "UNKNOWN"})

    def __post_init__(self) -> None:
        if not self.archive_id:
            raise ValueError("Recording.archive_id must be non-empty")
        if self.source_type not in self._VALID_SOURCES:
            raise ValueError(
                f"Recording.source_type {self.source_type!r} not in {sorted(self._VALID_SOURCES)}"
            )


@dataclass(frozen=True)
class Release:
    """An official album or box-set release."""

    slug: str
    title: str
    release_date: _date
    kind: str  # studio | live | archival | box-set
    track_show_slugs: tuple[str, ...] = field(default_factory=tuple)

    _VALID_KINDS = frozenset({"studio", "live", "archival", "box-set"})

    def __post_init__(self) -> None:
        if self.kind not in self._VALID_KINDS:
            raise ValueError(
                f"Release.kind {self.kind!r} not in {sorted(self._VALID_KINDS)}"
            )


@dataclass(frozen=True)
class Citation:
    """A bibliographic source cited in the compendium."""

    key: str
    title: str
    url: str
    kind: str  # web | github | book | article | database | api | corpus
    year: int | None = None

    _VALID_KINDS = frozenset(
        {"web", "github", "book", "article", "database", "api", "corpus"}
    )

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("Citation.key must be non-empty")
        if not self.url:
            raise ValueError("Citation.url must be non-empty")
        if self.kind not in self._VALID_KINDS:
            raise ValueError(
                f"Citation.kind {self.kind!r} not in {sorted(self._VALID_KINDS)}"
            )


@dataclass(frozen=True)
class LyricPointer:
    """A pointer to where a song's lyric text can be found, with metadata.

    We do **not** bundle lyric text (copyright). The pointer carries the
    canonical lyricist, the source URL (typically Alex Allan's whitegum.com
    songfile entries), and a short tuple of theme labels for downstream
    semantic analysis.

    Missing or non-http(s) ``source_url`` values are intentionally accepted
    by the dataclass so the runtime
    :class:`~grateful_data.honesty.HonestyBoundary` can catch them at the
    boundary — content-level honesty rules live there, not in the schema.
    """

    song_slug: str
    lyricist: str
    source_url: str
    themes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.song_slug:
            raise ValueError("LyricPointer.song_slug must be non-empty")
        if self.source_url and not self.source_url.startswith(("http://", "https://")):
            raise ValueError("LyricPointer.source_url must be empty or an http(s) URL")


@dataclass(frozen=True)
class Review:
    """A pointer to a per-show review / commentary record.

    ``sentiment`` is a normalized score in ``[0, 1]`` derived externally;
    ``kind`` distinguishes fan, press, official, or documentary sources.
    """

    show_slug: str
    author: str
    sentiment: float
    summary: str
    source_url: str
    kind: str  # fan | press | official | official-release | documentary

    _VALID_KINDS = frozenset(
        {"fan", "press", "official", "official-release", "documentary"}
    )

    def __post_init__(self) -> None:
        if not (0.0 <= self.sentiment <= 1.0):
            raise ValueError(f"Review.sentiment {self.sentiment} must lie in [0, 1]")
        if self.kind not in self._VALID_KINDS:
            raise ValueError(
                f"Review.kind {self.kind!r} not in {sorted(self._VALID_KINDS)}"
            )
        if not self.show_slug:
            raise ValueError("Review.show_slug must be non-empty")


@dataclass(frozen=True)
class Lineup:
    """A band lineup on a specific date — the set of active people."""

    on_date: _date
    member_slugs: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(set(self.member_slugs)) != len(self.member_slugs):
            raise ValueError("Lineup.member_slugs must be unique")

    @property
    def fingerprint(self) -> str:
        """Stable hash over the sorted member set — equality of lineups."""
        joined = "|".join(sorted(self.member_slugs))
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def lineup_on(people: Iterable[Person], day: _date) -> Lineup:
    """Compute the lineup active on ``day`` from a population of ``Person``."""
    actives = tuple(sorted(p.slug for p in people if p.active_on(day)))
    return Lineup(on_date=day, member_slugs=actives)
