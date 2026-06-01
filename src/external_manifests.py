"""Pointer-only external media and lyric manifests."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

from .integration.reconcile import Compendium

ALLOWED_KINDS = frozenset({"audio", "lyrics"})
FORBIDDEN_POINTER_FIELDS = frozenset(
    {
        "audio",
        "audio_bytes",
        "audio_file",
        "audio_path",
        "derived_text",
        "excerpt",
        "lyric",
        "lyric_text",
        "lyrics",
        "local_path",
        "transcript",
        "waveform",
    }
)


@dataclass(frozen=True)
class ExternalPointer:
    """A protected-content-safe pointer row."""

    kind: str
    key: str
    url: str
    content_hash: str = ""
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_external_pointer(self)

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "key": self.key,
            "url": self.url,
            "content_hash": self.content_hash,
            "metadata": dict(sorted(self.metadata.items())),
        }

    def to_csv_row(self) -> dict[str, str]:
        return {
            "kind": self.kind,
            "key": self.key,
            "url": self.url,
            "content_hash": self.content_hash,
            "metadata": json.dumps(dict(sorted(self.metadata.items())), sort_keys=True),
        }


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_external_pointer(pointer: ExternalPointer) -> None:
    """Reject bundled protected content and non-pointer rows."""

    if pointer.kind not in ALLOWED_KINDS:
        raise ValueError(f"unsupported external pointer kind: {pointer.kind!r}")
    if not pointer.key.strip():
        raise ValueError("external pointer key must be non-empty")
    if not _is_http_url(pointer.url):
        raise ValueError("external pointer url must be http(s)")
    for field_name, value in pointer.metadata.items():
        lowered = field_name.casefold().strip()
        if lowered in FORBIDDEN_POINTER_FIELDS:
            raise ValueError(f"forbidden protected-content field: {field_name}")
        if lowered.endswith("_text") or lowered.endswith("_path"):
            raise ValueError(f"forbidden protected-content field: {field_name}")
        if isinstance(value, str) and "\n" in value:
            raise ValueError("external pointer metadata must be compact metadata, not excerpts")


def default_external_pointers(compendium: Compendium) -> tuple[ExternalPointer, ...]:
    """Build safe audio and lyric URL manifests from existing metadata."""

    pointers: list[ExternalPointer] = []
    for recording in sorted(compendium.recordings, key=lambda item: item.archive_id):
        if not recording.url:
            continue
        pointers.append(
            ExternalPointer(
                kind="audio",
                key=recording.archive_id,
                url=recording.url,
                metadata={
                    "show_slug": recording.show_slug,
                    "source_type": recording.source_type,
                    "policy": "pointer-only-no-audio-bundled",
                },
            )
        )
    for lyric_pointer in sorted(
        compendium.lyric_pointers, key=lambda item: item.song_slug
    ):
        if not lyric_pointer.source_url:
            continue
        pointers.append(
            ExternalPointer(
                kind="lyrics",
                key=lyric_pointer.song_slug,
                url=lyric_pointer.source_url,
                metadata={
                    "lyricist": lyric_pointer.lyricist,
                    "themes": ";".join(lyric_pointer.themes),
                    "policy": "pointer-only-no-lyric-text-bundled",
                },
            )
        )
    return tuple(sorted(pointers, key=lambda item: (item.kind, item.key, item.url)))


def write_external_manifests(
    compendium: Compendium, out_dir: Path
) -> tuple[Path, Path, Path]:
    """Write audio and lyric pointer-only manifests plus a summary."""

    out_dir.mkdir(parents=True, exist_ok=True)
    pointers = default_external_pointers(compendium)
    fieldnames = ("kind", "key", "url", "content_hash", "metadata")
    paths: dict[str, Path] = {}
    for kind in sorted(ALLOWED_KINDS):
        kind_pointers = [pointer for pointer in pointers if pointer.kind == kind]
        csv_path = out_dir / f"{kind}_pointers.csv"
        json_path = out_dir / f"{kind}_pointers.json"
        with csv_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(pointer.to_csv_row() for pointer in kind_pointers)
        with json_path.open("w", encoding="utf-8") as fh:
            json.dump(
                [pointer.to_dict() for pointer in kind_pointers],
                fh,
                indent=2,
                sort_keys=True,
            )
            fh.write("\n")
        paths[kind] = json_path

    contract_path = out_dir / "pipeline_contract.json"
    contract = {
        "schema": "grateful-data-external-pipeline-contract-v1",
        "scope": "Future external audio or lyric analysis must remain pointer-only in this repository.",
        "allowed_inputs": [
            "http(s) URLs",
            "source identifiers",
            "optional cryptographic hashes",
            "compact non-excerpt metadata",
        ],
        "allowed_outputs": [
            "aggregate numeric metadata",
            "source coverage counts",
            "hash manifests",
            "diagnostic logs without protected excerpts",
        ],
        "forbidden_outputs": sorted(FORBIDDEN_POINTER_FIELDS),
        "audio_feature_pipeline": [
            "Resolve URL outside the repository.",
            "Verify hash when a hash is present.",
            "Compute external features in a user-controlled cache.",
            "Export only aggregate metadata and reproducibility pointers.",
        ],
        "lyric_annotation_pipeline": [
            "Resolve lyric URL outside the repository.",
            "Annotate externally without writing lyric text back to this repo.",
            "Export only controlled vocabulary labels, counts, and provenance pointers.",
        ],
    }
    with contract_path.open("w", encoding="utf-8") as fh:
        json.dump(contract, fh, indent=2, sort_keys=True)
        fh.write("\n")

    summary_path = out_dir / "external_manifest_summary.json"
    payload = {
        "schema": "grateful-data-external-pointer-manifest-v1",
        "policy": "Pointer metadata only. Bundled audio, lyric text, transcripts, excerpts, and derived text are rejected.",
        "counts": {
            kind: sum(1 for pointer in pointers if pointer.kind == kind)
            for kind in sorted(ALLOWED_KINDS)
        },
        "files": {
            **{kind: str(path) for kind, path in sorted(paths.items())},
            "pipeline_contract": str(contract_path),
        },
    }
    with summary_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return paths["audio"], paths["lyrics"], summary_path
