#!/usr/bin/env python3
"""Validate publication-facing outputs and raw-data links."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.viz.figures import DASHBOARD_FIGURES, FIGURE_SPECS  # noqa: E402


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


def _read_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} did not contain a JSON object")
    return data


def _text_files(root: Path, patterns: tuple[str, ...]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(path for path in root.glob(pattern) if path.is_file())
    return sorted(set(paths))


def _files_without_pattern(
    files: list[Path], pattern: str, *, flags: int = 0
) -> tuple[bool, str]:
    regex = re.compile(pattern, flags)
    hits: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        if regex.search(text):
            hits.append(str(path))
    return not hits, ", ".join(hits[:10])


def _check_exists(name: str, path: Path) -> CheckResult:
    return CheckResult(name=name, ok=path.is_file(), detail=str(path))


def validate_publication_outputs(root: Path = ROOT) -> dict[str, object]:
    """Return a JSON-serializable validation report."""

    output = root / "output"
    reports = output / "reports"
    checks: list[CheckResult] = [
        _check_exists("combined_pdf_exists", output / "pdf" / "grateful_data_combined.pdf"),
        _check_exists("web_index_exists", output / "web" / "index.html"),
        _check_exists("dashboard_exists", output / "dashboard.html"),
        _check_exists("figure_validation_exists", reports / "figure_validation.json"),
        _check_exists("completeness_report_exists", reports / "completeness_report.json"),
        _check_exists("figure_data_index_exists", output / "data" / "figures" / "index.json"),
        _check_exists("first_principles_report_exists", reports / "first_principles_review.json"),
        _check_exists("provenance_sidecar_exists", output / "data" / "provenance" / "provenance.json"),
        _check_exists("external_manifest_summary_exists", output / "data" / "external" / "external_manifest_summary.json"),
        _check_exists("external_pipeline_contract_exists", output / "data" / "external" / "pipeline_contract.json"),
        _check_exists("explorer_exists", output / "explorer" / "index.html"),
        _check_exists("peer_review_dossier_exists", reports / "peer_review_dossier.json"),
    ]

    text_files = _text_files(
        output,
        (
            "manuscript/*.md",
            "web/*.html",
            "dashboard.html",
            "explorer/*.html",
        ),
    )
    ok, detail = _files_without_pattern(text_files, r"\{\{[A-Z0-9_]+\}\}")
    checks.append(
        CheckResult(
            "no_unresolved_tokens",
            ok,
            detail=detail or f"scanned {len(text_files)} text files",
        )
    )
    rendered_files = _text_files(output, ("web/*.html", "dashboard.html", "explorer/*.html"))
    ok, detail = _files_without_pattern(rendered_files, r"\[@[A-Za-z0-9_:-]+\]")
    checks.append(
        CheckResult(
            "no_raw_markdown_citations_in_rendered_outputs",
            ok,
            detail=detail or f"scanned {len(rendered_files)} rendered files",
        )
    )

    figure_validation_path = reports / "figure_validation.json"
    if figure_validation_path.is_file():
        payload = _read_json(figure_validation_path)
        checks.append(
            CheckResult(
                "figure_validation_all_ok",
                bool(payload.get("all_ok")),
                f"n_ok={payload.get('n_ok')} n_figures={payload.get('n_figures')}",
            )
        )

    completeness_path = reports / "completeness_report.json"
    if completeness_path.is_file():
        payload = _read_json(completeness_path)
        checks.append(
            CheckResult(
                "completeness_dangling_total_zero",
                payload.get("dangling_total") == 0,
                f"dangling_total={payload.get('dangling_total')}",
            )
        )

    data_dir = output / "data" / "figures"
    index_path = data_dir / "index.json"
    if index_path.is_file():
        payload = _read_json(index_path)
        datasets = payload.get("datasets") or []
        index_by_figure = {
            str(row.get("figure")): row
            for row in datasets
            if isinstance(row, dict) and row.get("figure")
        }
        expected_dataset_figures = {
            spec.filename for spec in FIGURE_SPECS if spec.dataset is not None
        }
        missing_index = sorted(expected_dataset_figures - set(index_by_figure))
        checks.append(
            CheckResult(
                "figure_data_index_complete",
                not missing_index,
                f"missing={missing_index[:10]} expected={len(expected_dataset_figures)} indexed={len(index_by_figure)}",
            )
        )
        missing_files: list[str] = []
        missing_doc_fields: list[str] = []
        for row in index_by_figure.values():
            csv_name = str(row.get("csv", ""))
            json_name = str(row.get("json", ""))
            if not (data_dir / csv_name).is_file():
                missing_files.append(csv_name)
            if not (data_dir / json_name).is_file():
                missing_files.append(json_name)
            for field in (
                "alt_text",
                "caption_hint",
                "data_source",
                "statistic",
                "exclusion_rule",
                "claim_class",
            ):
                if not str(row.get(field, "")).strip():
                    missing_doc_fields.append(f"{row.get('figure')}:{field}")
        checks.append(
            CheckResult(
                "figure_data_files_exist",
                not missing_files,
                f"missing={missing_files[:10]}",
            )
        )
        checks.append(
            CheckResult(
                "figure_data_index_documentation_complete",
                not missing_doc_fields,
                f"missing={missing_doc_fields[:12]}",
            )
        )
        dashboard_path = output / "dashboard.html"
        if dashboard_path.is_file():
            dashboard_html = dashboard_path.read_text(encoding="utf-8", errors="ignore")
            missing_links: list[str] = []
            dashboard_dataset_figures = {
                filename
                for filename in DASHBOARD_FIGURES
                if filename in expected_dataset_figures
            }
            for filename in sorted(dashboard_dataset_figures):
                stem = filename.removesuffix(".png")
                for suffix in ("csv", "json"):
                    link = f"data/figures/{stem}.{suffix}"
                    if link not in dashboard_html:
                        missing_links.append(link)
            checks.append(
                CheckResult(
                    "dashboard_raw_data_links_complete",
                    not missing_links,
                    f"missing={missing_links[:12]}",
                )
            )

    pdf_log = output / "pdf" / "_combined_manuscript.log"
    if pdf_log.is_file():
        text = pdf_log.read_text(encoding="utf-8", errors="ignore")
        bad_patterns = (
            "Undefined control sequence",
            "Citation `",
            "Reference `",
            "There were undefined references",
            "undefined citations",
        )
        hits = [pattern for pattern in bad_patterns if pattern in text]
        checks.append(
            CheckResult(
                "pdf_log_no_unresolved_latex",
                not hits,
                f"hits={hits}",
            )
        )

    all_ok = all(check.ok for check in checks)
    return {
        "schema": "grateful-data-publication-validation-v1",
        "all_ok": all_ok,
        "n_checks": len(checks),
        "n_failed": sum(1 for check in checks if not check.ok),
        "checks": [check.to_dict() for check in checks],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on failure.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = validate_publication_outputs(ROOT)
    out_path = ROOT / "output" / "reports" / "publication_validation.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(out_path)
    print(f"all_ok={report['all_ok']} n_failed={report['n_failed']}")
    return 1 if args.strict and not report["all_ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
