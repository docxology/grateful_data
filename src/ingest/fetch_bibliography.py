"""Parse bundled bibliography sources into citation records."""

from __future__ import annotations

import re
from pathlib import Path

from ..models import Citation, normalize_slug

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BIBLIOGRAPHY_PATH = (
    PROJECT_ROOT
    / "The Grateful Dead  A Comprehensive Bibliography and Citation Reference.md"
)
REFERENCES_BIB_PATH = PROJECT_ROOT / "manuscript" / "references.bib"

_NUMBERED_ENTRY = re.compile(
    r"^\d+\.\s+\[(?P<title>[^\]]+)\]\((?P<url>https?://[^\)]+)\)",
    re.MULTILINE,
)
_INLINE_LINK = re.compile(r"\[(?P<title>[^\]]+)\]\((?P<url>https?://[^\)]+)\)")
_BIB_ENTRY = re.compile(r"@(?P<entry_type>\w+)\{(?P<key>[^,\s]+)", re.MULTILINE)
_BIB_FIELD = re.compile(
    r"(?P<name>\w+)\s*=\s*(?P<value>\{[^{}]*\}|\"[^\"]*\")", re.MULTILINE
)
_BIB_URL = re.compile(r"\\url\{([^}]+)\}")
_DOI_URL = re.compile(r"https?://(?:dx\.)?doi\.org/[^\s\)\]\[]+", re.IGNORECASE)
_YEAR_IN_TITLE = re.compile(r"\b(19|20)\d{2}\b")
_FOOTNOTE_REF = re.compile(r"\[\^\d+\]?")


def _clean_citation_value(value: str) -> str:
    """Remove Markdown footnote markers and surrounding citation punctuation."""
    cleaned = _FOOTNOTE_REF.sub("", value).strip()
    return cleaned.rstrip(".,;")


def _infer_kind(url: str, *, entry_type: str | None = None) -> str:
    if entry_type:
        lowered_type = entry_type.lower()
        if lowered_type in {"book", "inbook", "incollection", "proceedings"}:
            return "book"
        if lowered_type in {"article", "inproceedings", "techreport"}:
            return "article"
    lowered = url.lower()
    if "github.com" in lowered:
        return "github"
    if "arxiv.org" in lowered:
        return "article"
    if any(
        host in lowered
        for host in ("doi.org", "dukeupress.edu", "academic.oup.com", "tandfonline.com")
    ):
        return "article"
    if "archive.org" in lowered:
        return "corpus"
    if "reddit.com" in lowered:
        return "web"
    if "gratefulstats.com" in lowered and "/api" in lowered:
        return "api"
    return "web"


def _unwrap_bib_value(raw: str) -> str:
    text = raw.strip()
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1]
    elif text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    return text.strip()


def _extract_year(title: str, url: str) -> int | None:
    for text in (title, url):
        match = _YEAR_IN_TITLE.search(text)
        if match:
            return int(match.group(0))
    return None


def _extract_explicit_year(fields: dict[str, str]) -> int | None:
    year = fields.get("year")
    if year is None:
        return None
    match = _YEAR_IN_TITLE.search(year)
    return int(match.group(0)) if match else None


def _doi_url(raw_doi: str) -> str:
    doi = _clean_citation_value(raw_doi)
    doi = doi.removeprefix("doi:")
    if doi.lower().startswith(("http://", "https://")):
        return doi
    return f"https://doi.org/{doi}"


def _url_from_bib_fields(block: str, fields: dict[str, str]) -> str | None:
    """Return a stable URL from BibTeX URL, DOI, or legacy ``\\url`` wrappers."""
    if fields.get("url"):
        return fields["url"].strip()
    if fields.get("doi"):
        return _doi_url(fields["doi"])
    url_match = _BIB_URL.search(block)
    if url_match:
        return url_match.group(1).strip()
    return None


def parse_bibliography_markdown(text: str) -> list[Citation]:
    """Extract numbered bibliography entries with http(s) URLs."""
    citations: list[Citation] = []
    seen_urls: set[str] = set()
    for match in _NUMBERED_ENTRY.finditer(text):
        title = _clean_citation_value(match.group("title"))
        url = _clean_citation_value(match.group("url"))
        if url in seen_urls:
            continue
        seen_urls.add(url)
        key = normalize_slug(title)[:80] or normalize_slug(url)[:80]
        year = _extract_year(title, url)
        citations.append(
            Citation(key=key, title=title, url=url, kind=_infer_kind(url), year=year),
        )
    return citations


def parse_inline_markdown_links(text: str) -> list[Citation]:
    """Extract non-numbered markdown links from bibliography prose."""
    citations: list[Citation] = []
    seen_urls: set[str] = set()
    for match in _INLINE_LINK.finditer(text):
        title = _clean_citation_value(match.group("title"))
        url = _clean_citation_value(match.group("url"))
        if url in seen_urls:
            continue
        if title.startswith("^"):
            continue
        seen_urls.add(url)
        key = normalize_slug(title)[:80] or normalize_slug(url)[:80]
        year = _extract_year(title, url)
        citations.append(
            Citation(key=key, title=title, url=url, kind=_infer_kind(url), year=year),
        )
    return citations


def parse_doi_urls(text: str) -> list[Citation]:
    """Extract bare DOI URLs appearing in prose (not already linked)."""
    citations: list[Citation] = []
    seen: set[str] = set()
    for raw_url in _DOI_URL.findall(text):
        url = _clean_citation_value(raw_url)
        if url in seen:
            continue
        seen.add(url)
        key = normalize_slug(url.split("/")[-1])[:80]
        citations.append(
            Citation(
                key=key or "doi",
                title=f"DOI {url.split('/')[-1]}",
                url=url,
                kind="article",
            ),
        )
    return citations


def parse_references_bib(text: str) -> list[Citation]:
    """Extract citation rows from BibTeX entries.

    Supports ordinary ``url = {...}``, DOI-only entries, and legacy
    ``howpublished = {\\url{...}}`` wrappers used by earlier project notes.
    """
    citations: list[Citation] = []
    seen_urls: set[str] = set()
    for key_match in _BIB_ENTRY.finditer(text):
        key = key_match.group("key").strip()
        entry_type = key_match.group("entry_type").strip().lower()
        start = key_match.end()
        next_at = text.find("@", start)
        block = text[start : next_at if next_at != -1 else len(text)]
        fields: dict[str, str] = {}
        for field_match in _BIB_FIELD.finditer(block):
            fields[field_match.group("name").lower()] = _unwrap_bib_value(
                field_match.group("value")
            )
        url = _url_from_bib_fields(block, fields)
        if not url:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        title = _clean_citation_value(fields.get("title", key.replace("_", " ")))
        url = _clean_citation_value(url)
        year = _extract_explicit_year(fields) or _extract_year(
            title, fields.get("note", "")
        )
        citations.append(
            Citation(
                key=normalize_slug(key)[:80],
                title=title,
                url=url,
                kind=_infer_kind(url, entry_type=entry_type),
                year=year,
            ),
        )
    return citations


def _merge_citations(*groups: list[Citation]) -> list[Citation]:
    merged: list[Citation] = []
    seen_urls: set[str] = set()
    for group in groups:
        for citation in group:
            if citation.url in seen_urls:
                continue
            seen_urls.add(citation.url)
            merged.append(citation)
    return merged


def load_bibliography_citations(path: Path | None = None) -> list[Citation]:
    """Load citations from the project bibliography markdown (offline-safe)."""
    bib_path = path or BIBLIOGRAPHY_PATH
    if not bib_path.is_file():
        return []
    return parse_bibliography_markdown(bib_path.read_text(encoding="utf-8"))


def load_references_bib_citations(path: Path | None = None) -> list[Citation]:
    """Load citations from ``manuscript/references.bib`` (offline-safe)."""
    bib_path = path or REFERENCES_BIB_PATH
    if not bib_path.is_file():
        return []
    return parse_references_bib(bib_path.read_text(encoding="utf-8"))


def load_all_project_citations(
    *,
    bibliography_md: Path | None = None,
    references_bib: Path | None = None,
    include_inline: bool = True,
    include_dois: bool = True,
) -> list[Citation]:
    """Merge bibliography markdown, inline links, DOIs, and ``references.bib``."""
    md_path = bibliography_md or BIBLIOGRAPHY_PATH
    md_text = md_path.read_text(encoding="utf-8") if md_path.is_file() else ""
    groups: list[list[Citation]] = [
        parse_bibliography_markdown(md_text) if md_text else [],
        load_references_bib_citations(references_bib),
    ]
    if include_inline and md_text:
        groups.append(parse_inline_markdown_links(md_text))
    if include_dois and md_text:
        groups.append(parse_doi_urls(md_text))
    return _merge_citations(*groups)
