"""Per-song markdown page generation."""

from __future__ import annotations

from pathlib import Path

from ..analysis import eras, network
from ..integration.reconcile import Compendium


def write_song_pages(comp: Compendium, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    show_year = {s.slug: s.date.year for s in comp.shows}
    lp_by_song = {lp.song_slug: lp for lp in comp.lyric_pointers}

    for song in comp.songs:
        history = [p for p in comp.performances if p.song_slug == song.slug]
        years = sorted(
            {show_year[p.show_slug] for p in history if p.show_slug in show_year}
        )
        neighbors = network.song_neighbors(comp, song.slug)
        lp = lp_by_song.get(song.slug)
        lines: list[str] = [
            f"# {song.title}",
            "",
            f"- **Slug**: `{song.slug}`",
        ]
        if song.composers:
            lines.append(f"- **Composers**: {', '.join(song.composers)}")
        if song.lyricists:
            lines.append(f"- **Lyricists**: {', '.join(song.lyricists)}")
        if song.first_performed:
            lines.append(
                f"- **First performed**: {song.first_performed.isoformat()} "
                f"(era: {eras.era_of(song.first_performed)})"
            )
        if song.last_performed:
            lines.append(f"- **Last performed**: {song.last_performed.isoformat()}")
        if song.aliases:
            lines.append(f"- **Aliases**: {', '.join(song.aliases)}")
        lines.append(f"- **Seed performances**: {len(history)}")
        if years:
            lines.append(f"- **Years performed (in seed)**: {min(years)}–{max(years)}")
        if lp:
            lines.extend(
                [
                    "",
                    "## Lyric pointer",
                    f"- Lyricist: {lp.lyricist}",
                    f"- Source: <{lp.source_url}>",
                ]
            )
            if lp.themes:
                lines.append(f"- Themes: {', '.join(lp.themes)}")
        if history:
            lines.append("")
            lines.append("## Performances in seed")
            for perf in sorted(
                history, key=lambda p: (p.show_slug, p.set_number, p.position)
            ):
                lines.append(
                    f"- {perf.show_slug} (set {perf.set_number}, pos {perf.position})"
                )
        if neighbors:
            lines.append("")
            lines.append("## Same-show neighbors (top 15)")
            for nb in neighbors[:15]:
                lines.append(f"- `{nb}`")
        (out_dir / f"{song.slug}.md").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )

    index = out_dir / "_index.md"
    index_lines = ["# Song index", ""]
    for song in comp.songs:
        index_lines.append(f"- [{song.title}]({song.slug}.md)")
    index.write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    return index
