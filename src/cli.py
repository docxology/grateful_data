"""Tiny query CLI over the bundled compendium.

Usage::

    python -m projects.grateful_data.src.cli stats
    python -m projects.grateful_data.src.cli song scarlet_begonias
    python -m projects.grateful_data.src.cli show 1977-05-08@barton_hall_ithaca
    python -m projects.grateful_data.src.cli person garcia
    python -m projects.grateful_data.src.cli venue barton_hall_ithaca
    python -m projects.grateful_data.src.cli provenance songs scarlet_begonias
    python -m projects.grateful_data.src.cli list shows | songs | people | venues
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from .analysis import composers, eras, stats, timeseries
from .seed import load_seed_compendium


def _dump(payload: Any) -> None:
    print(json.dumps(payload, indent=2, default=str))


def _cmd_stats(comp, args) -> None:
    s = stats.compute(comp, top_n=15)
    _dump(
        {
            "n_shows": s.n_shows,
            "n_songs": s.n_songs,
            "n_people": s.n_people,
            "n_venues": s.n_venues,
            "n_performances": s.n_performances,
            "n_recordings": s.n_recordings,
            "n_releases": s.n_releases,
            "n_citations": s.n_citations,
            "n_lyric_pointers": len(comp.lyric_pointers),
            "n_reviews": len(comp.reviews),
            "shows_per_year": s.shows_per_year,
            "top_songs": list(s.top_songs),
        }
    )


def _cmd_song(comp, args) -> None:
    slug = args.slug
    song = comp.song_by_slug.get(slug)
    if not song:
        raise SystemExit(f"no song with slug {slug!r}")
    history = [p.show_slug for p in comp.performances if p.song_slug == slug]
    lp = next((x for x in comp.lyric_pointers if x.song_slug == slug), None)
    _dump(
        {
            "slug": song.slug,
            "title": song.title,
            "composers": list(song.composers),
            "lyricists": list(song.lyricists),
            "first_performed": song.first_performed.isoformat()
            if song.first_performed
            else None,
            "last_performed": song.last_performed.isoformat()
            if song.last_performed
            else None,
            "aliases": list(song.aliases),
            "n_performances_in_seed": len(history),
            "shows_performed_in": history[:10],
            "lyric_pointer": (
                {
                    "lyricist": lp.lyricist,
                    "source_url": lp.source_url,
                    "themes": list(lp.themes),
                }
                if lp
                else None
            ),
        }
    )


def _cmd_show(comp, args) -> None:
    slug = args.slug
    show = comp.show_by_slug.get(slug)
    if not show:
        raise SystemExit(f"no show with slug {slug!r}")
    perfs = sorted(
        (p for p in comp.performances if p.show_slug == slug),
        key=lambda p: (p.set_number, p.position),
    )
    venue = comp.venue_by_slug.get(show.venue_slug)
    reviews = [r for r in comp.reviews if r.show_slug == slug]
    _dump(
        {
            "slug": show.slug,
            "date": show.date.isoformat(),
            "venue": {
                "slug": venue.slug,
                "name": venue.name,
                "city": venue.city,
                "state": venue.state_or_region,
            }
            if venue
            else None,
            "tour": show.tour,
            "era": eras.era_of(show.date),
            "setlist": [
                {
                    "set": p.set_number,
                    "pos": p.position,
                    "song": p.song_slug,
                    "segue_into": p.segue_into,
                }
                for p in perfs
            ],
            "reviews": [
                {
                    "author": r.author,
                    "kind": r.kind,
                    "sentiment": r.sentiment,
                    "summary": r.summary,
                }
                for r in reviews
            ],
        }
    )


def _cmd_person(comp, args) -> None:
    slug = args.slug
    person = comp.person_by_slug.get(slug)
    if not person:
        raise SystemExit(f"no person with slug {slug!r}")
    _dump(
        {
            "slug": person.slug,
            "full_name": person.full_name,
            "intervals": [
                {
                    "start": s.isoformat(),
                    "end": e.isoformat() if e else None,
                    "role": role,
                }
                for s, e, role in person.intervals
            ],
        }
    )


def _cmd_venue(comp, args) -> None:
    slug = args.slug
    venue = comp.venue_by_slug.get(slug)
    if not venue:
        raise SystemExit(f"no venue with slug {slug!r}")
    shows_here = [s.slug for s in comp.shows if s.venue_slug == slug]
    _dump(
        {
            "slug": venue.slug,
            "name": venue.name,
            "city": venue.city,
            "state_or_region": venue.state_or_region,
            "country": venue.country,
            "n_shows_in_seed": len(shows_here),
            "shows": shows_here,
        }
    )


def _cmd_list(comp, args) -> None:
    kind = args.kind
    if kind == "shows":
        _dump([s.slug for s in comp.shows])
    elif kind == "songs":
        _dump([s.slug for s in comp.songs])
    elif kind == "people":
        _dump([p.slug for p in comp.people])
    elif kind == "venues":
        _dump([v.slug for v in comp.venues])
    elif kind == "tours":
        from .analysis import tours

        _dump(tours.shows_per_tour(comp))
    elif kind == "releases":
        _dump(
            [
                {
                    "slug": r.slug,
                    "title": r.title,
                    "kind": r.kind,
                    "date": r.release_date.isoformat(),
                }
                for r in comp.releases
            ]
        )
    else:
        raise SystemExit(f"unknown list kind {kind!r}")


def _cmd_composers(comp, args) -> None:
    _dump(
        {
            "songs_by_composer": composers.composer_song_counts(comp),
            "performances_by_composer": composers.composer_performance_counts(comp),
            "songs_by_lyricist": composers.lyricist_song_counts(comp),
        }
    )


def _cmd_year(comp, args) -> None:
    py = timeseries.performances_per_year(comp)
    _dump(py)


def _cmd_diagnostics(comp, args) -> None:
    from .honesty import HonestyBoundary
    from .validation import validate_seed

    boundary = HonestyBoundary()
    violations = boundary.check_compendium(comp)
    seed_violations = validate_seed()
    _dump(
        {
            "honesty_boundary": {
                "ok": len(violations) == 0,
                "violations": list(violations),
            },
            "seed_schema": {
                "ok": len(seed_violations) == 0,
                "violations": list(seed_violations),
            },
            "totals": {
                "shows": len(comp.shows),
                "songs": len(comp.songs),
                "people": len(comp.people),
                "venues": len(comp.venues),
                "performances": len(comp.performances),
                "recordings": len(comp.recordings),
                "releases": len(comp.releases),
                "lyric_pointers": len(comp.lyric_pointers),
                "reviews": len(comp.reviews),
                "citations": len(comp.citations),
            },
        }
    )


def _cmd_provenance(comp, args) -> None:
    from .provenance import lookup_provenance, provenance_records

    matches = lookup_provenance(provenance_records(comp), args.entity_type, args.key)
    if not matches:
        raise SystemExit(
            f"no provenance record for {args.entity_type!r} key {args.key!r}"
        )
    _dump([record.to_dict() for record in matches])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats")
    sp = sub.add_parser("song")
    sp.add_argument("slug")
    sp = sub.add_parser("show")
    sp.add_argument("slug")
    sp = sub.add_parser("person")
    sp.add_argument("slug")
    sp = sub.add_parser("venue")
    sp.add_argument("slug")
    sp = sub.add_parser("list")
    sp.add_argument(
        "kind", choices=["shows", "songs", "people", "venues", "tours", "releases"]
    )
    sub.add_parser("composers")
    sub.add_parser("year")
    sub.add_parser("diagnostics")
    sp = sub.add_parser("provenance")
    sp.add_argument(
        "entity_type",
        choices=[
            "citations",
            "lyric_pointers",
            "people",
            "performances",
            "recordings",
            "releases",
            "reviews",
            "segues",
            "shows",
            "songs",
            "venues",
        ],
    )
    sp.add_argument("key")
    return parser


DISPATCH = {
    "stats": _cmd_stats,
    "song": _cmd_song,
    "show": _cmd_show,
    "person": _cmd_person,
    "venue": _cmd_venue,
    "list": _cmd_list,
    "composers": _cmd_composers,
    "year": _cmd_year,
    "diagnostics": _cmd_diagnostics,
    "provenance": _cmd_provenance,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    comp = load_seed_compendium()
    DISPATCH[args.cmd](comp, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
