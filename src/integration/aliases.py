"""Canonical song-alias map.

Two real Dead-corpus naming patterns silently split into separate slugs under
naive title-slug normalization:

* ``Playin' in the Band`` vs ``Playing in the Band`` (apostrophe drop);
* ``Bertha`` vs ``Bertha (Reprise)`` (segue/reprise notation).

This map is consulted by :func:`canonicalize_alias` before insertion into a
``Compendium``. The map is small and curated; future sources should extend it
rather than route around it.
"""

from __future__ import annotations

# Map of (alias_slug -> canonical_slug).
SONG_ALIAS_MAP: dict[str, str] = {
    "playin_in_the_band": "playing_in_the_band",
    "bertha_reprise": "bertha",
    "rhythm_devils": "drums",
    "china_cat_i_know_you_rider": "china_cat_sunflower",
    "minglewood_blues_new": "minglewood_blues",
    "new_minglewood_blues": "minglewood_blues",
    "sugar_mag": "sugar_magnolia",
    "lovelight": "turn_on_your_lovelight",
    "music_never_stopped": "the_music_never_stopped",
    "estimated": "estimated_prophet",
    "scarlet": "scarlet_begonias",
    "fire": "fire_on_the_mountain",
    "help_slipknot_franklins": "help_on_the_way",
    "stranger": "feel_like_a_stranger",
    "uncle_johns": "uncle_johns_band",
}


def canonicalize_alias(slug: str) -> str:
    """Return the canonical slug for ``slug``, applying the alias map."""
    return SONG_ALIAS_MAP.get(slug, slug)


# ---------------------------------------------------------------------------
# Venue aliases
# ---------------------------------------------------------------------------
# A single physical venue is recorded under many name variants across sources
# (spelling, punctuation, word order, official-vs-common name), which fragments
# venue/show/network/geo counts at archival scale — the Oakland Coliseum *Arena*
# alone appears as five slugs totalling 132 shows, whose two largest fragments
# (66 and 55) currently rank as separate #1 and #3 venues.
#
# This map is a CONSERVATIVE, CURATED, hand-verified layer. Principles:
#   * Only obvious same-venue variants (spelling/punctuation/word-order, common
#     vs official name) are collapsed.
#   * Each canonical target is chosen to MATCH the bundled-seed slug when the
#     venue exists in the seed, so canonicalization is a no-op on the seed
#     (pinned seed venue count is preserved) and only collapses archival dupes.
#   * Genuinely distinct venues are NEVER merged. Negative controls enforced in
#     tests: Fillmore West/East/Auditorium stay three venues; Madison Square
#     Garden != its Felt Forum room; the Coliseum *Arena* (indoor) != the
#     *Stadium* (outdoor); Oakland Auditorium (pre-1984 name) is left separate
#     from Henry J. Kaiser Convention Center (a rename we deliberately do NOT
#     fold, to avoid a judgment merge across time).
#   * The map is intentionally NON-EXHAUSTIVE; residual venue fragmentation is
#     reported as a known limitation rather than resolved by fuzzy matching.
VENUE_ALIAS_MAP: dict[str, str] = {
    # Oakland-Alameda County Coliseum Arena (indoor) — seed form is canonical.
    "oakland_coliseum_oakland": "oakland_coliseum_arena_oakland",
    "oakland_alameda_county_coliseum_arena_oakland": "oakland_coliseum_arena_oakland",
    "oakland_alameda_co_coliseum_oakland": "oakland_coliseum_arena_oakland",
    "oakland_arena_oakland": "oakland_coliseum_arena_oakland",
    # Oakland Coliseum Stadium (outdoor) — distinct building from the Arena.
    "oakland_alameda_county_coliseum_stadium_oakand": "oakland_coliseum_stadium_oakland",
    "oakland_alameda_county_stadium_oakland": "oakland_coliseum_stadium_oakland",
    # The Spectrum, Philadelphia — seed form is canonical.
    "spectrum_philadelphia": "the_spectrum_philadelphia",
    "philadelphia_spectrum_philadelphia": "the_spectrum_philadelphia",
    # Winterland, San Francisco — seed form is canonical.
    "winterland_san_francisco": "winterland_arena_san_francisco",
    # Madison Square Garden, New York — seed form is canonical (NOT Felt Forum).
    "madison_square_garden_new_york_city": "madison_square_garden_new_york",
    "madison_square_garden_nyc": "madison_square_garden_new_york",
    # Nassau Veterans Memorial Coliseum, Uniondale.
    "nassau_coliseum_uniondale": "nassau_veterans_memorial_coliseum_uniondale",
    # Henry J. Kaiser Convention Center, Oakland — seed form is canonical.
    "henry_j_kaiser_oakland": "henry_j_kaiser_convention_center_oakland",
    "henry_j_kaiser_auditorium_oakland": "henry_j_kaiser_convention_center_oakland",
    # Red Rocks Amphitheatre, Morrison — seed spelling is canonical.
    "red_rocks_amphitheater_morrison": "red_rocks_amphitheatre_morrison",
    # William Randolph Hearst Greek Theatre, UC Berkeley.
    "greek_theater_u_of_california_berkeley": "greek_theatre_berkeley",
    "the_greek_theatre_berkeley": "greek_theatre_berkeley",
    "william_randolph_hearst_greek_theatre_uc_berkeley_berkeley": "greek_theatre_berkeley",
    # Hampton Coliseum, Hampton.
    "coliseum_hampton": "hampton_coliseum_hampton",
    "hampton_roads_coliseum_hampton": "hampton_coliseum_hampton",
}


def canonicalize_venue_slug(slug: str) -> str:
    """Return the canonical venue slug for ``slug`` (conservative alias layer)."""
    return VENUE_ALIAS_MAP.get(slug, slug)
