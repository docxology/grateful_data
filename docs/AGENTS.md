# Agent notes — grateful_data/docs

- Docs conventions for this repo live in the root `AGENTS.md` and
  `docs/manuscript/AGENTS.md` (token-injection authoring contract); this folder
  holds only supplementary engineering docs.
- Manuscript numbers come from `{{TOKEN}}` substitution resolved at render
  time; do not hard-code counts into docs or prose.
- Factual claims in anything added here must trace to `data/`, `src/`,
  `output/`, or `pyproject.toml`. If unverifiable, write "Not documented in
  repo — needs owner input" instead.
- Do not create render intermediates here; rendering goes through the
  manuscript pipeline (see root `README.md` / `pyproject.toml`).
