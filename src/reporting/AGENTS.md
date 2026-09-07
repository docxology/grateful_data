# AGENTS.md — `grateful_data/src/reporting`

> Local-only path under `projects/ongoing/DataTools/` — matched by the
> root `.gitignore` rule `projects/*`; never commit. Repo-wide policy:
> see `/Volumes/external_drive/Git/template/projects/ongoing/AGENTS.md`.

## What this is

Report and table generation.

## Layout (verified by direct listing, 2026-08-29)

```
__init__.py, dashboard.py, entity_pages.py, explorer.py, manuscript.py, peer_review.py, release_prep.py, song_pages.py
```

## Gotchas

- `manuscript.py` and `release_prep.py` hold the logic moved out of
  `scripts/z_generate_manuscript_variables.py` and `scripts/21_release_prep.py`
  (thin-orchestrator contract, 2026-09 audit remediation).
- Template-root discovery lives in `manuscript.find_template_root`; never
  hardcode machine-specific absolute paths in scripts or src.
