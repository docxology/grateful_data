#!/usr/bin/env python3
"""Build the reconciled compendium from the bundled seed and dump CSV+JSON."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.seed import load_seed_compendium  # noqa: E402


def main() -> None:
    out_dir = ROOT / "output" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    comp = load_seed_compendium()

    with (out_dir / "shows.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["slug", "date", "venue_slug", "tour"])
        for s in comp.shows:
            w.writerow([s.slug, s.date.isoformat(), s.venue_slug, s.tour or ""])
    with (out_dir / "performances.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["show_slug", "song_slug", "set_number", "position", "segue_into"])
        for p in comp.performances:
            w.writerow(
                [p.show_slug, p.song_slug, p.set_number, p.position, p.segue_into or ""]
            )
    with (out_dir / "songs.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["slug", "title", "composers", "lyricists"])
        for s in comp.songs:
            w.writerow([s.slug, s.title, ";".join(s.composers), ";".join(s.lyricists)])
    with (out_dir / "compendium.json").open("w", encoding="utf-8") as fh:
        json.dump(
            {
                "n_shows": len(comp.shows),
                "n_venues": len(comp.venues),
                "n_songs": len(comp.songs),
                "n_people": len(comp.people),
                "n_performances": len(comp.performances),
                "n_recordings": len(comp.recordings),
                "n_citations": len(comp.citations),
            },
            fh,
            indent=2,
        )
    print(out_dir / "shows.csv")
    print(out_dir / "performances.csv")
    print(out_dir / "songs.csv")
    print(out_dir / "compendium.json")


if __name__ == "__main__":
    main()
