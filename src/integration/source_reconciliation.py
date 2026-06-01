"""Cross-source setlist reconciliation summaries."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ..integration.reconcile import Compendium


@dataclass(frozen=True)
class SourceReconciliationReport:
    """Counts and samples comparing supplemental sources to the primary compendium."""

    primary_shows: int
    primary_performances: int
    supplemental_label: str
    supplemental_shows: int
    supplemental_performances: int
    gap_shows_added: int
    shows_without_performances_primary: int
    performed_songs_without_lyric_pointer: int
    song_slug_mismatch_samples: tuple[dict[str, object], ...] = field(
        default_factory=tuple
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "primary_shows": self.primary_shows,
            "primary_performances": self.primary_performances,
            "supplemental_label": self.supplemental_label,
            "supplemental_shows": self.supplemental_shows,
            "supplemental_performances": self.supplemental_performances,
            "gap_shows_added": self.gap_shows_added,
            "shows_without_performances_primary": self.shows_without_performances_primary,
            "performed_songs_without_lyric_pointer": self.performed_songs_without_lyric_pointer,
            "song_slug_mismatch_samples": list(self.song_slug_mismatch_samples),
        }


def reconcile_gap_fill(
    comp: Compendium,
    *,
    supplemental_label: str,
    supplemental_show_slugs: set[str],
    supplemental_perf_count: int,
    shows_with_perf_before: set[str],
) -> SourceReconciliationReport:
    """Summarize how a supplemental source relates to the merged compendium."""
    show_slugs = {s.slug for s in comp.shows}
    shows_with_perf = {p.show_slug for p in comp.performances}
    performed_songs = {p.song_slug for p in comp.performances}
    lyric_songs = {lp.song_slug for lp in comp.lyric_pointers}
    gap_added = len(supplemental_show_slugs - shows_with_perf_before)

    # Sample shows where supplemental has performances but primary had none.
    samples: list[dict[str, object]] = []
    for slug in sorted(supplemental_show_slugs - shows_with_perf_before)[:10]:
        if slug in show_slugs:
            samples.append(
                {"show_slug": slug, "note": "gap-filled from supplemental source"}
            )

    return SourceReconciliationReport(
        primary_shows=len(comp.shows),
        primary_performances=len(comp.performances),
        supplemental_label=supplemental_label,
        supplemental_shows=len(supplemental_show_slugs),
        supplemental_performances=supplemental_perf_count,
        gap_shows_added=gap_added,
        shows_without_performances_primary=len(show_slugs - shows_with_perf),
        performed_songs_without_lyric_pointer=len(performed_songs - lyric_songs),
        song_slug_mismatch_samples=tuple(samples),
    )


def performance_counts_by_show(comp: Compendium) -> dict[str, int]:
    """Return performance row counts keyed by ``show_slug``."""
    counts: dict[str, int] = defaultdict(int)
    for perf in comp.performances:
        counts[perf.show_slug] += 1
    return dict(counts)


def source_contribution_counts(
    comp: Compendium,
    *,
    ingest_stats: dict[str, int] | None = None,
    sources_used: list[str] | tuple[str, ...] | None = None,
) -> dict[str, object]:
    """Summarize source-layer contributions without pretending row provenance."""

    ingest_stats = ingest_stats or {}
    sources_used = tuple(sources_used or ())
    return {
        "entity_counts": {
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
        },
        "source_layers_used": list(sources_used),
        "known_contribution_counters": dict(sorted(ingest_stats.items())),
        "source_layer_notes": {
            "gdshowsdb": "Primary show/performance spine when archival tier is used.",
            "truckin-gap-fill": "Setlist gap fill only; does not replace committed archival data.",
            "internet-archive-lma": "Recording metadata pointers only; audio is not bundled.",
            "bibliography-combined": "Citation metadata; does not create show or performance rows.",
            "external-lyric-sources": "Lyric URL pointers and curated metadata only; lyric text is not bundled.",
        },
    }


def ambiguity_buckets(comp: Compendium) -> dict[str, object]:
    """Count unresolved-but-explicit ambiguity classes for review."""

    show_slugs = {show.slug for show in comp.shows}
    shows_with_perf = {perf.show_slug for perf in comp.performances}
    performed_songs = {perf.song_slug for perf in comp.performances}
    lyric_songs = {pointer.song_slug for pointer in comp.lyric_pointers}
    recording_show_slugs = {recording.show_slug for recording in comp.recordings}
    release_track_slugs = {
        slug for release in comp.releases for slug in release.track_show_slugs
    }
    return {
        "shows_without_performances": len(show_slugs - shows_with_perf),
        "performed_songs_without_lyric_pointer": len(performed_songs - lyric_songs),
        "recordings_without_show": len(recording_show_slugs - show_slugs),
        "release_track_show_refs_without_show": len(release_track_slugs - show_slugs),
        "shows_with_multiple_same_day_venue_index": sum("#" in show.slug for show in comp.shows),
        "notes": [
            "Ambiguity buckets are publication-review counters, not automatic errors.",
            "Dangling hard references remain governed by completeness_report.json.",
        ],
    }


def conflict_buckets(
    *, ingest_stats: dict[str, int] | None = None, skipped_sources: list[str] | None = None
) -> dict[str, object]:
    """Surface skipped or dropped source inputs in stable buckets."""

    ingest_stats = ingest_stats or {}
    skipped_sources = skipped_sources or []
    dropped = {
        key: value
        for key, value in sorted(ingest_stats.items())
        if "dropped" in key or "reject" in key or "conflict" in key
    }
    credential_or_access = [
        item
        for item in skipped_sources
        if any(term in item.lower() for term in ("key not set", "403", "401", "forbidden"))
    ]
    unavailable = [
        item
        for item in skipped_sources
        if item not in credential_or_access
    ]
    return {
        "dropped_or_conflict_counters": dropped,
        "skipped_credential_or_access": credential_or_access,
        "skipped_unavailable": unavailable,
        "n_skipped_sources": len(skipped_sources),
    }


def venue_alias_collision_summary(comp: Compendium) -> dict[str, object]:
    """Summarize likely venue alias collisions without changing venue slugs."""

    by_name_city: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for venue in comp.venues:
        key = (
            venue.name.casefold().strip(),
            venue.city.casefold().strip(),
            venue.state_or_region.casefold().strip(),
        )
        by_name_city[key].append(venue.slug)
    collisions = {
        "|".join(key): sorted(slugs)
        for key, slugs in sorted(by_name_city.items())
        if len(slugs) > 1
    }
    return {
        "n_collision_groups": len(collisions),
        "n_slugs_in_collision_groups": sum(len(slugs) for slugs in collisions.values()),
        "sample_collision_groups": [
            {"normalized_name_city_region": key, "venue_slugs": slugs}
            for key, slugs in list(collisions.items())[:20]
        ],
        "policy": "Alias collisions are reported for review; canonical venue slugs are not rewritten here.",
    }
