# grateful_data documentation

`grateful_data` builds a curated Grateful Dead data corpus — archival shows,
performances, songs, venues, personnel, releases, reviews, and citations —
and derives setlist/repertoire analytics from it. The publication-track
manuscript lives in `../manuscript/`.

## Repo layout

| Path | Contents |
|---|---|
| `data/` | Corpus source data |
| `src/` | Corpus construction and analysis code |
| `scripts/` | Thin orchestrators that call `src/` |
| `tests/` | Test suite |
| `output/` | Generated figures and data artifacts |
| `manuscript/` | Publication-track manuscript (sections, `config.yaml`, `references.bib`) |
| `AGENTS.md`, `ISA.md`, `TODO.md` | Agent notes, project ISA, backlog |

## How to run/test

Commands are declared by `pyproject.toml` at the repo root (dependency group
`uv.lock`); install and run tests with:

```bash
uv sync
uv run pytest tests/
```

Entry-point script names are listed in `pyproject.toml` under
`[project.scripts]`; consult it rather than this file for the live list.

## Documentation here

This `docs/` folder is intentionally minimal: root `README.md` (overview +
commands), `AGENTS.md` (agent-facing notes), and `manuscript/AGENTS.md`
(manuscript authoring contract) are the maintained entry points. Add one
file per real concern here only when a concern outgrows those.
