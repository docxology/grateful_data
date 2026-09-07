#!/usr/bin/env python3
"""Run or dry-run the publication release-prep gate.

Thin orchestrator over :mod:`src.reporting.release_prep`.
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.reporting.release_prep import (  # noqa: E402
    build_steps,
    postprocess_html,
    resolve_template_root,
    run_step,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tier", default="archival", choices=["seed", "archival"])
    parser.add_argument("--template-root", type=Path, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--skip-pipeline", action="store_true")
    parser.add_argument("--skip-render", action="store_true")
    parser.add_argument("--skip-html-postprocess", action="store_true")
    parser.add_argument("--skip-validator", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    template_root = args.template_root or resolve_template_root()
    out_path = ROOT / "output" / "reports" / "release_prep.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    steps = build_steps(
        tier=args.tier,
        template_root=template_root,
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
        result = run_step(step)
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
