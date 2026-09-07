"""Release-prep gate: step plan, subprocess runner, and HTML postprocess.

Moved verbatim from ``scripts/21_release_prep.py`` so the gate logic is
importable and testable; the script is a thin wrapper around these pieces.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from src.reporting.manuscript import find_template_root

ROOT = Path(__file__).resolve().parents[2]


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


def resolve_template_root() -> Path:
    """Locate the template repo root (``TEMPLATE_REPO_ROOT`` or ancestor walk)."""
    return find_template_root(ROOT)


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


def run_step(step: Step) -> dict[str, object]:
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
