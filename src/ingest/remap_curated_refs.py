"""Remap seed-tier show slugs onto gdshowsdb canonical slugs (date + venue tokens)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace

from ..models import Recording, Review, Show
from ..sources.internet_archive import date_from_archive_id


def _date_from_archive_id(archive_id: str) -> str | None:
    return date_from_archive_id(archive_id)


def _venue_tokens(venue_slug: str) -> set[str]:
    return {t for t in venue_slug.replace("_", " ").split() if len(t) > 2}


def _remap_slug(ref: str, shows_by_date: dict[str, list[Show]], known: set[str]) -> str:
    if ref in known:
        return ref
    if "@" not in ref:
        return ref
    date_part, _, venue_hint = ref.partition("@")
    candidates = shows_by_date.get(date_part, ())
    if not candidates:
        return ref
    if len(candidates) == 1:
        return candidates[0].slug
    hint_tokens = _venue_tokens(venue_hint)
    best_slug = ref
    best_score = 0
    for show in candidates:
        score = len(hint_tokens & _venue_tokens(show.venue_slug))
        if score > best_score:
            best_score = score
            best_slug = show.slug
    return best_slug if best_score > 0 else ref


def remap_reviews_and_recordings(
    shows: tuple[Show, ...] | list[Show],
    reviews: list[Review],
    recordings: list[Recording],
) -> tuple[list[Review], list[Recording]]:
    """Align curated review/recording ``show_slug`` values with ingested shows."""
    show_list = list(shows)
    known = {s.slug for s in show_list}
    by_date: dict[str, list[Show]] = defaultdict(list)
    for show in show_list:
        by_date[show.date.isoformat()].append(show)

    remapped_reviews = [
        replace(r, show_slug=_remap_slug(r.show_slug, by_date, known))
        if r.show_slug
        else r
        for r in reviews
    ]
    remapped_recordings: list[Recording] = []
    for rec in recordings:
        slug = rec.show_slug
        if slug not in known:
            date_hint = _date_from_archive_id(rec.archive_id) or (
                slug.split("@")[0] if "@" in slug else None
            )
            if date_hint and date_hint in by_date:
                candidates = by_date[date_hint]
                if len(candidates) == 1:
                    slug = candidates[0].slug
                elif "@" in rec.show_slug:
                    slug = _remap_slug(rec.show_slug, by_date, known)
        remapped_recordings.append(
            replace(rec, show_slug=slug) if slug != rec.show_slug else rec
        )
    return remapped_reviews, remapped_recordings
