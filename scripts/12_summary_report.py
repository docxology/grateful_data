#!/usr/bin/env python3
"""Write output/SUMMARY.md — one-page extent report from live computation."""

from __future__ import annotations

from _bootstrap import ensure_project_root

ROOT = ensure_project_root()

from src.analysis import composers, eras, stats, timeseries, tours  # noqa: E402
from src.cattheory.functors import (  # noqa: E402
    active_lineup_presheaf,
    is_monotone,
    lineup_functor,
    setlist_functor,
)
from src.honesty import HonestyBoundary  # noqa: E402
from src.seed import load_seed_compendium  # noqa: E402
from src.tier import resolve_seed_dir  # noqa: E402
from src.validation import validate_seed  # noqa: E402


def main() -> None:
    comp = load_seed_compendium()
    tier = resolve_seed_dir().name
    s = stats.compute(comp, top_n=15)
    boundary = HonestyBoundary()
    honesty_violations = boundary.check_compendium(comp)
    seed_violations = validate_seed()
    F_set = setlist_functor(comp)
    F_lin = lineup_functor(comp)
    P_act = active_lineup_presheaf(comp)

    lines: list[str] = [
        "# The Music Never Stopped — Summary",
        "",
        f"Auto-generated from the {tier} compendium by `scripts/12_summary_report.py`.",
        "Re-run after any change to refresh.",
        "",
        "## Extent",
        "",
        "| Layer | Count |",
        "| --- | --- |",
        f"| Shows | {s.n_shows} |",
        f"| Performances | {s.n_performances} |",
        f"| Songs | {s.n_songs} |",
        f"| Personnel | {s.n_people} |",
        f"| Venues | {s.n_venues} |",
        f"| Recordings | {s.n_recordings} |",
        f"| Releases | {s.n_releases} |",
        f"| Lyric pointers | {len(comp.lyric_pointers)} |",
        f"| Reviews | {len(comp.reviews)} |",
        f"| Citations | {s.n_citations} |",
        f"| Tours | {len(tours.shows_per_tour(comp))} |",
        "",
        "## Gates",
        "",
        f"- **Honesty boundary:** {'PASS' if not honesty_violations else 'FAIL'} "
        f"({len(honesty_violations)} violations)",
        f"- **Seed schema validation:** {'PASS' if not seed_violations else 'FAIL'} "
        f"({len(seed_violations)} violations)",
        f"- **Setlist functor monotone:** {is_monotone(F_set)}",
        f"- **Lineup functor monotone:** {is_monotone(F_lin)}",
        f"- **Active-lineup presheaf monotone:** {is_monotone(P_act)} (expected `False`)",
        "",
        "## Top composers (by song count)",
        "",
    ]
    for name, n in list(composers.composer_song_counts(comp).items())[:10]:
        lines.append(f"- {name}: {n}")
    lines.append("")
    lines.append("## Shows per year")
    lines.append("")
    py = timeseries.performances_per_year(comp)
    for year in sorted(s.shows_per_year):
        lines.append(
            f"- {year}: {s.shows_per_year[year]} shows, {py.get(year, 0)} performances"
        )
    lines.append("")
    lines.append("## Top songs (seed)")
    lines.append("")
    for slug, c in s.top_songs:
        lines.append(f"- `{slug}` ({c})")
    lines.append("")
    lines.append("## Era breakdown")
    lines.append("")
    for era, count in eras.shows_by_era(comp).items():
        lines.append(f"- {era}: {count} shows")
    lines.append("")
    lines.append("## Output index")
    lines.append("")
    lines.append("- [Total mosaic](figures/mosaic.png)")
    lines.append("- [HTML dashboard](dashboard.html)")
    lines.append("- [Per-song pages](songs/_index.md)")
    lines.append("- [Per-era pages](eras/_index.md)")
    lines.append("- [Per-venue pages](venues/_index.md)")
    lines.append("- [Per-person pages](people/_index.md)")
    out = ROOT / "output" / "SUMMARY.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
