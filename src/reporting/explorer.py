"""Generate a small static explorer from exported JSON data."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from ..analysis.first_principles import review_summary
from ..analysis.segues import segue_edges
from ..integration.reconcile import Compendium
from ..provenance import provenance_records
from ..viz.figures import FIGURE_SPECS


def explorer_payload(compendium: Compendium) -> dict[str, object]:
    """Return the JSON payload consumed by the static explorer."""

    song_titles = {song.slug: song.title for song in compendium.songs}
    venue_by_slug = {venue.slug: venue for venue in compendium.venues}
    provenance = provenance_records(compendium)
    claim_rows = review_summary(compendium)["rows"]
    return {
        "schema": "grateful-data-static-explorer-v3",
        "summary": {
            "shows": len(compendium.shows),
            "songs": len(compendium.songs),
            "venues": len(compendium.venues),
            "performances": len(compendium.performances),
            "segues": sum(1 for perf in compendium.performances if perf.segue_into),
            "claim_rows": len(claim_rows),
            "provenance_records": len(provenance),
            "figures": len(FIGURE_SPECS),
        },
        "figures": [
            {
                "figure": spec.filename,
                "title": spec.display_title,
                "claim_class": spec.claim_class,
                "statistic": spec.statistic,
                "exclusion_rule": spec.exclusion_rule,
                "raw_csv": f"../data/figures/{spec.filename.removesuffix('.png')}.csv",
                "raw_json": f"../data/figures/{spec.filename.removesuffix('.png')}.json",
            }
            for spec in FIGURE_SPECS
        ],
        "shows": [
            {
                "slug": show.slug,
                "date": show.date.isoformat(),
                "venue_slug": show.venue_slug,
                "venue": venue_by_slug[show.venue_slug].name
                if show.venue_slug in venue_by_slug
                else show.venue_slug,
                "tour": show.tour or "",
                "related_venue": show.venue_slug,
                "related_provenance": f"shows:{show.slug}",
            }
            for show in sorted(compendium.shows, key=lambda item: item.slug)
        ],
        "songs": [
            {
                "slug": song.slug,
                "title": song.title,
                "composers": "; ".join(song.composers),
                "lyricists": "; ".join(song.lyricists),
                "first_performed": song.first_performed.isoformat()
                if song.first_performed
                else "",
                "related_provenance": f"songs:{song.slug}",
                "related_figures": "top_songs.png; cooccurrence_heatmap.png; transition_matrix.png; repertoire_embedding.png",
            }
            for song in sorted(compendium.songs, key=lambda item: item.slug)
        ],
        "venues": [
            {
                "slug": venue.slug,
                "name": venue.name,
                "city": venue.city,
                "region": venue.state_or_region,
                "country": venue.country,
                "related_provenance": f"venues:{venue.slug}",
                "related_figures": "geo_scatter.png; venue_concentration.png; venue_identity_review.png",
            }
            for venue in sorted(compendium.venues, key=lambda item: item.slug)
        ],
        "segues": [
            {
                "src": edge.src,
                "src_title": song_titles.get(edge.src, edge.src),
                "dst": edge.dst,
                "dst_title": song_titles.get(edge.dst, edge.dst),
                "count": edge.count,
                "related_figures": "segue_graph.png; transition_sensitivity.png",
            }
            for edge in segue_edges(compendium)
        ],
        "claim_evidence": [
            {
                **row,
                "related_figure": row.get("figure_filename", ""),
                "related_report_key": row.get("report_key", ""),
            }
            for row in claim_rows
        ],
        "provenance_index": [
            {
                "entity_type": record.entity_type,
                "key": record.key,
                "source_keys": "; ".join(record.source_keys),
                "confidence": record.confidence,
                "related_entity": f"{record.entity_type}:{record.key}",
            }
            for record in provenance[:2000]
        ],
    }


def build_explorer_html() -> str:
    """Return plain HTML/CSS/JS explorer shell."""

    return dedent(
        """\
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Grateful Data Explorer</title>
          <style>
            :root {
              color-scheme: light;
              --ink: #14213d;
              --muted: #5b6472;
              --line: #d8dee9;
              --panel: #ffffff;
              --accent: #8f2d56;
              --bg: #f6f7f9;
            }
            * { box-sizing: border-box; }
            body {
              margin: 0;
              font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
              color: var(--ink);
              background: var(--bg);
            }
            header {
              padding: 28px clamp(18px, 4vw, 48px) 18px;
              border-bottom: 1px solid var(--line);
              background: var(--panel);
            }
            h1 { margin: 0 0 8px; font-size: clamp(1.6rem, 3vw, 2.4rem); }
            header p { margin: 0; max-width: 900px; color: var(--muted); line-height: 1.5; }
            main { padding: 24px clamp(18px, 4vw, 48px) 48px; }
            .controls {
              display: grid;
              grid-template-columns: minmax(220px, 1fr) minmax(180px, 260px) auto;
              gap: 12px;
              margin-bottom: 18px;
            }
            input, select, button {
              width: 100%;
              min-height: 42px;
              border: 1px solid var(--line);
              border-radius: 6px;
              padding: 8px 10px;
              font-size: 1rem;
              background: #fff;
              color: var(--ink);
            }
            button { cursor: pointer; font-weight: 650; color: #fff; background: var(--accent); border-color: var(--accent); }
            .summary {
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
              gap: 10px;
              margin-bottom: 18px;
            }
            .metric {
              background: var(--panel);
              border: 1px solid var(--line);
              border-radius: 6px;
              padding: 12px;
            }
            .metric b { display: block; font-size: 1.45rem; color: var(--accent); }
            .metric span { color: var(--muted); font-size: .9rem; }
            .grid {
              display: grid;
              grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
              gap: 16px;
            }
            section {
              background: var(--panel);
              border: 1px solid var(--line);
              border-radius: 6px;
              min-width: 0;
              overflow: hidden;
            }
            section h2 {
              margin: 0;
              padding: 12px 14px;
              font-size: 1rem;
              border-bottom: 1px solid var(--line);
            }
            .table-wrap { max-height: 420px; overflow: auto; }
            table { width: 100%; border-collapse: collapse; font-size: .88rem; }
            th, td { padding: 8px 10px; border-bottom: 1px solid #eef1f5; text-align: left; vertical-align: top; }
            th { position: sticky; top: 0; background: #f9fafb; z-index: 1; cursor: pointer; }
            td { color: #263447; }
            .muted { color: var(--muted); }
            #status { color: var(--muted); margin: -8px 0 16px; font-size: .9rem; }
            @media (max-width: 680px) {
              .controls { grid-template-columns: 1fr; }
              table { font-size: .8rem; }
            }
          </style>
        </head>
        <body>
          <header>
            <h1>Grateful Data Explorer</h1>
            <p>Static, local explorer over exported show, song, venue, segue, provenance, and claim-evidence data. It is pointer-only and contains no bundled audio or lyric text.</p>
          </header>
          <main>
            <div class="controls">
              <input id="data-search" type="search" placeholder="Filter current tables">
              <select id="dataset-select" aria-label="Visible dataset">
                <option value="all">All datasets</option>
                <option value="shows">Shows</option>
                <option value="songs">Songs</option>
                <option value="venues">Venues</option>
                <option value="segues">Segues</option>
                <option value="figures">Figures</option>
                <option value="claim_evidence">Claim evidence</option>
                <option value="provenance_index">Provenance</option>
              </select>
              <button id="download-filtered" type="button">Download CSV</button>
            </div>
            <div id="status"></div>
            <div id="summary" class="summary"></div>
            <div id="tables" class="grid"></div>
          </main>
          <script>
            const labels = {
              shows: ["date", "venue", "tour", "related_venue", "related_provenance", "slug"],
              songs: ["title", "composers", "lyricists", "first_performed", "related_figures", "slug"],
              venues: ["name", "city", "region", "country", "related_figures", "slug"],
              segues: ["src_title", "dst_title", "count", "related_figures"],
              figures: ["figure", "title", "claim_class", "statistic", "exclusion_rule", "raw_csv", "raw_json"],
              claim_evidence: ["claim_area", "claim_status", "manuscript_section", "related_figure", "test_file"],
              provenance_index: ["entity_type", "key", "source_keys", "confidence", "related_entity"]
            };
            let payload = null;
            let sortState = { key: "shows", column: "date", direction: "asc" };
            function cell(value) {
              const text = String(value ?? "");
              return text.replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
            }
            function formatCell(value, col) {
              const text = String(value ?? "");
              if (!text) return "";
              if (col === "raw_csv" || col === "raw_json") {
                return `<a href="${cell(text)}">${cell(text.split("/").pop())}</a>`;
              }
              if (col === "related_figures") {
                return text.split(";").map(v => v.trim()).filter(Boolean)
                  .map(v => `<a href="../figures/${cell(v)}">${cell(v)}</a>`).join(" · ");
              }
              if (col === "related_figure" && text.endsWith(".png")) {
                return `<a href="../figures/${cell(text)}">${cell(text)}</a>`;
              }
              if (col.startsWith("related_") || col === "related_entity") {
                return `<a href="?q=${encodeURIComponent(text)}">${cell(text)}</a>`;
              }
              return cell(text);
            }
            function updateUrlState() {
              const params = new URLSearchParams();
              const dataset = document.getElementById("dataset-select").value;
              const q = document.getElementById("data-search").value.trim();
              if (dataset !== "all") params.set("dataset", dataset);
              if (q) params.set("q", q);
              if (sortState.key && sortState.column) {
                params.set("sort", `${sortState.key}:${sortState.column}:${sortState.direction}`);
              }
              const next = `${location.pathname}${params.toString() ? "?" + params.toString() : ""}`;
              history.replaceState(null, "", next);
            }
            function restoreUrlState() {
              const params = new URLSearchParams(location.search);
              const dataset = params.get("dataset");
              const q = params.get("q");
              const sort = params.get("sort");
              if (dataset && labels[dataset]) document.getElementById("dataset-select").value = dataset;
              if (q) document.getElementById("data-search").value = q;
              if (sort) {
                const [key, column, direction] = sort.split(":");
                if (labels[key]?.includes(column)) sortState = { key, column, direction: direction === "desc" ? "desc" : "asc" };
              }
            }
            function renderSummary(summary) {
              const root = document.getElementById("summary");
              root.innerHTML = Object.entries(summary).map(([key, value]) => `<div class="metric"><b>${cell(value)}</b><span>${cell(key.replaceAll("_", " "))}</span></div>`).join("");
            }
            function filteredRows(key) {
              const filter = document.getElementById("data-search").value.trim().toLowerCase();
              const rows = (payload[key] || []).filter(row => JSON.stringify(row).toLowerCase().includes(filter));
              if (sortState.key === key && sortState.column) {
                rows.sort((a, b) => {
                  const av = a[sortState.column] ?? "";
                  const bv = b[sortState.column] ?? "";
                  const numeric = Number(av) - Number(bv);
                  const cmp = Number.isFinite(numeric) && av !== "" && bv !== "" ? numeric : String(av).localeCompare(String(bv));
                  return sortState.direction === "desc" ? -cmp : cmp;
                });
              }
              return rows;
            }
            function renderTables() {
              const selected = document.getElementById("dataset-select").value;
              const root = document.getElementById("tables");
              const keys = selected === "all" ? Object.keys(labels) : [selected];
              let totalShown = 0;
              root.innerHTML = keys.map(key => {
                const cols = labels[key];
                const allRows = filteredRows(key);
                const rows = allRows.slice(0, 500);
                totalShown += rows.length;
                const body = rows.map(row => `<tr>${cols.map(col => `<td>${formatCell(row[col], col)}</td>`).join("")}</tr>`).join("");
                const heads = cols.map(col => {
                  const marker = sortState.key === key && sortState.column === col ? (sortState.direction === "asc" ? " ↑" : " ↓") : "";
                  return `<th data-key="${cell(key)}" data-col="${cell(col)}">${cell(col.replaceAll("_", " "))}${marker}</th>`;
                }).join("");
                return `<section id="${cell(key)}"><h2>${cell(key.replaceAll("_", " "))} <span class="muted">(${rows.length} shown of ${allRows.length})</span></h2><div class="table-wrap"><table><thead><tr>${heads}</tr></thead><tbody>${body}</tbody></table></div></section>`;
              }).join("");
              document.getElementById("status").textContent = `${totalShown} rows shown. Click any column header to sort; filters are stored in the URL.`;
              document.querySelectorAll("th[data-key]").forEach(th => {
                th.addEventListener("click", () => {
                  const key = th.getAttribute("data-key");
                  const column = th.getAttribute("data-col");
                  const same = sortState.key === key && sortState.column === column;
                  sortState = { key, column, direction: same && sortState.direction === "asc" ? "desc" : "asc" };
                  updateUrlState();
                  renderTables();
                });
              });
              updateUrlState();
            }
            function downloadFilteredCsv() {
              const selected = document.getElementById("dataset-select").value;
              const key = selected === "all" ? "shows" : selected;
              const cols = labels[key];
              const lines = [cols.join(",")].concat(filteredRows(key).map(row => cols.map(col => `"${String(row[col] ?? "").replaceAll('"', '""')}"`).join(",")));
              const blob = new Blob([lines.join("\n") + "\n"], { type: "text/csv" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `grateful_data_${key}_filtered.csv`;
              a.click();
              URL.revokeObjectURL(url);
            }
            fetch("explorer_data.json")
              .then(response => response.json())
              .then(data => {
                payload = data;
                restoreUrlState();
                renderSummary(data.summary || {});
                renderTables();
              });
            document.getElementById("dataset-select").addEventListener("change", () => { updateUrlState(); renderTables(); });
            document.getElementById("data-search").addEventListener("input", () => { updateUrlState(); renderTables(); });
            document.getElementById("download-filtered").addEventListener("click", downloadFilteredCsv);
          </script>
        </body>
        </html>
        """
    )


def write_explorer(compendium: Compendium, out_dir: Path) -> tuple[Path, Path]:
    """Write ``index.html`` and ``explorer_data.json``."""

    out_dir.mkdir(parents=True, exist_ok=True)
    data_path = out_dir / "explorer_data.json"
    html_path = out_dir / "index.html"
    with data_path.open("w", encoding="utf-8") as fh:
        json.dump(explorer_payload(compendium), fh, indent=2, sort_keys=True)
        fh.write("\n")
    html_path.write_text(build_explorer_html(), encoding="utf-8")
    return html_path, data_path
