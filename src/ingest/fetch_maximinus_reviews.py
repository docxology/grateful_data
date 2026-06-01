"""maximinus/grateful-dead-reviews corpus fetch adapter."""

from __future__ import annotations

import re
from datetime import date

from ..models import Review, normalize_slug
from ._vendor_fetch import fetch_or_read_cache_with_fallbacks

CORPUS_URL = "https://raw.githubusercontent.com/maximinus/grateful-dead-reviews/master/dead_reviews.txt"
CORPUS_FALLBACK_URLS: tuple[str, ...] = (CORPUS_URL,)
SOURCE_URL = (
    "https://github.com/maximinus/grateful-dead-reviews/blob/master/dead_reviews.txt"
)

_REVIEW_LINE = re.compile(r"^(\d{2}-\d{2}-\d{2})\s+([\d.]+|-)\s+(.*)$", re.MULTILINE)


def _dd_mm_yy_to_iso(token: str) -> str | None:
    parts = token.split("-")
    if len(parts) != 3 or parts[0] == "??":
        return None
    day_s, month_s, year_s = parts
    try:
        day, month, year2 = int(day_s), int(month_s), int(year_s)
    except ValueError:
        return None
    year = 1900 + year2
    try:
        date(year, month, day)
    except ValueError:
        return None
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_maximinus_reviews(text: str) -> list[Review]:
    """Parse ``dead_reviews.txt`` into :class:`Review` rows (unmapped show slugs)."""
    reviews: list[Review] = []
    for date_token, score_token, summary in _REVIEW_LINE.findall(text):
        if score_token == "-":
            continue
        iso = _dd_mm_yy_to_iso(date_token)
        if iso is None:
            continue
        score = float(score_token)
        sentiment = max(0.0, min(1.0, score / 5.0))
        show_slug = f"{iso}@maximinus_pending"
        reviews.append(
            Review(
                show_slug=show_slug,
                author="maximinus",
                sentiment=sentiment,
                summary=summary.strip()[:500],
                source_url=SOURCE_URL,
                kind="fan",
            )
        )
    return reviews


def attach_reviews_to_shows(
    reviews: list[Review], shows_by_date: dict[str, list]
) -> list[Review]:
    """Map date-only maximinus rows onto ingested show slugs (first show on that date)."""
    attached: list[Review] = []
    for review in reviews:
        if not review.show_slug.endswith("@maximinus_pending"):
            attached.append(review)
            continue
        iso = review.show_slug.split("@", 1)[0]
        candidates = shows_by_date.get(iso, ())
        if not candidates:
            continue
        slug = sorted(candidates, key=lambda s: s.slug)[0].slug
        attached.append(
            Review(
                show_slug=slug,
                author=review.author,
                sentiment=review.sentiment,
                summary=review.summary,
                source_url=review.source_url,
                kind=review.kind,
            )
        )
    return attached


def fetch_maximinus_reviews(*, online: bool) -> list[Review]:
    """Fetch and parse the maximinus review corpus."""
    text, _ = fetch_or_read_cache_with_fallbacks(
        source="maximinus",
        filename="dead_reviews.txt",
        urls=CORPUS_FALLBACK_URLS,
        online=online,
        min_bytes=10_000,
    )
    return parse_maximinus_reviews(text)


def citation_key_for_maximinus() -> str:
    return normalize_slug("maximinus grateful dead reviews")
