# Abstract

We present a modular, citation-bound data compendium for the Grateful Dead
universe — shows, songs, performances, personnel timelines, venues,
recordings, and reception — and a category-theoretic interpretation of the
performance graph. The work is grounded in the archival reality that Grateful
Dead history is both institutional and participatory: UCSC's Grateful Dead
Archive and the Internet Archive collection preserve formal and community
records [@ucsc_grateful_dead_archive; @internet_archive_lma;
@internet_archive_gd_collection_policy], while taping and trading scholarship
shows why setlists and recording metadata are cultural evidence, not merely
fan trivia [@dead_net_taping_dead; @wallace_cocreation_sound_archive].
The surrounding source dossier also binds the non-quantitative historical
frame -- formation and Acid Test context, Wall of Sound engineering, live
recording/liveness scholarship, Deadhead sociology, studio-era reception, and
public recognition -- to checked sources rather than to folklore alone
[@dead_net_biography; @foundsf_weir_psychedelic_sf;
@smithsonian_institutionally_dead; @mcintosh_wall_of_sound;
@brackett_live_dead; @adams_deadhead_social_science;
@rockhall_grateful_dead; @grammy_lifetime_achievement;
@kennedy_center_honors_2024].
The compendium integrates nine primary sources
(`Setlist.fm` [@setlistfm_gd], `The SetList Program` [@setlists_net_program],
the Mark Leone CMU setlist archive [@cmu_leone_setlists; @noah_truckin_through_time],
`GDsets` [@gdsets_com; @gdsets_dead],
`gdshowsdb` [@gdshowsdb; @github_topic_gratefuldead],
the Internet Archive Live Music Archive [@internet_archive_lma; @fifteen_songs_dataset],
the Alex Allan / whitegum lyric finder [@whitegum_alex_allan; @cmu_leone_lyrics],
the official band site [@dead_net_official], and Wikipedia
[@wikipedia_gd; @wikipedia_discography])
with four reference sources (Britannica [@britannica_gd], the lineup-changes
guide [@ucr_lineup_changes], Dodd and Trist's *The Complete Annotated
Grateful Dead Lyrics* [@dodd_annotated_lyrics], and the Grateful Stats
front-end [@grateful_stats]) and secondary corpora and community
discussions [@grateful_data_tutorial; @jerry_pycia; @gd_reviews_corpus;
@reddit_data_sets; @reddit_lyrics_attribution; @reddit_setlist_db;
@reddit_spreadsheet_archive]. Each source is parsed by an independently
testable *reference* module written against the documented record shape;
the committed compendium under ``data/archival/`` is the dataset reported
here ({{CORPUS_SCOPE_PHRASE}}). A runtime
completeness audit and figure-validation gate certify referential integrity
and non-degenerate outputs on every pipeline run. Integration is a
deterministic, sort-keyed merge over canonical slugs; registered figures also
emit CSV/JSON data tables, and a first-principles claim ledger classifies each
major result by irreducible input, hard constraint, assumption, validation
artifact, and interpretation limit. Exploratory repertoire/uncertainty panels
are labelled as pattern-discovery rather than causal inference. We then
exhibit four small but real categorical constructions, situated against
transformational and categorical music-theory precedents
[@lewin_gmit; @padi_category_music_case_study; @popoff_hidden_categories]:
a poset category of
dates, a discrete category of shows, a *monotone* cumulative setlist functor
and lineup functor from dates into sets, and a span representation that takes
each performance to be the apex of a span between its show and its song. Wide
pullbacks over a fixed show recover the show's setlist; wide pullbacks over a
fixed song recover the song's performance history. The active-band roster, by
contrast, is a non-monotone presheaf on the date poset — a categorical
formalization of the familiar fact that members come and go. The artefacts in
this paper come from the committed archival snapshot; all source-ingestion
modules are written against the *real* source shape so that
``scripts/00_fetch_sources.py --online --write-archival`` refreshes the full
snapshot.
