# Introduction

## What we mean by "the music never stopped"

The Grateful Dead performed roughly two and a half thousand concerts between
1965 and 1995. The public record of those concerts — setlists, recordings,
ticket stubs, member rosters, composer credits, release histories, and decades
of fan commentary — is one of the most extensively documented bodies of live
performance in popular-music history. It is also unusually hybrid. UCSC's
Grateful Dead Archive gives the band a formal institutional home
[@ucsc_grateful_dead_archive], while the Internet Archive collection and
Deadhead taping culture preserve the community-built sound archive and its
metadata [@internet_archive_gd_collection_policy; @dead_net_taping_dead;
@wallace_cocreation_sound_archive]. The record is fragmented across primary
databases, archival corpora, reference works, and a long tail of community
spreadsheets and forum threads
[@reddit_data_sets; @reddit_setlist_db; @reddit_spreadsheet_archive]. This
paper introduces *The Music Never Stopped*: a reproducible, citation-bound
compendium that integrates the primary sources into a single schema, exposes
them to standard data-analysis machinery, and exhibits a small but genuine
category-theoretic structure latent in the performance graph.

## Sources surveyed

We organize the cited landscape into four layers.

**Primary setlist sources.** Setlist.fm publishes a crowd-curated, API-backed
register of every Grateful Dead show [@setlistfm_gd]. The SetList Program at
``setlists.net`` covers 1965–1995 with an interactive interface
[@setlists_net_program]. The Mark Leone CMU archive
[@cmu_leone_setlists], derived from the Jerry Stratton database, is the
ancestor of many community scrapes; Noah Gorstein has converted the abandoned
HTML into an open SQLite database [@noah_truckin_through_time]. ``GDsets``
combines setlists with ticket-stub and stage-pass images
[@gdsets_com; @gdsets_dead]. The ``gdshowsdb`` repository ships a relational
schema and a Ruby gem [@gdshowsdb]; the GitHub topic ``gratefuldead`` is the
meta-index that links these and other resources [@github_topic_gratefuldead].

**Primary lyric and song-attribution sources.** Mark Leone's lyric index at
CMU [@cmu_leone_lyrics] points to the Stratton database via FTP. Alex Allan's
``whitegum.com`` is the canonical lyric and song finder for every song the
Dead played, with composer/lyricist attribution and per-song performance
data [@whitegum_alex_allan]. Dodd and Trist's *The Complete Annotated
Grateful Dead Lyrics* supplies the authoritative interpretive and annotation
context for lyric studies [@dodd_annotated_lyrics]. We cite it as an external
authority and store only pointer metadata; no lyric text is bundled.
Hunter's own retrospective account and community discussion are used only as
context for songwriter roles, never as an override of the structured
composer/lyricist fields [@rolling_stone_robert_hunter_interview;
@reddit_lyrics_attribution].

**Personnel, discography, recording, and reception sources.** The official band
site lists members and roles [@dead_net_official]. Wikipedia's Grateful Dead
entry [@wikipedia_gd] and discography [@wikipedia_discography] anchor the
biographical timeline; Britannica frames the wider cultural context
[@britannica_gd]. *Ultimate Classic Rock*'s lineup-changes guide
[@ucr_lineup_changes] provides a chronological narrative of personnel
transitions. The Internet Archive's Live Music Archive supplies recording
metadata for the bulk of the live corpus [@internet_archive_lma], and its
Grateful Dead collection policy explains the special access and metadata
posture of those recordings [@internet_archive_gd_collection_policy]. The
``fifteen-songs-dataset`` curates 2617 soundboard recordings of 15 songs for
music-information-retrieval research [@fifteen_songs_dataset], while Wang
et al.'s setlist-segmentation paper gives a broader MIR frame for why live
setlist identification is non-trivial [@wang_setlist_segmentation].
``jerryPycia`` provides a Python query library over Dead show data
[@jerry_pycia]; the ``grateful-dead-reviews`` corpus collects long-form fan
reviews [@gd_reviews_corpus]. The ``gratefulstats.com`` front-end aggregates
show/tune/venue statistics [@grateful_stats]. The ``gratefuldata`` tutorial
demonstrates an ETL pipeline using the Internet Archive together with ASCAP
ACE composer data [@grateful_data_tutorial]. The compendium draws
composer/lyricist attributions from these sources and encodes them in
``data/archival/songs.json``.

**Historical, technical, and interpretive context.** The supplied enriched
bibliography is useful as a discovery map, but the map is not itself evidence.
Each durable topic is therefore rebound to checked source families: the
official dead.net biography and FoundSF's Bob Weir oral-history page for
formation and Acid Test context [@dead_net_biography;
@foundsf_weir_psychedelic_sf], Smithsonian and UCSC for institutional archive
status [@smithsonian_institutionally_dead; @ucsc_grateful_dead_archive],
McIntosh for the Wall of Sound hardware [@mcintosh_wall_of_sound], Marshall,
JSTOR Daily, Meriwether, Wallace, and the Internet Archive policy page for
the tape-trading and sound-archive ecosystem [@marshall_bootleg_collectors;
@jstor_daily_tape_trading; @dead_net_taping_dead;
@wallace_cocreation_sound_archive; @internet_archive_gd_collection_policy],
Brackett's *Live Dead* for liveness and recorded-performance scholarship
[@brackett_live_dead], Adams and Sardiello for Deadhead sociology
[@adams_deadhead_social_science], Dodd and Weiner for the bibliographic field
map [@dodd_weiner_annotated_bibliography], Britannica and Americana Highways
for narrow biographical and studio-reception context
[@britannica_jerry_garcia; @americana_highways_workingmans_american_beauty],
and official public-recognition sources for later institutional status
[@rockhall_grateful_dead; @grammy_lifetime_achievement;
@kennedy_center_honors_2024]. Community reconstructions such as touring
revenue estimates are cited only as labelled business-history context, not as
compendium measurements [@grateful_seconds_touring_revenues].

## What is in this repository

We ship a committed archival compendium under ``data/archival/`` that drives
every analysis and category-theoretic claim in this paper end-to-end, plus a
parser for each cited source so that refreshing the snapshot is a matter of
running the same code with online flags.

## Related work

Prior Grateful Dead data efforts are mostly *single-source* or
*single-purpose*. Community setlist databases and the gdshowsdb /
truckin-through-time projects [@gdshowsdb; @noah_truckin_through_time]
assemble the raw show record; aggregators such as Grateful Stats
[@grateful_stats] and community spreadsheets and forums [@reddit_setlist_db;
@reddit_data_sets] surface frequency rankings; and query libraries such as
``jerryPycia`` [@jerry_pycia] and the ``grateful-data`` tutorial
[@grateful_data_tutorial] expose one source programmatically. Archive and
popular-music studies add a second frame: the Dead's sound record is
co-produced by band, archive, tapers, uploaders, and curators rather than
handed down by a single authority [@wallace_cocreation_sound_archive;
@dead_net_taping_dead; @internet_archive_gd_collection_policy;
@brackett_live_dead]. Sociological work on Deadheads, bibliographic
scholarship, and tape-trader studies explain why this record is also a
community institution rather than simply a discography
[@adams_deadhead_social_science; @dodd_weiner_annotated_bibliography;
@marshall_bootleg_collectors; @jstor_daily_tape_trading].

This compendium differs on two axes. It is *integration-first*: primary sources
are reconciled on canonical slugs into one immutable, citation-bound schema
with a runtime honesty boundary and completeness/figure-validation probes. It
is also *structure-first*: the performance record is read through small but
mechanically checked categorical constructions (functors, spans, colimits, a
date-poset Yoneda statement) rather than treated only as a frequency table.
The music-theory lineage is Lewin's transformational shift from static objects
to relations and transformations [@lewin_gmit], with newer categorical music
work showing how such networks can be formalized diagrammatically
[@padi_category_music_case_study; @popoff_hidden_categories]. Our contribution
is a concrete, reproducible instantiation on a real performance corpus, with
every quantitative or categorical claim bound to code.

## What is *not* in this repository

We do not bundle lyric text — full lyrics are copyrighted. The compendium
stores songs as titled records with composer and lyricist attribution; the
semantic layer (motifs, themes, annotations) is read against external
indices such as Alex Allan's finder and Dodd's annotated lyrics
[@whitegum_alex_allan; @dodd_annotated_lyrics]. We do not bundle audio.
The audio-enriched category in §3 is a structural abstraction over
similarity weights; concrete weights are produced by an external pipeline
against the ``fifteen-songs-dataset`` [@fifteen_songs_dataset].
