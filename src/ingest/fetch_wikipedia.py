"""Wikipedia MediaWiki fetch adapter for discography + members."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime

from ..models import Person, Release
from ..sources.wikipedia import parse_person as parse_wiki_person
from ..sources.wikipedia import parse_release as parse_wiki_release
from ._vendor_fetch import vendor_path

API_URL = "https://en.wikipedia.org/w/api.php"
_TITLE_RE = re.compile(r"''\[\[([^|\]]+)(?:\|([^\]]+))?\]\]''")
_RELEASED_RE = re.compile(r"\* Released:\s*([^\n<]+)")
_MEMBER_RE = re.compile(r"\* \[\[([^|\]]+)(?:\|([^\]]+))?\]\]")
_DATE_FORMATS = ("%B %d, %Y", "%B %Y", "%Y-%m-%d", "%Y")


def _api_get(params: dict[str, str]) -> dict:
    url = API_URL + "?" + urllib.parse.urlencode({**params, "format": "json"})
    req = urllib.request.Request(
        url, headers={"User-Agent": "grateful_data-ingest/1.0"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _parse_release_date(raw: str) -> str | None:
    cleaned = raw.strip().rstrip(".")
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def parse_discography_wikitext(wikitext: str) -> list[dict]:
    """Extract album rows from current Grateful Dead discography wikitext tables."""
    rows: list[dict] = []
    seen: set[str] = set()
    for block in wikitext.split("|-")[1:]:
        title_m = _TITLE_RE.search(block)
        rel_m = _RELEASED_RE.search(block)
        if not title_m or not rel_m:
            continue
        title = (title_m.group(2) or title_m.group(1)).strip()
        release_date = _parse_release_date(rel_m.group(1))
        if not release_date:
            continue
        slug_key = f"{title}|{release_date}"
        if slug_key in seen:
            continue
        seen.add(slug_key)
        kind = (
            "live" if re.search(r"\blive\b", block[:400], re.IGNORECASE) else "studio"
        )
        rows.append({"title": title, "release_date": release_date, "kind": kind})
    return rows


def parse_members_wikitext(wikitext: str) -> list[dict]:
    """Extract former-member names from the Grateful Dead article wikitext."""
    start = wikitext.find("=== Former members ===")
    if start < 0:
        return []
    chunk = wikitext[start:]
    end = chunk.find("\n===")
    if end > 0:
        chunk = chunk[:end]
    rows: list[dict] = []
    seen: set[str] = set()
    for match in _MEMBER_RE.finditer(chunk):
        name = (match.group(2) or match.group(1)).strip()
        if len(name) < 3:
            continue
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        if slug in seen:
            continue
        seen.add(slug)
        rows.append({"slug": slug, "full_name": name, "intervals": []})
    return rows


def fetch_wikipedia_releases(*, online: bool = False) -> list[Release]:
    """Parse studio/live album rows from the Grateful Dead discography wikitext."""
    cache = vendor_path("wikipedia", "discography.json")
    if cache.is_file():
        payload = json.loads(cache.read_text(encoding="utf-8"))
        if payload:
            return [parse_wiki_release(row) for row in payload]

    if not online:
        return []

    data = _api_get(
        {
            "action": "parse",
            "page": "Grateful_Dead_discography",
            "prop": "wikitext",
        }
    )
    wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
    rows = parse_discography_wikitext(wikitext)
    if rows:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return [parse_wiki_release(row) for row in rows]


def fetch_wikipedia_personnel(*, online: bool = False) -> list[Person]:
    """Parse former-member names from the Grateful Dead article (intervals optional)."""
    cache = vendor_path("wikipedia", "members.json")
    if cache.is_file():
        payload = json.loads(cache.read_text(encoding="utf-8"))
        if payload:
            return [parse_wiki_person(row) for row in payload]

    if not online:
        return []

    data = _api_get(
        {
            "action": "parse",
            "page": "Grateful_Dead",
            "prop": "wikitext",
        }
    )
    wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
    rows = parse_members_wikitext(wikitext)
    if rows:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    return [parse_wiki_person(row) for row in rows]
