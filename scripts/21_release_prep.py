#!/usr/bin/env python3
"""Run or dry-run the publication release-prep gate."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()
DEFAULT_TEMPLATE_ROOT = Path("/Users/4d/Documents/GitHub/template")


@dataclass(frozen=True)
class Step:
    name: str
    command: tuple[str, ...] | None
    cwd: Path
    env: dict[str, str]

    def to_plan_row(self) -> dict[str, object]:
        return {
            "name": self.name,
            "command": list(self.command) if self.command else None,
            "cwd": str(self.cwd),
            "env": self.env,
        }


def postprocess_html(root: Path = ROOT) -> dict[str, object]:
    """Inject stable navigation links into rendered web output."""

    index_path = root / "output" / "web" / "index.html"
    if not index_path.is_file():
        return {"ok": False, "path": str(index_path), "changed": False, "reason": "missing"}
    changed_files: list[str] = []
    citation_re = re.compile(
        r'(<span\b(?=[^>]*\bclass="citation")(?=[^>]*\bdata-cites="([^"]+)")[^>]*>)\[@([^<]+)\](</span>)'
    )

    def normalize_citations(path: Path) -> bool:
        text = path.read_text(encoding="utf-8")

        def repl(match: re.Match[str]) -> str:
            prefix, cites, _raw, suffix = match.groups()
            label = "; ".join(cites.split())
            return f"{prefix}[{label}]{suffix}"

        new_text = citation_re.sub(repl, text)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            return True
        return False

    for path in sorted((root / "output" / "web").glob("*.html")):
        if normalize_citations(path):
            changed_files.append(str(path))

    text = index_path.read_text(encoding="utf-8")
    marker = "<!-- grateful-data-release-links -->"
    block = (
        f"{marker}\n"
        '<nav class="grateful-data-release-links" aria-label="Publication artifacts">\n'
        '  <a href="../dashboard.html">Dashboard</a>\n'
        '  <a href="../explorer/index.html">Static Explorer</a>\n'
        '  <a href="../pdf/grateful_data_combined.pdf">Combined PDF</a>\n'
        "</nav>\n"
    )
    css = (
        "<style>\n"
        ".grateful-data-release-links{display:flex;gap:12px;flex-wrap:wrap;"
        "padding:12px 16px;margin:12px 0;border:1px solid #d8dee9;"
        "border-radius:6px;background:#f8fafc;font-family:system-ui,sans-serif}\n"
        ".grateful-data-release-links a{color:#1d4ed8;text-decoration:none;font-weight:600}\n"
        "</style>\n"
    )
    changed = False
    if marker not in text:
        if "</head>" in text:
            text = text.replace("</head>", css + "</head>", 1)
        if "<body>" in text:
            text = text.replace("<body>", "<body>\n" + block, 1)
            changed = True
        elif "</body>" in text:
            text = text.replace("</body>", block + "</body>", 1)
            changed = True
    if changed:
        index_path.write_text(text, encoding="utf-8")
        changed_files.append(str(index_path))
    return {
        "ok": True,
        "path": str(index_path),
        "changed": bool(changed_files),
        "changed_files": changed_files,
    }


def _run_step(step: Step) -> dict[str, object]:
    assert step.command is not None
    env = os.environ.copy()
    env.update(step.env)
    proc = subprocess.run(
        list(step.command),
        cwd=step.cwd,
        env=env,
        capture_output=True,
        text=True,
    )
    return {
        "name": step.name,
        "command": list(step.command),
        "cwd": str(step.cwd),
        "returncode": proc.returncode,
        "ok": proc.returncode == 0,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def build_steps(
    *,
    tier: str,
    template_root: Path,
    skip_tests: bool,
    skip_pipeline: bool,
    skip_render: bool,
    skip_validator: bool,
) -> list[Step]:
    env = {"GRATEFUL_DATA_TIER": tier}
    steps: list[Step] = []
    if not skip_tests:
        steps.append(
            Step(
                "tests",
                ("uv", "run", "pytest", "tests/", "--cov=src", "--cov-fail-under=90"),
                ROOT,
                env,
            )
        )
    if not skip_pipeline:
        steps.append(
            Step(
                "archival_pipeline",
                ("uv", "run", "python", "scripts/99_pipeline.py", "--tier", tier),
                ROOT,
                env,
            )
        )
    if not skip_render:
        steps.append(
            Step(
                "template_render",
                ("uv", "run", "python", "scripts/03_render_pdf.py", "--project", "grateful_data"),
                template_root,
                env,
            )
        )
    if not skip_validator:
        steps.append(
            Step(
                "publication_validator",
                ("uv", "run", "python", "scripts/20_validate_publication_outputs.py", "--strict"),
                ROOT,
                env,
            )
        )
    return steps


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", default="archival", choices=["seed", "archival"])
    parser.add_argument("--template-root", type=Path, default=DEFAULT_TEMPLATE_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-pipeline", action="store_true")
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--skip-html-postprocess", action="store_true")
    parser.add_argument("--skip-validator", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    out_path = ROOT / "output" / "reports" / "release_prep.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    steps = build_steps(
        tier=args.tier,
        template_root=args.template_root,
        skip_tests=args.skip_tests,
        skip_pipeline=args.skip_pipeline,
        skip_render=args.skip_render,
        skip_validator=args.skip_validator,
    )
    if args.dry_run:
        payload = {
            "schema": "grateful-data-release-prep-v1",
            "dry_run": True,
            "all_ok": True,
            "steps": [step.to_plan_row() for step in steps],
            "html_postprocess": {
                "planned": not args.skip_html_postprocess,
                "path": str(ROOT / "output" / "web" / "index.html"),
            },
        }
        with out_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print(out_path)
        return 0

    results: list[dict[str, object]] = []
    for step in steps:
        if step.name == "publication_validator" and not args.skip_html_postprocess:
            results.append({"name": "html_postprocess", **postprocess_html(ROOT)})
        result = _run_step(step)
        results.append(result)
        if not result["ok"]:
            break
    if not args.skip_html_postprocess and not any(
        result.get("name") == "html_postprocess" for result in results
    ):
        results.append({"name": "html_postprocess", **postprocess_html(ROOT)})
    payload = {
        "schema": "grateful-data-release-prep-v1",
        "dry_run": False,
        "all_ok": all(bool(result.get("ok")) for result in results),
        "steps": results,
    }
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(out_path)
    print(f"all_ok={payload['all_ok']}")
    return 0 if payload["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
