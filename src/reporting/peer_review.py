"""Peer-review dossier linking claims to evidence artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from ..analysis.first_principles import review_summary
from ..integration.reconcile import Compendium


def build_peer_review_dossier(
    compendium: Compendium,
    *,
    reports_dir: Path,
    figures_dir: Path,
    output_dir: Path,
) -> dict[str, object]:
    """Map each claim family to code, reports, tests, figures, and artifacts."""

    rows = review_summary(compendium)["rows"]
    citation_keys = sorted(citation.key for citation in compendium.citations)
    artifact_status: list[dict[str, object]] = []
    for row in rows:
        figure_name = str(row["figure_filename"])
        report_key = str(row["report_key"]).split("::", 1)[0]
        figure_exists = figure_name != "not-applicable" and (figures_dir / figure_name).is_file()
        report_exists = (reports_dir / report_key).is_file() if report_key.endswith(".json") else True
        artifact_status.append(
            {
                "claim_area": row["claim_area"],
                "claim_status": row["claim_status"],
                "manuscript_section": row["manuscript_section"],
                "figure_filename": figure_name,
                "figure_exists": figure_exists,
                "report_key": row["report_key"],
                "report_exists": report_exists,
                "test_file": row["test_file"],
                "validation_artifact": row["validation_artifact"],
                "interpretation_limit": row["interpretation_limit"],
            }
        )
    return {
        "schema": "grateful-data-peer-review-dossier-v1",
        "claim_count": len(rows),
        "citation_count": len(citation_keys),
        "citation_keys": citation_keys,
        "artifact_roots": {
            "reports": str(reports_dir),
            "figures": str(figures_dir),
            "output": str(output_dir),
        },
        "claims": artifact_status,
        "review_note": "Dossier maps claim families to available artifacts; it is a reviewer navigation aid, not a replacement for tests.",
    }


def render_peer_review_markdown(payload: dict[str, object]) -> str:
    """Render a compact Markdown dossier."""

    lines = [
        "# Grateful Data Peer-Review Dossier",
        "",
        str(payload["review_note"]),
        "",
        f"- Claim families: {payload['claim_count']}",
        f"- Citation keys: {payload['citation_count']}",
        "",
        "| Claim | Status | Section | Figure | Report/Test | Limit |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for claim in payload["claims"]:  # type: ignore[index]
        figure = claim["figure_filename"]
        if claim["figure_exists"]:
            figure = f"{figure} (present)"
        elif figure != "not-applicable":
            figure = f"{figure} (missing)"
        report_test = f"{claim['report_key']} / {claim['test_file']}"
        lines.append(
            "| "
            + " | ".join(
                str(value).replace("|", "\\|")
                for value in (
                    claim["claim_area"],
                    claim["claim_status"],
                    claim["manuscript_section"],
                    figure,
                    report_test,
                    claim["interpretation_limit"],
                )
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def write_peer_review_dossier(
    compendium: Compendium, output_dir: Path, *, reports_dir: Path, figures_dir: Path
) -> tuple[Path, Path]:
    """Write JSON and Markdown peer-review dossier files."""

    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_peer_review_dossier(
        compendium,
        reports_dir=reports_dir,
        figures_dir=figures_dir,
        output_dir=output_dir,
    )
    json_path = output_dir / "peer_review_dossier.json"
    markdown_path = output_dir / "peer_review_dossier.md"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    markdown_path.write_text(render_peer_review_markdown(payload), encoding="utf-8")
    return json_path, markdown_path
