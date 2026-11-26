# Publication artifacts

| Artifact | Path | Purpose |
| --- | --- | --- |
| Dashboard | `output/dashboard.html` | Sectioned static figure browser with raw CSV/JSON links |
| Figure data | `output/data/figures/` | Registry-backed plotted data exports and index |
| Provenance sidecar | `output/data/provenance/` | Entity/source-layer provenance without schema mutation |
| External manifests | `output/data/external/` | Pointer-only audio/lyric manifests plus future-pipeline contract; no protected content |
| Static explorer | `output/explorer/index.html` | Plain HTML/JS filters for shows, songs, venues, segues, figures, claims, provenance |
| Peer-review dossier | `output/reports/peer_review_dossier.{json,md}` | Claim-to-artifact map for reviewers |
| Publication validation | `output/reports/publication_validation.json` | PDF/HTML/dashboard/figure-data/citation/token checks |
| Release prep | `output/reports/release_prep.json` | Command-order and execution report for release gate |

The explorer is intentionally framework-free. It supports URL-state filters,
sortable table headers, related links, and filtered CSV downloads so reviewers
can inspect show, song, venue, segue, figure, claim, and provenance subsets
locally.

Useful inspection commands:

```bash
GRATEFUL_DATA_TIER=archival uv run python -m src.cli provenance songs scarlet_begonias
python -m json.tool output/reports/analysis_report.json | rg "transition_sensitivity|repertoire_topn_sensitivity|venue_identity_review"
python -m json.tool output/reports/publication_validation.json
python -m json.tool output/data/figures/index.json
```
