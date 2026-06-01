"""Data-completeness audit for the compendium.

The manuscript and README assert the loaded compendium is *internally
consistent*. This module promotes that assertion from prose to a runtime
probe: :func:`audit_completeness` walks the reconciled :class:`Compendium`
and returns a structured :class:`CompletenessReport` proving — or refuting —
that every show carries full, real, resolvable data:

* every ``Show.venue_slug`` resolves to a ``Venue`` record,
* every performed song resolves to a ``Song`` record,
* every venue has geo coverage (lat/lon/region sidecar),
* every ``Review``/``Recording`` references a show that exists,
* every ``Release.track_show_slugs`` reference resolves,
* every ``Citation`` carries an http(s) URL.

Setlist completeness is handled honestly by TIER, not silently: at the
``seed`` tier every show must carry at least one ``Performance`` and an
empty setlist counts as dangling; at the ``archival`` tier the gdshowsdb
catalog legitimately lists setlist-empty shows, so those are reported as
``shows_without_performances`` (with an explicit count) and treated as
*scope*, not as a dangling reference. ``is_complete`` therefore means "zero
unresolved references on the hard relations above," NOT "every show has a
non-empty setlist" — the empty-setlist count is surfaced separately so it is
never hidden.

It deliberately reports **corpus scope honestly**: ingested show count is
compared to ``FULL_CORPUS_SHOW_ESTIMATE`` (a community literature figure, not
an ingest ceiling). Nothing here fabricates a show.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .analysis.geo import load_geo
from .integration.reconcile import Compendium
from .sources.internet_archive import date_from_archive_id

# Documented size of the full Grateful Dead *primary-performance* corpus, per
# the cited setlist databases (M. Leone / CMU, A. Allan / whitegum.com). This
# is a citation, not bundled data — used only to state curated-vs-full scope.
FULL_CORPUS_SHOW_ESTIMATE: int = 2318


@dataclass(frozen=True)
class CompletenessReport:
    """Structured, serialisable result of a completeness audit."""

    n_shows: int
    n_performances: int
    n_songs: int
    n_venues: int
    n_people: int
    date_min: str
    date_max: str
    #: Data tier this report was computed for ("seed" or "archival"). Single
    #: source of truth for tier-dependent semantics — set once at construction
    #: so dangling_total and corpus_scope can never disagree on the tier.
    tier: str = "seed"
    shows_missing_venue: tuple[str, ...] = field(default_factory=tuple)
    performed_songs_missing_record: tuple[str, ...] = field(default_factory=tuple)
    shows_without_performances: tuple[str, ...] = field(default_factory=tuple)
    venues_missing_geo: tuple[str, ...] = field(default_factory=tuple)
    reviews_dangling: tuple[str, ...] = field(default_factory=tuple)
    recordings_dangling: tuple[str, ...] = field(default_factory=tuple)
    recordings_date_mismatch: tuple[str, ...] = field(default_factory=tuple)
    releases_dangling_track_refs: tuple[str, ...] = field(default_factory=tuple)
    citations_bad_url: tuple[str, ...] = field(default_factory=tuple)
    geo_coverage_pct: float = 0.0
    # Informational coverage of optional data dimensions (not part of the hard
    # completeness claim — reported so absent dimensions are never hidden).
    n_segue_markers: int = 0
    n_shows_with_tour: int = 0
    performed_songs_without_lyric_pointer: int = 0
    songs_with_lyricist_on_pointer: int = 0
    songs_with_themes_on_pointer: int = 0
    n_recordings_dropped_show: int = 0
    n_recordings_dropped_date: int = 0
    maximinus_reviews_n: int = 0
    curated_reviews_n: int = 0

    @property
    def n_shows_without_performances(self) -> int:
        """Count of catalog shows with an empty setlist (surfaced, never hidden)."""
        return len(self.shows_without_performances)

    @property
    def dangling_total(self) -> int:
        """Unresolved references on the hard relations (tier-aware setlist rule)."""
        base = (
            len(self.shows_missing_venue)
            + len(self.performed_songs_missing_record)
            + len(self.reviews_dangling)
            + len(self.recordings_dangling)
            + len(self.recordings_date_mismatch)
            + len(self.releases_dangling_track_refs)
            + len(self.citations_bad_url)
        )
        if self.tier == "archival":
            # gdshowsdb catalogs many setlist-empty shows; that is honest scope,
            # reported via n_shows_without_performances (NOT folded into dangling).
            return base
        return base + len(self.shows_without_performances)

    @property
    def is_complete(self) -> bool:
        """True iff zero unresolved references on the hard relations.

        This is a *referential* claim, NOT "every show has a non-empty setlist":
        at the archival tier ``shows_without_performances`` is reported as scope
        (see ``n_shows_without_performances``), not counted here. Geo coverage is
        likewise reported but not folded in. Honesty over convenience: no soft
        metric is silently absorbed into this hard claim.
        """
        return self.dangling_total == 0

    @property
    def corpus_scope(self) -> str:
        """Honest, one-line statement of ingested corpus vs literature estimate."""
        lit_ref = f"community literature cites ~{FULL_CORPUS_SHOW_ESTIMATE} canonical concerts"
        if self.tier == "archival":
            return (
                f"archival compendium: {self.n_shows} ingested shows "
                f"({self.date_min} … {self.date_max}); {lit_ref}"
            )
        return (
            f"compendium: {self.n_shows} real shows "
            f"({self.date_min} … {self.date_max}); {lit_ref}"
        )

    def to_dict(self) -> dict:
        """JSON-serialisable view including derived fields."""
        return {
            "n_shows": self.n_shows,
            "n_performances": self.n_performances,
            "n_songs": self.n_songs,
            "n_venues": self.n_venues,
            "n_people": self.n_people,
            "date_min": self.date_min,
            "date_max": self.date_max,
            "geo_coverage_pct": round(self.geo_coverage_pct, 2),
            "n_segue_markers": self.n_segue_markers,
            "n_shows_with_tour": self.n_shows_with_tour,
            "performed_songs_without_lyric_pointer": self.performed_songs_without_lyric_pointer,
            "songs_with_lyricist_on_pointer": self.songs_with_lyricist_on_pointer,
            "songs_with_themes_on_pointer": self.songs_with_themes_on_pointer,
            "n_recordings_dropped_show": self.n_recordings_dropped_show,
            "n_recordings_dropped_date": self.n_recordings_dropped_date,
            "maximinus_reviews_n": self.maximinus_reviews_n,
            "curated_reviews_n": self.curated_reviews_n,
            "shows_missing_venue": list(self.shows_missing_venue),
            "performed_songs_missing_record": list(self.performed_songs_missing_record),
            "shows_without_performances": list(self.shows_without_performances),
            "venues_missing_geo": list(self.venues_missing_geo),
            "reviews_dangling": list(self.reviews_dangling),
            "recordings_dangling": list(self.recordings_dangling),
            "recordings_date_mismatch": list(self.recordings_date_mismatch),
            "releases_dangling_track_refs": list(self.releases_dangling_track_refs),
            "citations_bad_url": list(self.citations_bad_url),
            "n_shows_without_performances": self.n_shows_without_performances,
            "tier": self.tier,
            "dangling_total": self.dangling_total,
            "is_complete": self.is_complete,
            "corpus_scope": self.corpus_scope,
        }


def audit_completeness(
    comp: Compendium, geo: dict | None = None, tier: str | None = None
) -> CompletenessReport:
    """Audit referential completeness across the whole compendium.

    ``tier`` selects the setlist-completeness rule; when omitted it is resolved
    once from the active data tier (so the report's tier-dependent properties
    are internally consistent rather than re-reading the environment per call).
    """
    geo_map = geo if geo is not None else load_geo()
    if tier is None:
        from .tier import resolve_seed_dir

        tier = resolve_seed_dir().name

    venue_slugs = {v.slug for v in comp.venues}
    song_slugs = {s.slug for s in comp.songs}
    show_slugs = {s.slug for s in comp.shows}
    shows_with_perf = {p.show_slug for p in comp.performances}
    performed_songs = {p.song_slug for p in comp.performances}
    lyric_songs = {lp.song_slug for lp in comp.lyric_pointers}

    shows_missing_venue = tuple(
        sorted({s.slug for s in comp.shows if s.venue_slug not in venue_slugs})
    )
    performed_songs_missing = tuple(
        sorted(
            {p.song_slug for p in comp.performances if p.song_slug not in song_slugs}
        )
    )
    shows_without_perf = tuple(sorted(show_slugs - shows_with_perf))
    venues_missing_geo = tuple(sorted(venue_slugs - set(geo_map.keys())))
    reviews_dangling = tuple(
        sorted({r.show_slug for r in comp.reviews if r.show_slug not in show_slugs})
    )
    recordings_dangling = tuple(
        sorted(
            {
                rec.archive_id
                for rec in comp.recordings
                if rec.show_slug and rec.show_slug not in show_slugs
            }
        )
    )
    # Correctness, not just resolution: a recording whose archive_id encodes
    # gdYYYY-MM-DD must resolve to a show on *that* date — guards the
    # "wrong-but-resolving" mapping a pure existence check would miss.
    show_date_by_slug = {s.slug: s.date.isoformat() for s in comp.shows}
    recordings_date_mismatch = tuple(
        sorted(
            rec.archive_id
            for rec in comp.recordings
            if rec.show_slug in show_date_by_slug
            and (encoded := date_from_archive_id(rec.archive_id)) is not None
            and encoded != show_date_by_slug[rec.show_slug]
        )
    )
    releases_dangling = tuple(
        sorted(
            {
                f"{rel.slug}:{ref}"
                for rel in comp.releases
                for ref in rel.track_show_slugs
                if ref not in show_slugs
            }
        )
    )
    citations_bad_url = tuple(
        sorted(
            {
                c.key
                for c in comp.citations
                if not c.url or not c.url.startswith(("http://", "https://"))
            }
        )
    )

    dates = sorted(s.date.isoformat() for s in comp.shows)
    geo_pct = (
        100.0 * (len(venue_slugs & set(geo_map.keys())) / len(venue_slugs))
        if venue_slugs
        else 0.0
    )

    maximinus_reviews = sum(1 for r in comp.reviews if r.author == "maximinus")
    curated_reviews = len(comp.reviews) - maximinus_reviews

    return CompletenessReport(
        n_shows=len(comp.shows),
        n_performances=len(comp.performances),
        n_songs=len(comp.songs),
        n_venues=len(comp.venues),
        n_people=len(comp.people),
        date_min=dates[0] if dates else "",
        date_max=dates[-1] if dates else "",
        tier=tier,
        shows_missing_venue=shows_missing_venue,
        performed_songs_missing_record=performed_songs_missing,
        shows_without_performances=shows_without_perf,
        venues_missing_geo=venues_missing_geo,
        reviews_dangling=reviews_dangling,
        recordings_dangling=recordings_dangling,
        recordings_date_mismatch=recordings_date_mismatch,
        releases_dangling_track_refs=releases_dangling,
        citations_bad_url=citations_bad_url,
        geo_coverage_pct=geo_pct,
        n_segue_markers=sum(1 for p in comp.performances if p.segue_into),
        n_shows_with_tour=sum(1 for s in comp.shows if s.tour),
        performed_songs_without_lyric_pointer=len(performed_songs - lyric_songs),
        songs_with_lyricist_on_pointer=sum(
            1 for lp in comp.lyric_pointers if lp.lyricist
        ),
        songs_with_themes_on_pointer=sum(1 for lp in comp.lyric_pointers if lp.themes),
        maximinus_reviews_n=maximinus_reviews,
        curated_reviews_n=curated_reviews,
    )


class IncompleteCompendiumError(Exception):
    """Raised when the compendium has unresolved references."""

    def __init__(self, report: CompletenessReport) -> None:
        super().__init__(
            f"compendium incomplete: {report.dangling_total} dangling references"
        )
        self.report = report


def assert_complete(comp: Compendium, geo: dict | None = None) -> CompletenessReport:
    """Audit and raise :class:`IncompleteCompendiumError` if not complete."""
    report = audit_completeness(comp, geo=geo)
    if not report.is_complete:
        raise IncompleteCompendiumError(report)
    return report
