# grateful_data manuscript

Publication-track manuscript for the Grateful Dead data compendium
("The Music Never Stopped" — see repo root `README.md`, DOI
10.5281/zenodo.20482025): a citation-bound corpus of shows, songs,
performances, personnel, venues, recordings, and reception, with a
category-theoretic reading of the performance graph.

## Files

| File | Role |
|---|---|
| `config.yaml` | Paper metadata (paper, authors, publication, metadata, keywords, render blocks) |
| `00_abstract.md` … `05_conclusion.md` | Core sections in reading order |
| `03_category_theory.md` | Category-theoretic interpretation of the performance graph |
| `04b_segue_structure.md` | Segue-transition analysis companion to results |
| `06_reproducibility.md`, `07_honesty_boundary.md` | Reproducibility and claim-boundary sections |
| `99_references.md` + `references.bib` | References and bibliography |
| `preamble.md` | Render preamble |
| `AGENTS.md` | Authoring contract (token-injection rules) |

## Section order

00_abstract, 01_introduction, 02_methodology, 03_category_theory,
04_results, 04b_segue_structure, 05_conclusion, 06_reproducibility,
07_honesty_boundary, 99_references.

## Token injection

Quantitative values are cited through `{{UPPERCASE_TOKEN}}` substitution
(see `AGENTS.md`); tokens resolve at render time from generated variables
(`../scripts/z_generate_manuscript_variables.py` →
`output/data/manuscript_variables.json`). Unresolved tokens in these source
files on disk are expected. Do not hand-type numbers; every registered
figure panel declares its data source and plotted CSV/JSON rows under
`../output/data/figures/`.
