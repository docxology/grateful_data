"""Markdown entity page generation (eras, venues, people)."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from ..analysis import composers, eras, geo
from ..integration.reconcile import Compendium


def _ensure(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_entity_pages(comp: Compendium, base: Path) -> tuple[Path, Path, Path]:
    show_date = {s.slug: s.date for s in comp.shows}

    era_dir = _ensure(base / "eras")
    by_era_shows: dict[str, list[str]] = defaultdict(list)
    for show in comp.shows:
        by_era_shows[eras.era_of(show.date)].append(show.slug)
    by_era_songs: dict[str, Counter[str]] = defaultdict(Counter)
    for perf in comp.performances:
        era = eras.era_of(show_date[perf.show_slug])
        by_era_songs[era][perf.song_slug] += 1

    era_index = ["# Eras", ""]
    for name, start, end in eras.ERAS:
        era_show_slugs = sorted(by_era_shows.get(name, []))
        page_lines = [
            f"# {name}",
            "",
            f"- **Window:** {start.isoformat()} → {end.isoformat()}",
            f"- **Shows in seed:** {len(era_show_slugs)}",
            "",
            "## Top songs in this era",
        ]
        for slug, count in by_era_songs.get(name, Counter()).most_common(20):
            page_lines.append(f"- `{slug}` ({count})")
        page_lines.append("")
        page_lines.append("## Shows")
        for slug in era_show_slugs:
            page_lines.append(f"- `{slug}`")
        slug = name.lower().replace(" ", "_").replace("->", "to").replace("+", "_")
        (era_dir / f"{slug}.md").write_text(
            "\n".join(page_lines) + "\n", encoding="utf-8"
        )
        era_index.append(f"- {name}: {len(era_show_slugs)} shows")
    (era_dir / "_index.md").write_text("\n".join(era_index) + "\n", encoding="utf-8")

    venue_dir = _ensure(base / "venues")
    geo_map = geo.load_geo()
    venue_index = ["# Venues", ""]
    for venue in comp.venues:
        venue_shows = [show for show in comp.shows if show.venue_slug == venue.slug]
        years = sorted({show.date.year for show in venue_shows}) if venue_shows else []
        page = [
            f"# {venue.name}",
            "",
            f"- **Slug:** `{venue.slug}`",
            f"- **Location:** {venue.city}, {venue.state_or_region}, {venue.country}",
            f"- **Shows in seed:** {len(venue_shows)}",
        ]
        if years:
            page.append(f"- **Year span:** {min(years)}–{max(years)}")
        geo_entry = geo_map.get(venue.slug)
        if geo_entry:
            page.append(
                f"- **Coordinates:** ({geo_entry['lat']}, {geo_entry['lon']}) — region {geo_entry['region']}"
            )
        if venue_shows:
            page.append("")
            page.append("## Shows here")
            for show in sorted(venue_shows, key=lambda s: s.date):
                page.append(f"- {show.date.isoformat()} ({show.tour or 'no tour tag'})")
        (venue_dir / f"{venue.slug}.md").write_text(
            "\n".join(page) + "\n", encoding="utf-8"
        )
        venue_index.append(
            f"- [{venue.name}]({venue.slug}.md) — {len(venue_shows)} shows"
        )
    (venue_dir / "_index.md").write_text(
        "\n".join(venue_index) + "\n", encoding="utf-8"
    )

    person_dir = _ensure(base / "people")
    person_index = ["# People", ""]
    composer_song_count = composers.composer_song_counts(comp)
    for person in comp.people:
        page = [
            f"# {person.full_name}",
            "",
            f"- **Slug:** `{person.slug}`",
            f"- **Songs credited as composer:** {composer_song_count.get(person.full_name, 0)}",
        ]
        if person.intervals:
            page.append("")
            page.append("## Intervals")
            for interval_start, interval_end, role in person.intervals:
                end_label = (
                    interval_end.isoformat() if interval_end is not None else "present"
                )
                page.append(f"- {interval_start.isoformat()} → {end_label}: {role}")
        active_shows = [s for s in comp.shows if person.active_on(s.date)]
        if active_shows:
            page.append("")
            page.append(
                f"## Shows in seed during this person's intervals ({len(active_shows)})"
            )
            for show in sorted(active_shows, key=lambda s: s.date)[:30]:
                page.append(f"- {show.date.isoformat()} @ {show.venue_slug}")
            if len(active_shows) > 30:
                page.append(f"- … ({len(active_shows) - 30} more)")
        (person_dir / f"{person.slug}.md").write_text(
            "\n".join(page) + "\n", encoding="utf-8"
        )
        person_index.append(f"- [{person.full_name}]({person.slug}.md)")
    (person_dir / "_index.md").write_text(
        "\n".join(person_index) + "\n", encoding="utf-8"
    )
    return era_dir, venue_dir, person_dir
