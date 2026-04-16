# Knowledge Graph Rebuild — Status

**Branch:** `claude/review-mskb-patterns-OmGDe`  
**Approach:** Apply the [MSKB three-layer methodology](https://github.com/wrgr/mskb) to the LE knowledge graph.  
**Last updated:** 2026-04-10

---

## What Is Done

All items from the original rebuild plan are complete. The additional structural
improvements from the MSKB peer review (April 2026) are also incorporated.

### Original Rebuild Items

| File | Status | Notes |
|------|--------|-------|
| `corpus/tables/concept_ontology.json` | ✅ | 35 concepts with prerequisites, Bloom levels, paper+resource bindings |
| `corpus/tables/icicle_resources_registry.json` | ✅ | 40 ICICLE-harvested resources (LE-IC-001–LE-IC-040) |
| `corpus/tables/concept_graph_seeds.json` | ✅ | BELONGS_TO, PREREQ_FOR, BOOK_CHAPTER edges |
| `corpus/tables/learning_journeys.json` | ✅ | J-01 through J-06 with concept_ids per stage |
| `scripts/build_dataset.py` — concept layer | ✅ | `build_concept_graph()` implemented and wired into `build_graph()` |
| `scripts/build_dataset.py` — ICICLE registry | ✅ | `build_resources()` loads `icicle_resources_registry.json` |
| `LEARNING_CONCEPT_ONTOLOGY.md` | ✅ | Human-readable reference for all 35 concepts |
| `RESOURCE_CURATOR_TEMPLATE.md` | ✅ | Curation workflow, ID scheme, fields, concept binding |

### MSKB Peer Review Additions (April 2026)

| Change | Status | Notes |
|--------|--------|-------|
| `programs_people_registry.json` wired into `build_resources()` | ✅ | Deduplication by resource_id; LE-PP-* resources now in graph |
| `data/learning_journeys.json` output in `main()` | ✅ | Pipeline now writes journeys to `data/` for frontend |
| `concept_nodes` count in `build_summary()` | ✅ | Visible in `data/build_summary.json` |
| `audit_resource_diversity()` function | ✅ | Per-topic content-type balance check; writes `data/diversity_audit.json` |
| `seed_role` field in `metadata_schema.json` | ✅ | expansion / landmark_anchor / framing / bridge |
| `RETIRED` status + `retired_in_version` field in `metadata_schema.json` | ✅ | Full seed lifecycle now documented |
| Scoring rubric in `RESOURCE_CURATOR_TEMPLATE.md` | ✅ | 5-dimension rubric, 18/25 threshold |
| Maintenance schedule in `RESOURCE_CURATOR_TEMPLATE.md` | ✅ | Quarterly URL checks, annual freshness review |
| `TECH_NOTE_CONCEPT_BINDING.md` | ✅ | Architecture rationale for three-layer model |

### Build Pipeline Refactor (April 2026)

| Change | Status | Notes |
|--------|--------|-------|
| `scripts/utils.py` | ✅ | Shared constants and pure utility functions |
| `scripts/openalex_client.py` | ✅ | OpenAlex, Crossref, ArXiv API clients |
| `scripts/abstract_fetcher.py` | ✅ | URL/PDF fetching, enrichment pipeline, Topic model |
| `scripts/build_dataset.py` | ✅ | Corpus builders + main() — replaced broken stub |

---

## The Three-Layer Architecture (Stable)

```
Layer 1: Topics (T00–T17)         18 broad topic areas — coarse-grained taxonomy
Layer 2: Concepts (C01–C35)       35 concepts — meso-level ontology (WIRED ✅)
Layer 3: Papers + Resources       ~300 seed/hop papers + 100+ curated resources (WIRED ✅)
```

All three layers are now connected in `data/graph.json`. The concept layer is fully
operational: topic→concept edges, concept→paper edges, concept→resource edges, and
concept→concept prereq edges are all emitted in the standard build.

---

## Known Remaining Gaps (Future Work)

These items are out of scope for the current branch but worth tracking:

| Gap | Priority | Notes |
|-----|----------|-------|
| Populate `seed_role` for existing T1 seeds in `academic_papers.jsonl` | Medium | Most T1 seeds are `expansion`; textbook + Saxberg essay should be `landmark_anchor` |
| Assign concept bindings for C34 (Ethics & Equity) | Low | `primary_resources: []` — needs at least 1–2 resources |
| Expand coverage of T14 (Ethics & Equity) | Low | Under-resourced relative to its importance |
| URL validation pass on LE-PP-* entries | Low | Some entries have empty or `[internal]` URLs |
| Version-tag the corpus (`v1.0`) | Low | Helps with lifecycle tracking and retired_in_version references |

---

## Key Design References

| Document | Location | Purpose |
|----------|----------|---------|
| MSKB three-layer architecture | `wrgr/mskb README` | The methodology applied here |
| LE concept ontology (Layer 2) | `corpus/tables/concept_ontology.json` | 35 concepts |
| LE topic map (Layer 1) | `corpus/tables/topic_map.json` | 18 topics T00–T17 |
| LE ICICLE resources | `corpus/tables/icicle_resources_registry.json` | LE-IC-* registry |
| LE programs/people | `corpus/tables/programs_people_registry.json` | LE-PP-* registry |
| LE existing graph seeds | `corpus/tables/knowledge_graph_seeds.json` | Topic-level edges |
| Architecture rationale | `TECH_NOTE_CONCEPT_BINDING.md` | Why three layers; how concept binding works |
| Build pipeline | `scripts/build_dataset.py` | Main graph construction entry point |

---

## Quick Start

```bash
cd learning-engineering-resources
git checkout claude/review-mskb-patterns-OmGDe

# Run the full build
python3 scripts/build_dataset.py

# Outputs written to data/:
#   graph.json               — full L1+L2+L3 graph
#   learning_journeys.json   — J-01 through J-06
#   diversity_audit.json     — per-topic content-type balance warnings
#   build_summary.json       — includes concept_nodes count
```
