# Grateful Data Peer-Review Dossier

Dossier maps claim families to available artifacts; it is a reviewer navigation aid, not a replacement for tests.

- Claim families: 12
- Citation keys: 139

| Claim | Status | Section | Figure | Report/Test | Limit |
| --- | --- | --- | --- | --- | --- |
| Corpus scope and identity | audited-descriptive | Data and Scope | not-applicable | analysis_report.json::top_line / tests/test_pipeline_integration.py | Referential completeness is not exhaustive coverage of every concert or optional layer |
| Setlist-size distribution | audited-descriptive | Descriptive Statistics | performance_distribution.png (present) | analysis_report.json::performance_distribution / tests/test_distributions.py | The statistic describes metadata density, not musical length or quality |
| Repertoire ranking | audited-descriptive | Repertoire Shape | top_songs.png (present) | analysis_report.json::top_songs / tests/test_stats.py | A high count is not a preference, importance, or aesthetic claim |
| Concentration metrics | audited-model | Concentration and Uncertainty | concentration_uncertainty.png (present) | analysis_report.json::concentration_uncertainty / tests/test_distributions.py | Intervals do not estimate unseen concerts or listener behavior |
| Transition model | audited-model | Transitions and Segues | transition_matrix.png (present) | analysis_report.json::transition_significance / tests/test_transitions.py | Transition probabilities are not causal or predictive laws |
| Explicit segue structure | audited-descriptive | Transitions and Segues | segue_graph.png (present) | analysis_report.json::segues / tests/test_more_analyses.py | Unmarked segues and audio-continuity evidence are outside this corpus |
| Co-occurrence and centrality | audited-model | Co-occurrence | cooccurrence_heatmap.png (present) | analysis_report.json::cooccurrence / tests/test_more_analyses.py | Association centrality is not influence, authorship, or musical similarity |
| Exploratory repertoire embedding | exploratory-noncausal | Exploratory Repertoire Geometry | repertoire_embedding.png (present) | analysis_report.json::exploratory_repertoire / tests/test_exploratory.py | Clusters are pattern-discovery aids, not definitive musicological taxonomy |
| Category-theoretic abstraction | audited-formalization | Categorical Model | functor_cardinalities.png (present) | category_theory_report.json / tests/test_category_theory.py | Formal coherence does not prove cultural or musical explanation |
| Venue geography | metadata-limited | Geography | geo_scatter.png (present) | analysis_report.json::venue_geography / tests/test_more_analyses.py | Slug-level venue counts are lower bounds per physical building when aliases remain |
| Lyrics and review overlays | pointer-only-limited | External Pointer Overlays | lyric_themes.png (present) | analysis_report.json::lyrics_reviews / tests/test_lyric_enrichment.py | Overlay counts are not representative samples of all lyrics or reviews |
| Historical and archival context | citation-supported | Related Work and Archival Context | context_timeline.png (present) | bibliography_report.json / tests/test_fetch_bibliography.py | Contextual overlays explain why dates matter but do not alter computed counts |
