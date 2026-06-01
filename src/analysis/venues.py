"""Venue data-quality measurement (detect, don't silently mutate).

A single physical venue is recorded under several name variants across sources
(spelling, punctuation, word order, official vs common name). The curated
:data:`integration.aliases.VENUE_ALIAS_MAP` captures the unambiguous cases.

This module *reports* the duplication rather than rewriting the corpus. Two
findings are surfaced:

* how many distinct venue slugs would collapse under the conservative alias
  layer (and the post-canonicalization venue count);
* how many shows share a date AND a canonical venue under different original
  spellings — *ambiguous same-date collisions*.

Those collisions have **near-disjoint setlists** (mean Jaccard ~0.05), which is
genuinely ambiguous: such a pair could be a single concert whose setlist was
split across two venue-spelling records, OR two legitimately distinct
performances — the Grateful Dead routinely played early/late shows on the same
date. The low overlap does not distinguish these cases, so we do NOT label them
"duplicates" and we do NOT merge them; we report the collision count and the
overlap as an honest measurement and leave the corpus unmutated. See
``manuscript/04_results.md`` (Limitations).

Scope note: the alias map is *precision-oriented* — it only collapses
hand-verified same-venue spellings. Its **recall is non-exhaustive**: other
real same-venue spelling variants outside the curated 20 may remain
un-canonicalized, so the reported collapse count is a lower bound.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations

from ..integration.aliases import VENUE_ALIAS_MAP, canonicalize_venue_slug
from ..integration.reconcile import Compendium


@dataclass(frozen=True)
class VenueDuplicationReport:
    n_venue_slugs: int
    n_alias_slugs_present: int
    n_venues_after_canonicalization: int
    #: Same-date, same-canonical-venue collisions under different spellings.
    #: AMBIGUOUS — a split single concert OR two legitimate same-day shows.
    n_ambiguous_same_date_collisions: int
    mean_collision_setlist_jaccard: float

    @property
    def n_venues_collapsed(self) -> int:
        return self.n_venue_slugs - self.n_venues_after_canonicalization

    def to_dict(self) -> dict[str, int | float]:
        return {
            "n_venue_slugs": self.n_venue_slugs,
            "n_alias_slugs_present": self.n_alias_slugs_present,
            "n_venues_after_canonicalization": self.n_venues_after_canonicalization,
            "n_venues_collapsed": self.n_venues_collapsed,
            "n_ambiguous_same_date_collisions": self.n_ambiguous_same_date_collisions,
            "mean_collision_setlist_jaccard": self.mean_collision_setlist_jaccard,
        }


NEGATIVE_CONTROL_VENUE_SLUGS: tuple[str, ...] = (
    "fillmore_west_san_francisco",
    "fillmore_east_new_york",
    "fillmore_auditorium_san_francisco",
    "oakland_coliseum_stadium_oakland",
    "oakland_auditorium_oakland",
    "felt_forum_madison_square_garden_new_york",
)


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def venue_duplication_report(comp: Compendium) -> VenueDuplicationReport:
    """Quantify probable venue/show duplication without mutating the corpus."""
    venue_slugs = {v.slug for v in comp.venues}
    n_alias_present = sum(1 for s in venue_slugs if s in VENUE_ALIAS_MAP)
    canon_targets = {canonicalize_venue_slug(s) for s in venue_slugs}

    songs_by_show: dict[str, set[str]] = defaultdict(set)
    for p in comp.performances:
        songs_by_show[p.show_slug].add(p.song_slug)

    by_key: dict[tuple[object, str], list[str]] = defaultdict(list)
    for s in comp.shows:
        by_key[(s.date, canonicalize_venue_slug(s.venue_slug))].append(s.slug)

    collisions = [slugs for (_d, _cv), slugs in by_key.items() if len(slugs) > 1]
    jaccards: list[float] = []
    for slugs in collisions:
        # TRUE pairwise mean Jaccard across the colliding records (not
        # first-vs-rest). For the common size-2 group this is the single pair;
        # for size>2 groups it is the mean over all C(n,2) pairs.
        sets = [songs_by_show.get(sl, set()) for sl in slugs]
        pair_jacs = [_jaccard(a, b) for a, b in combinations(sets, 2)]
        if pair_jacs:
            jaccards.append(sum(pair_jacs) / len(pair_jacs))

    mean_jac = round(sum(jaccards) / len(jaccards), 4) if jaccards else 0.0
    return VenueDuplicationReport(
        n_venue_slugs=len(venue_slugs),
        n_alias_slugs_present=n_alias_present,
        n_venues_after_canonicalization=len(canon_targets),
        n_ambiguous_same_date_collisions=len(collisions),
        mean_collision_setlist_jaccard=mean_jac,
    )


def venue_identity_review(comp: Compendium) -> dict[str, object]:
    """Return reviewed venue-alias decisions and negative controls."""

    venue_slugs = {venue.slug for venue in comp.venues}
    show_counts: dict[str, int] = defaultdict(int)
    for show in comp.shows:
        show_counts[show.venue_slug] += 1

    alias_rows = []
    for source_slug, canonical_slug in sorted(VENUE_ALIAS_MAP.items()):
        source_present = source_slug in venue_slugs
        canonical_present = canonical_slug in venue_slugs
        alias_rows.append(
            {
                "source_slug": source_slug,
                "canonical_slug": canonical_slug,
                "source_present": source_present,
                "canonical_present": canonical_present,
                "source_show_count": show_counts.get(source_slug, 0),
                "canonical_show_count": show_counts.get(canonical_slug, 0),
                "decision_status": "reviewed-collapse",
                "review_note": (
                    "Conservative spelling/name variant collapse; does not mutate "
                    "the compendium and is reported for review."
                ),
            }
        )

    negative_controls = []
    for slug in NEGATIVE_CONTROL_VENUE_SLUGS:
        negative_controls.append(
            {
                "slug": slug,
                "canonical_slug": canonicalize_venue_slug(slug),
                "preserved_distinct": canonicalize_venue_slug(slug) == slug,
                "present_in_compendium": slug in venue_slugs,
                "show_count": show_counts.get(slug, 0),
                "review_note": "Negative-control venue intentionally not folded by alias map.",
            }
        )

    report = venue_duplication_report(comp)
    return {
        "method": "reviewed conservative alias map; report-only, no venue rows rewritten",
        "summary": report.to_dict(),
        "alias_decisions": alias_rows,
        "negative_controls": negative_controls,
        "policy": (
            "Only hand-verified same-venue spellings collapse. Distinct rooms, "
            "stadium/arena splits, and time-renamed venues remain separate unless "
            "future review explicitly changes the map."
        ),
    }
