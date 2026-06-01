# AGENTS — grateful_data/manuscript

Markdown sections for the Grateful Dead data compendium paper. Rendered via the
template root:

```bash
GRATEFUL_DATA_TIER=archival uv run python scripts/z_generate_manuscript_variables.py
uv run python scripts/03_render_pdf.py --project grateful_data
```

## Files

| File | Role |
| --- | --- |
| `config.yaml` | Title, authors, render options |
| `preamble.md` | LaTeX preamble hooks |
| `00_abstract.md` … `07_honesty_boundary.md` | Body sections |
| `references.bib` | Bibliography (parser sources + archival/MIR/context/category-theory scholarship) |
| `99_references.md` | Rendered references section stub |

## Variable substitution

Publication uses archival counts only. Tokens (`{{ARCHIVAL_*}}`,
`{{ARCHIVAL_SEGUE_MARKERS}}`, `{{CORPUS_SCOPE_PHRASE}}`, `{{CORPUS_LABEL}}`) are
resolved by `scripts/z_generate_manuscript_variables.py`, which writes
`output/data/manuscript_variables.json` and hydrates `output/manuscript/` via
`write_resolved_manuscript_tree` before PDF render. Unresolved `{{TOKENS}}`
after injection abort the generator.

## Citation and visual documentation rules

- Keep volatile counts in `{{TOKENS}}`; update
  `scripts/z_generate_manuscript_variables.py` rather than hard-coding new
  archival counts in prose.
- Cite source-parser inputs separately from interpretive scholarship. Archival,
  taping, MIR, lyric-annotation, historical-context, public-recognition, and
  category-theory sources belong in `references.bib` even when they are not
  ingested as data rows.
- Figure filenames, dashboard labels, alt text, caption hints, data source,
  statistic, exclusion rule, claim class, and figure-data exporters live in
  `src/viz/figures.py`. Add or rename figures through that registry rather
  than duplicating lists in scripts or prose; CSV/JSON panel data and the
  metadata index are emitted by `scripts/18_export_figure_data.py`.
- Claim boundaries live in `src/analysis/first_principles.py` and are exported
  by `scripts/19_first_principles_review.py`; do not strengthen a descriptive
  or exploratory claim without updating the ledger.
- Preserve the no-lyrics/no-audio boundary: lyric references are pointers and
  interpretive citations only; audio similarity remains a downstream stub.
