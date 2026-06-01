"""dead.net band roster fetch adapter."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..models import Person
from ..sources.dead_net import parse as parse_person_record
from ._vendor_fetch import fetch_or_read_cache

BAND_URL = "https://www.dead.net/band"
_NAME_RE = re.compile(r"<h[23][^>]*>\s*([^<]+?)\s*</h[23]>", re.IGNORECASE)


def _slugify_name(name: str) -> str:
    out = []
    for ch in name.lower():
        out.append(ch if ch.isalnum() else "_")
    return "_".join(filter(None, "".join(out).split("_")))


def fetch_dead_net_personnel(
    *, online: bool = False, seed_dir: Path | None = None
) -> list[Person]:
    """Return personnel from curated seed, optionally unioned with dead.net page scrape."""
    people: dict[str, Person] = {}
    if seed_dir:
        path = seed_dir / "personnel.json"
        if path.is_file():
            for row in json.loads(path.read_text(encoding="utf-8")):
                person = parse_person_record(row)
                people[person.slug] = person

    if not online:
        return list(people.values())

    try:
        html = fetch_or_read_cache(
            source="dead_net", filename="band.html", url=BAND_URL, online=True
        )
    except OSError:
        return list(people.values())

    for name in _NAME_RE.findall(html):
        clean = name.strip()
        if len(clean) < 3 or clean.lower() in {"band", "members", "the grateful dead"}:
            continue
        slug = _slugify_name(clean)
        if slug in people:
            continue
        people[slug] = Person(slug=slug, full_name=clean, intervals=())

    return list(people.values())
