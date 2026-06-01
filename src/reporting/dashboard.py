"""HTML dashboard generation."""

from __future__ import annotations

import html
from pathlib import Path

from ..analysis import (
    composers,
    distributions,
    eras,
    first_principles,
    stats,
    timeseries,
)
from ..integration.reconcile import Compendium
from ..viz import style
from ..viz.figures import DASHBOARD_FIGURES, FIGURE_SPEC_BY_FILENAME


def _esc(value: object) -> str:
    return html.escape(str(value))


def _pretty_slug(slug: str) -> str:
    return slug.replace("_", " ").title()


def build_dashboard_html(
    comp: Compendium,
    *,
    figures_dir: Path | None = None,
    data_dir: Path | None = None,
) -> str:
    s = stats.compute(comp, top_n=20)
    py = timeseries.performances_per_year(comp)
    era_counts = eras.shows_by_era(comp)
    cs = composers.composer_song_counts(comp)
    perf_dist = distributions.performance_distribution(comp)
    song_conc = distributions.song_performance_concentration(comp)
    venue_conc = distributions.venue_show_concentration(comp)
    fp_review = first_principles.review_summary(comp)

    def data_links(name: str) -> str:
        if data_dir is None:
            return ""
        stem = name.removesuffix(".png")
        csv_path = data_dir / f"{stem}.csv"
        json_path = data_dir / f"{stem}.json"
        links: list[str] = []
        if csv_path.exists():
            links.append(f'<a href="data/figures/{stem}.csv">CSV</a>')
        if json_path.exists():
            links.append(f'<a href="data/figures/{stem}.json">JSON</a>')
        if not links:
            return ""
        return '<div class="dataLinks">Raw data: ' + " · ".join(links) + "</div>"

    def figure_card(
        name: str, *, title: str | None = None, alt: str | None = None
    ) -> str:
        spec = FIGURE_SPEC_BY_FILENAME.get(name)
        display_title = title or (spec.display_title if spec is not None else name)
        alt_text = alt or (
            spec.alt_text if spec is not None and spec.alt_text else display_title
        )
        hint = spec.caption_hint if spec is not None else ""
        metadata = ""
        if spec is not None:
            metadata = (
                '<dl class="figureMeta">'
                f"<div><dt>Statistic</dt><dd>{_esc(spec.statistic)}</dd></div>"
                f"<div><dt>Exclusion</dt><dd>{_esc(spec.exclusion_rule)}</dd></div>"
                f"<div><dt>Claim</dt><dd>{_esc(spec.claim_class)}</dd></div>"
                "</dl>"
            )
        return (
            f'<article class="figureCard"><h3>{_esc(display_title)}</h3>'
            f'<img src="figures/{name}" alt="{_esc(alt_text)}"/>'
            f"{f'<p>{_esc(hint)}</p>' if hint else ''}"
            f"{metadata}"
            f"{data_links(name)}</article>"
        )

    def section(title: str, intro: str, names: tuple[str, ...]) -> str:
        cards = "\n".join(
            figure_card(name)
            for name in names
            if figures_dir is None or (figures_dir / name).exists()
        )
        return (
            f'<section><div class="sectionHead"><h2>{_esc(title)}</h2>'
            f"<p>{_esc(intro)}</p></div>"
            f'<div class="figureGrid">{cards}</div></section>'
        )

    parts: list[str] = []
    parts.append(
        """<!doctype html>
<html><head><meta charset="utf-8"><title>The Music Never Stopped — Dashboard</title>
<style>
body{font-family:-apple-system,system-ui,Inter,sans-serif;margin:0;padding:0;background:#f8fafc;color:#111827}
a{color:#2563eb;text-decoration:none}
a:hover{text-decoration:underline}
.wrap{max-width:1240px;margin:0 auto;padding:28px}
header{border-bottom:1px solid #d1d5db;padding-bottom:18px;margin-bottom:24px}
h1{font-weight:800;margin:0 0 4px 0;letter-spacing:0}
.muted{color:#4b5563;max-width:900px;line-height:1.45}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-top:18px}
.kpiCell{background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:12px;text-align:center}
.kpi{font-size:1.45rem;font-weight:800;color:#92400e}
section{margin:30px 0 42px 0}
.sectionHead{display:grid;grid-template-columns:minmax(220px,320px) 1fr;gap:20px;align-items:end;border-bottom:1px solid #e5e7eb;margin-bottom:14px;padding-bottom:10px}
.sectionHead h2{margin:0;font-size:1.25rem}
.sectionHead p{margin:0;color:#4b5563;line-height:1.45}
.figureGrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:16px}
.figureCard,.tableCard,.methodCard{background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:14px;box-shadow:0 1px 2px rgba(15,23,42,.05)}
.figureCard h3,.tableCard h3,.methodCard h3{margin:0 0 10px 0;font-size:1rem;color:#1f2937}
.figureCard p,.methodCard p{font-size:.88rem;line-height:1.4;color:#4b5563;margin:9px 0 0 0}
.dataLinks{font-size:.82rem;margin-top:8px;color:#4b5563}
.figureMeta{display:grid;grid-template-columns:1fr;gap:4px;margin:9px 0 0 0;font-size:.78rem;color:#4b5563}
.figureMeta div{display:grid;grid-template-columns:74px 1fr;gap:6px}
.figureMeta dt{font-weight:700;color:#374151}
.figureMeta dd{margin:0}
img{width:100%;height:auto;display:block;border-radius:6px;border:1px solid #f3f4f6}
table{width:100%;border-collapse:collapse;font-size:.88rem}
th,td{padding:6px 8px;text-align:left;border-bottom:1px solid #e5e7eb;vertical-align:top}
th{color:#374151;background:#f9fafb}
small{color:#6b7280}
.split{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}
.methodStats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px;margin-top:10px}
.methodStats div{background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:10px}
.tableScroll{max-height:360px;overflow:auto}
</style></head>
<body><div class="wrap">
"""
    )
    parts.append("<header><h1>The Music Never Stopped</h1>")
    parts.append(
        f'<div class="muted">Grateful Data Compendium dashboard, generated from the {style.tier_phrase(comp)}. '
        "Panels are tied to the registry metadata and, where available, to raw CSV/JSON exports under output/data/figures.</div>"
    )
    parts.append('<div class="kpis">')
    for label, val in (
        ("Shows", s.n_shows),
        ("Songs", s.n_songs),
        ("People", s.n_people),
        ("Venues", s.n_venues),
        ("Performances", s.n_performances),
        ("Recordings", s.n_recordings),
        ("Releases", s.n_releases),
        ("Lyric Pointers", len(comp.lyric_pointers)),
        ("Reviews", len(comp.reviews)),
        ("Citations", s.n_citations),
    ):
        parts.append(
            f'<div class="kpiCell"><div class="kpi">{_esc(val)}</div><small>{_esc(label)}</small></div>'
        )
    parts.append("</div></header>")

    parts.append(
        '<section><div class="sectionHead"><h2>Overview</h2>'
        "<p>Scope, temporal coverage, and the compact publication mosaic for the selected tier.</p></div>"
        '<div class="split">'
        + figure_card(
            "mosaic.png",
            title="Total Mosaic",
            alt="Composite overview of compendium extent, analyses, category checks, and figure panels.",
        )
    )
    parts.append(
        '<article class="tableCard"><h3>Top songs</h3><table><tr><th>Song</th><th>Perf count</th></tr>'
    )
    for slug, count in s.top_songs[:15]:
        parts.append(
            f"<tr><td>{_esc(_pretty_slug(slug))}</td><td>{_esc(count)}</td></tr>"
        )
    parts.append("</table></article>")

    parts.append(
        '<article class="tableCard"><h3>Shows per year</h3><table><tr><th>Year</th><th>Shows</th><th>Performances</th></tr>'
    )
    for year in sorted(s.shows_per_year):
        parts.append(
            f"<tr><td>{year}</td><td>{s.shows_per_year[year]}</td><td>{py.get(year, 0)}</td></tr>"
        )
    parts.append("</table></article></div></section>")

    parts.append(
        '<section><div class="sectionHead"><h2>Statistical Shape</h2>'
        "<p>Descriptive distributions, concentration curves, bootstrap intervals, and exploratory repertoire structure. These panels are pattern-discovery aids, not causal claims.</p></div>"
        '<div class="methodCard"><h3>Method Notes</h3><p>'
        f"Performance rows/show: median {perf_dist.per_show.median:g}, p90 {perf_dist.per_show.p90:g}, "
        f"empty shows {perf_dist.n_zero_performance_shows}. "
        f"Song concentration: Gini {song_conc.gini:.2f}, top decile {song_conc.top_10_share_pct:.0f}%. "
        f"Venue concentration: Gini {venue_conc.gini:.2f}, top decile {venue_conc.top_10_share_pct:.0f}%."
        "</p></div>"
        '<div class="figureGrid">'
    )
    for name in (
        "performance_distribution.png",
        "repertoire_concentration.png",
        "venue_concentration.png",
        "concentration_uncertainty.png",
        "repertoire_topn_sensitivity.png",
        "repertoire_embedding.png",
        "era_repertoire_heatmap.png",
    ):
        if figures_dir is None or (figures_dir / name).exists():
            parts.append(figure_card(name))
    parts.append("</div></section>")

    parts.append(
        section(
            "Repertoire/Transitions",
            "Frequency, association, first-order transition, stationary, centrality, and explicit segue views over setlist metadata.",
            (
                "top_songs.png",
                "cooccurrence_heatmap.png",
                "transition_matrix.png",
                "transition_sensitivity.png",
                "stationary_top20.png",
                "centrality_top20.png",
                "segue_graph.png",
            ),
        )
    )

    parts.append(
        section(
            "Geography",
            "Venue concentration, geocoded venue coverage, and era-level temporal grouping.",
            (
                "geo_scatter.png",
                "venue_concentration.png",
                "venue_identity_review.png",
                "shows_by_era.png",
            ),
        )
    )

    parts.append(
        '<section><div class="sectionHead"><h2>Evidence</h2>'
        "<p>Source mix, overlays, personnel intervals, release records, curated review/lyric-pointer dimensions, and first-principles claim boundaries.</p></div>"
        '<div class="methodCard"><h3>First-Principles Review</h3><p>'
        f"{fp_review['n_claim_areas']} claim families are classified by hard constraints, assumptions, validation artifacts, and limits. "
        f"The ledger names {fp_review['n_hard_constraints']} hard constraints and {fp_review['n_validation_artifacts']} validation artifacts."
        "</p></div>"
        '<div class="split"><article class="tableCard"><h3>Claim ledger</h3><div class="tableScroll">'
        "<table><tr><th>Claim</th><th>Status</th><th>Section</th><th>Test</th></tr>"
    )
    for row in fp_review["rows"]:
        parts.append(
            "<tr>"
            f"<td>{_esc(row['claim_area'])}</td>"
            f"<td>{_esc(row['claim_status'])}</td>"
            f"<td>{_esc(row['manuscript_section'])}</td>"
            f"<td>{_esc(row['test_file'])}</td>"
            "</tr>"
        )
    parts.append("</table></div></article>")
    if figures_dir is None or (figures_dir / "claim_evidence_matrix.png").exists():
        parts.append(figure_card("claim_evidence_matrix.png"))
    parts.append("</div>")
    parts.append(
        '<div class="split"><article class="tableCard"><h3>Composer credits</h3><table><tr><th>Composer</th><th>Songs</th></tr>'
    )
    for name, count in list(cs.items())[:15]:
        parts.append(f"<tr><td>{_esc(name)}</td><td>{count}</td></tr>")
    parts.append("</table></article>")

    parts.append(
        '<article class="tableCard"><h3>Shows by era</h3><table><tr><th>Era</th><th>Shows</th></tr>'
    )
    for era, count in era_counts.items():
        parts.append(f"<tr><td>{_esc(era)}</td><td>{count}</td></tr>")
    parts.append('</table></article></div><div class="figureGrid">')
    for name in (
        "composer_attribution.png",
        "era_density.png",
        "personnel_gantt.png",
        "lineup_diversity.png",
        "sentiment_by_kind.png",
        "citation_kinds.png",
        "recording_sources.png",
        "lyric_themes.png",
        "set_positions.png",
        "tours_top.png",
        "bustouts.png",
        "song_lifespans.png",
        "releases_timeline.png",
        "context_timeline.png",
    ):
        if figures_dir is None or (figures_dir / name).exists():
            parts.append(figure_card(name))
    parts.append("</div>")

    parts.append(
        '<div class="split"><article class="tableCard"><h3>Releases</h3><table><tr><th>Title</th><th>Date</th><th>Kind</th></tr>'
    )
    for release in comp.releases:
        parts.append(
            f"<tr><td>{_esc(release.title)}</td><td>{release.release_date.isoformat()}</td>"
            f"<td>{_esc(release.kind)}</td></tr>"
        )
    parts.append("</table></article>")

    parts.append(
        '<article class="tableCard"><h3>Citations</h3><table><tr><th>Key</th><th>Kind</th><th>Title</th></tr>'
    )
    for citation in comp.citations:
        parts.append(
            f"<tr><td>{_esc(citation.key)}</td><td>{_esc(citation.kind)}</td>"
            f'<td><a href="{_esc(citation.url)}">{_esc(citation.title)}</a></td></tr>'
        )
    parts.append("</table></article></div></section>")

    figure_names = DASHBOARD_FIGURES
    if figures_dir is not None:
        figure_names = tuple(
            name for name in DASHBOARD_FIGURES if (figures_dir / name).exists()
        )
    documented = {
        "mosaic.png",
        "performance_distribution.png",
        "repertoire_concentration.png",
        "venue_concentration.png",
        "concentration_uncertainty.png",
        "repertoire_embedding.png",
        "era_repertoire_heatmap.png",
        "top_songs.png",
        "cooccurrence_heatmap.png",
        "transition_matrix.png",
        "stationary_top20.png",
        "centrality_top20.png",
        "segue_graph.png",
        "geo_scatter.png",
        "shows_by_era.png",
        "claim_evidence_matrix.png",
        "composer_attribution.png",
        "era_density.png",
        "personnel_gantt.png",
        "lineup_diversity.png",
        "sentiment_by_kind.png",
        "citation_kinds.png",
        "recording_sources.png",
        "lyric_themes.png",
        "set_positions.png",
        "tours_top.png",
        "bustouts.png",
        "song_lifespans.png",
        "releases_timeline.png",
        "context_timeline.png",
    }
    remaining = tuple(name for name in figure_names if name not in documented)
    if remaining:
        parts.append(
            section(
                "Additional Registered Figures",
                "Registry-backed panels not already shown above.",
                remaining,
            )
        )

    parts.append("</div></body></html>")
    return "\n".join(parts)


def write_dashboard(comp: Compendium, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html_text = build_dashboard_html(
        comp,
        figures_dir=out_path.parent / "figures",
        data_dir=out_path.parent / "data" / "figures",
    )
    out_path.write_text(html_text, encoding="utf-8")
    return out_path
