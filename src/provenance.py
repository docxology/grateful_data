"""Sidecar provenance records for compendium entities.

The core schema stays intentionally small and frozen. This module builds a
separate, deterministic provenance sidecar that documents which ingest or
analysis layer supports each entity type without claiming row-level source
certainty that the current schema does not store.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

from .analysis.segues import segue_edges
from .integration.reconcile import Compendium


@dataclass(frozen=True)
class ProvenanceRecord:
    """Pointer-only provenance metadata for one entity or derived row."""

    entity_type: str
    key: str
    source_keys: tuple[str, ...]
    confidence: str
    notes: str
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.entity_type.strip():
            raise ValueError("entity_type must be non-empty")
        if not self.key.strip():
            raise ValueError("key must be non-empty")
        if not self.source_keys or any(not source.strip() for source in self.source_keys):
            raise ValueError("source_keys must be non-empty strings")
        if not self.confidence.strip():
            raise ValueError("confidence must be non-empty")
        if not self.notes.strip():
            raise ValueError("notes must be non-empty")

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_type": self.entity_type,
            "key": self.key,
            "source_keys": list(self.source_keys),
            "confidence": self.confidence,
            "notes": self.notes,
            "metadata": dict(sorted(self.metadata.items())),
        }

    def to_csv_row(self) -> dict[str, str]:
        return {
            "entity_type": self.entity_type,
            "key": self.key,
            "source_keys": ";".join(self.source_keys),
            "confidence": self.confidence,
            "notes": self.notes,
            "metadata": json.dumps(dict(sorted(self.metadata.items())), sort_keys=True),
        }


def _sources(*items: str) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(item for item in items if item)))


def provenance_records(compendium: Compendium) -> tuple[ProvenanceRecord, ...]:
    """Infer deterministic sidecar provenance for the current compendium.

    These records are intentionally conservative. They identify the ingest or
    computation family that produced an entity class, not hidden per-cell
    certainty that the frozen dataclasses do not carry.
    """

    records: list[ProvenanceRecord] = []
    note = "Sidecar provenance inferred from current ingest layers; not row-level source proof."

    for show in sorted(compendium.shows, key=lambda item: item.slug):
        records.append(
            ProvenanceRecord(
                entity_type="shows",
                key=show.slug,
                source_keys=_sources("gdshowsdb", "truckin-gap-fill", "curated-seed"),
                confidence="entity-type",
                notes=note,
                metadata={
                    "date": show.date.isoformat(),
                    "venue_slug": show.venue_slug,
                    "tour": show.tour or "",
                },
            )
        )

    for song in sorted(compendium.songs, key=lambda item: item.slug):
        records.append(
            ProvenanceRecord(
                entity_type="songs",
                key=song.slug,
                source_keys=_sources("gdshowsdb", "alex-allan-whitegum", "curated-seed"),
                confidence="entity-type",
                notes=note,
                metadata={"title": song.title},
            )
        )

    for venue in sorted(compendium.venues, key=lambda item: item.slug):
        records.append(
            ProvenanceRecord(
                entity_type="venues",
                key=venue.slug,
                source_keys=_sources("show-ingest", "venue-geo-sidecar"),
                confidence="entity-type",
                notes=note,
                metadata={
                    "name": venue.name,
                    "city": venue.city,
                    "region": venue.state_or_region,
                    "country": venue.country,
                },
            )
        )

    for perf in sorted(
        compendium.performances,
        key=lambda item: (item.show_slug, item.set_number, item.position, item.song_slug),
    ):
        key = f"{perf.show_slug}|{perf.set_number}|{perf.position}|{perf.song_slug}"
        records.append(
            ProvenanceRecord(
                entity_type="performances",
                key=key,
                source_keys=_sources("gdshowsdb-performances", "truckin-gap-fill"),
                confidence="entity-type",
                notes=note,
                metadata={
                    "show_slug": perf.show_slug,
                    "song_slug": perf.song_slug,
                    "set_number": str(perf.set_number),
                    "position": str(perf.position),
                    "segue_into": perf.segue_into or "",
                },
            )
        )

    for recording in sorted(compendium.recordings, key=lambda item: item.archive_id):
        records.append(
            ProvenanceRecord(
                entity_type="recordings",
                key=recording.archive_id,
                source_keys=_sources("internet-archive-lma", "curated-seed"),
                confidence="pointer",
                notes="Recording provenance is pointer-only; no audio is bundled.",
                metadata={
                    "show_slug": recording.show_slug,
                    "source_type": recording.source_type,
                    "url": recording.url,
                },
            )
        )

    for release in sorted(compendium.releases, key=lambda item: item.slug):
        records.append(
            ProvenanceRecord(
                entity_type="releases",
                key=release.slug,
                source_keys=_sources("wikipedia-discography", "curated-seed"),
                confidence="entity-type",
                notes=note,
                metadata={"title": release.title, "kind": release.kind},
            )
        )

    for citation in sorted(compendium.citations, key=lambda item: item.key):
        records.append(
            ProvenanceRecord(
                entity_type="citations",
                key=citation.key,
                source_keys=_sources("manuscript/references.bib", "bibliography-fetch"),
                confidence="bibliographic",
                notes="Citation rows point to bibliographic metadata only.",
                metadata={
                    "title": citation.title,
                    "kind": citation.kind,
                    "url": citation.url,
                    "year": "" if citation.year is None else str(citation.year),
                },
            )
        )

    for pointer in sorted(compendium.lyric_pointers, key=lambda item: item.song_slug):
        records.append(
            ProvenanceRecord(
                entity_type="lyric_pointers",
                key=pointer.song_slug,
                source_keys=_sources("cmu-lyrics-index", "dead.net", "curated-overlay"),
                confidence="pointer",
                notes="Lyric provenance is URL-only; lyric text is not bundled.",
                metadata={
                    "lyricist": pointer.lyricist,
                    "source_url": pointer.source_url,
                    "themes": ";".join(pointer.themes),
                },
            )
        )

    for review in sorted(
        compendium.reviews, key=lambda item: (item.show_slug, item.kind, item.author)
    ):
        key = f"{review.show_slug}|{review.kind}|{review.author}"
        records.append(
            ProvenanceRecord(
                entity_type="reviews",
                key=key,
                source_keys=_sources("maximinus", "curated-seed"),
                confidence="pointer",
                notes="Review provenance stores source URL and normalized sentiment only.",
                metadata={
                    "show_slug": review.show_slug,
                    "kind": review.kind,
                    "source_url": review.source_url,
                },
            )
        )

    for person in sorted(compendium.people, key=lambda item: item.slug):
        records.append(
            ProvenanceRecord(
                entity_type="people",
                key=person.slug,
                source_keys=_sources("dead.net", "wikipedia", "curated-seed"),
                confidence="entity-type",
                notes=note,
                metadata={"full_name": person.full_name},
            )
        )

    for edge in segue_edges(compendium):
        records.append(
            ProvenanceRecord(
                entity_type="segues",
                key=f"{edge.src}->{edge.dst}",
                source_keys=_sources("performance.segue_into", "computed-aggregate"),
                confidence="computed",
                notes="Segue provenance is derived from explicit source-marked segue fields.",
                metadata={"src": edge.src, "dst": edge.dst, "count": str(edge.count)},
            )
        )

    return tuple(sorted(records, key=lambda item: (item.entity_type, item.key)))


def lookup_provenance(
    records: Iterable[ProvenanceRecord], entity_type: str, key: str
) -> tuple[ProvenanceRecord, ...]:
    """Return provenance records matching ``entity_type`` and ``key``."""

    entity_type = entity_type.strip()
    key = key.strip()
    return tuple(
        record
        for record in records
        if record.entity_type == entity_type and record.key == key
    )


def write_provenance(compendium: Compendium, out_dir: Path) -> tuple[Path, Path]:
    """Write aggregate and per-entity provenance sidecars."""

    out_dir.mkdir(parents=True, exist_ok=True)
    records = provenance_records(compendium)
    fieldnames = (
        "entity_type",
        "key",
        "source_keys",
        "confidence",
        "notes",
        "metadata",
    )

    csv_path = out_dir / "provenance.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(record.to_csv_row() for record in records)

    by_type: dict[str, list[ProvenanceRecord]] = {}
    for record in records:
        by_type.setdefault(record.entity_type, []).append(record)
    for entity_type, entity_records in sorted(by_type.items()):
        path = out_dir / f"{entity_type}.csv"
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(record.to_csv_row() for record in entity_records)

    json_path = out_dir / "provenance.json"
    payload = {
        "schema": "grateful-data-provenance-v1",
        "record_count": len(records),
        "entity_type_counts": {
            entity_type: len(entity_records)
            for entity_type, entity_records in sorted(by_type.items())
        },
        "records": [record.to_dict() for record in records],
    }
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return csv_path, json_path
