# grateful_data documentation

`grateful_data` builds a curated Grateful Dead data corpus — archival shows,
performances, songs, venues, personnel, releases, reviews, and citations —
and derives setlist/repertoire analytics from it. The publication-track
manuscript lives in `docs/manuscript/`.

## Repo layout

| Path | Contents |
|---|---|
| `data/` | Corpus source data |
| `src/` | Corpus construction and analysis code |
| `scripts/` | Thin orchestrators that call `src/` |
| `tests/` | Test suite |
| `output/` | Generated figures and data artifacts |
| `docs/manuscript/` | Publication-track manuscript (sections, `config.yaml`, `references.bib`) |
| `AGENTS.md`, `ISA.md`, `TODO.md` | Agent notes, project ISA, backlog |

## How to run/test

Install and run the suite from the repo root (the `dev` extra carries pytest,
coverage, and hypothesis):

```bash
uv sync --extra dev
uv run --extra dev pytest tests/ --cov=src --cov-fail-under=90
```

Entry points are the numbered scripts in `scripts/` — see
[`../scripts/README.md`](../scripts/README.md) for the inventory; there is no
`[project.scripts]` console-script table in `pyproject.toml`.

## Documentation here

This `docs/` folder is intentionally minimal: root `README.md` (overview +
commands), `AGENTS.md` (agent-facing notes), and `docs/manuscript/AGENTS.md`
(manuscript authoring contract) are the maintained entry points. Add one
file per real concern here only when a concern outgrows those.
