# Knowledge Graph Rebuild — Status & Remaining Work

**Branch:** `claude/rebuild-knowledge-graph-Q1Fa3`  
**Approach:** Apply the [MSKB three-layer methodology](https://github.com/wrgr/mskb) to the LE knowledge graph.

---

## What Was Done

### Research (complete)
- Analyzed both repos (`wrgr/learning-engineering-resources`, `wrgr/mskb`) in full
- Scraped the [IEEE ICICLE resources page](https://sagroups.ieee.org/icicle/resources/) — ~80 resources catalogued (2018–2025): books, tools, templates, videos, podcasts, articles, communities
- Diagnosed the core problem: **the graph has no Layer 2** (concept ontology), which is why it feels disconnected. Topics (T00–T17) are too coarse; papers and resources have nothing in between to bind them together.

### Files Written
| File | Status | Notes |
|------|--------|-------|
| `corpus/tables/concept_ontology.json` | ✅ Written | 35 concepts, anchored to book chapters, with prereqs, Bloom levels, paper+resource bindings |

---

## The Three-Layer Architecture (Design)

```
Layer 1: Citation graph (papers)     — already built (21 seeds + 274 hop papers)
Layer 2: Concept ontology            — concept_ontology.json now exists (NEW)
Layer 3: Curated resources           — needs ICICLE harvest wired in (NEW)
```

**Layer 2 — concept_ontology.json** defines 35 concepts (`C01`–`C35`) each with:
- `book_chapter_anchors` — which of the 9 LE Toolkit chapters anchors it
- `topic_codes` — which T00–T17 topics it belongs to
- `prerequisites` — ordered learning dependencies
- `bloom_level` — cognitive target
- `primary_papers` — seed paper IDs (e.g. `LE-T1-008`)
- `primary_resources` — resource IDs including new `LE-IC-*` ICICLE resources

**35 concepts grouped by cluster:**
- Foundation (C01–C03): What is LE, LE vs ID, LE Teams
- Learning Science (C04–C08): How People Learn, Memory, Cognitive Load, Motivation, Transfer
- HCD & Process (C09–C12): HSI, Human-Centered Design, LE Process, Needs Analysis
- Measurement (C13–C17): EDM, Learning Analytics, Assessment, Decision Tracking, Evaluation
- Knowledge & Tech (C18–C22): KLI Framework, Competency Frameworks, ITS, Adaptive Systems, Infrastructure
- AI (C23–C24): Foundation Models in Ed, AI Ethics
- Simulation & Applied (C25–C29): Simulation, Games, XR, Expert Elicitation, Workforce Dev
- Evidence & Methods (C30–C32): Evidence Standards, Research Methods, Credentialing
- Context (C33–C35): High-Consequence Domains, Ethics & Equity, LE at Scale

---

## Remaining Work (in order)

### 1. `corpus/tables/icicle_resources_registry.json` — NEW FILE
~40 resources scraped from the ICICLE page, using IDs `LE-IC-001`–`LE-IC-040`.  
Schema matches `corpus/tables/programs_people_registry.json`:
```json
{
  "resource_id": "LE-IC-001",
  "status": "APPROVED",
  "content_type": "GL",
  "name": "...",
  "affiliation_or_venue": "IEEE ICICLE",
  "url": "...",
  "primary_topic": "T00",
  "secondary_topics": "",
  "description": "...",
  "notes": "Harvested from sagroups.ieee.org/icicle/resources/ Dec 2025"
}
```
Key resources to include (from ICICLE page scrape):
- `LE-IC-001` Learning Engineering for Online Education (book, Dede/Richards/Saxberg)
- `LE-IC-002` LE Process Description & Diagram (sagroups.ieee.org/icicle/learning-engineering-process/)
- `LE-IC-003` Learning Engineering Case Guide 1.0 (Google Slides)
- `LE-IC-004` Generalizable LE Adoption Maturity Model (PDF)
- `LE-IC-005` Five Whys Template (Google Doc)
- `LE-IC-006` Fishbone/Cause-Effect Analysis Template (Google Doc)
- `LE-IC-007` Performance Task Analysis Template (Google Doc)
- `LE-IC-008` LE Evidence Decision Tracker (Google Drive folder)
- `LE-IC-009` LE Implementation Checklist (Google Doc)
- `LE-IC-010` Examples of Roles & Expertise on an LE Team (Google Doc)
- `LE-IC-011` Learning Design Principles Toolkit (McEldoon, Google Drive)
- `LE-IC-012` Saxberg MIT Festival of Learning Keynote 2023 (YouTube)
- `LE-IC-013` QIP Learning Engineering Video Series (YouTube playlist)
- `LE-IC-014` Invitation to LE Webinar Series (ICICLE, YouTube)
- `LE-IC-015` IEEE Learning Engineering Podcast (PodServe/Spotify)
- `LE-IC-016` Silver Lining for Learning — Art & Science of LE ep. (podcast 2023)
- `LE-IC-017` Silver Lining for Learning — Human-Centered Methods ep. (podcast 2023)
- `LE-IC-018` Baker, Boser, Snow 2022 — LE: A View on Where the Field Is At (APA Open)
- `LE-IC-019` Craig et al. 2023 — LE Perspectives for Educational Systems (Sage)
- `LE-IC-020` Lee 2023 — Learning Sciences & LE: Natural or Artificial Distinction? (Taylor & Francis)
- `LE-IC-021` Kolodner 2023 — Learning engineering: What it is, why I'm involved (Taylor & Francis)
- `LE-IC-022` 7 Things to Know about Learning Engineering (EDUCAUSE 2018)
- `LE-IC-023` High-Leverage Opportunities for LE (Baker & Boser, 2021, The Learning Agency)
- `LE-IC-024` OpenSimon Community (CMU Simon Initiative)
- `LE-IC-025` MIT LEAP Group (Learning Engineering & Practice)
- `LE-IC-026` Playful Journey Lab / MITili (MIT)
- `LE-IC-027` The Learning Agency EdSurge Series (topic collection)
- `LE-IC-028` AECT Learning Engagement Activated Podcast — Jim Goodell ep. (2022)
- `LE-IC-029` Goodell 2019 — Are You Doing Learning Engineering or Instructional Design? (Learning Solutions)
- `LE-IC-030` SchoolSims platform (applies LE + CTA + NDM for teacher prep, 2025)
- `LE-IC-031` Learning Engineering at a Glance (Schatz, Goodell, Kessler 2023, Army Press)
- `LE-IC-032` State of XR & Immersive Learning Report 2021 (iLRN/ICICLE)
- `LE-IC-033` Data Use Throughout the LE Process (graphic/infographic, Google Drive)
- `LE-IC-034` Learning Engineering Adjacent Academic Programs (Google Doc directory)
- `LE-IC-035` Learning Engineering is a Team Sport (ICICLE 2024 presentation)
- `LE-IC-036` Teaming up to Improve Medical/Healthcare Education (Kurzweil & Marcellas 2020)
- `LE-IC-037` Build a Learning Data Dream Team (Torrance, Lin, Goodell 2024, ATD)
- `LE-IC-038` IDEO Design Thinking Process (ideou.com)
- `LE-IC-039` Van Campenhout et al. 2023 — Student-Centered Ed Data Science Through LE (Springer)
- `LE-IC-040` Herb Simon 1967 — The Job of a College President (Google Drive PDF)

### 2. `corpus/tables/concept_graph_seeds.json` — NEW FILE
Concept-level edges for the knowledge graph. Schema matches `knowledge_graph_seeds.json`:
```json
{ "node_type": "CONCEPT", "node_id": "C01", "node_label": "...", "edge_type": "BELONGS_TO", "edge_target": "T00", "edge_label": "..." }
{ "node_type": "CONCEPT", "node_id": "C05", "node_label": "...", "edge_type": "PREREQ_FOR", "edge_target": "C15", "edge_label": "..." }
```
Edge types needed:
- `BELONGS_TO` — concept → topic (35 edges)
- `PREREQ_FOR` — concept → concept (~25 edges, from the prereqs in concept_ontology.json)
- `BOOK_CHAPTER` — concept → chapter number annotation (~25 edges for book-anchored concepts)

### 3. `corpus/tables/learning_journeys.json` — UPDATE
Keep existing 4 journeys (J-01 through J-04) but:
- Add `concept_ids` field to each stage (e.g. `"concept_ids": "C01, C02"`)
- Add **J-05: AI/EdTech Practitioner** (5 stages: C01→C04→C18→C20→C23→C24→C14)
- Add **J-06: Getting Up to Speed Fast** (3-stage express path: C01, C04, C11, C17 — for the time-pressed professional)

### 4. `scripts/build_dataset.py` — EDIT (not rewrite)
Add two functions and wire them into the main build:

**A. `load_icicle_registry()`** — reads `corpus/tables/icicle_resources_registry.json`, merges into the `rows` list inside `build_resources()`. Insert after line ~1362:
```python
icicle_path = CORPUS_DIR / "tables" / "icicle_resources_registry.json"
if icicle_path.exists():
    rows = rows + load_json(icicle_path)
```

**B. `build_concept_graph(concepts, topic_codes, paper_ids, resource_ids)`** — creates concept nodes and edges. Call from inside `build_graph()` after line ~1620. Returns `(concept_nodes, concept_edges)` to be merged into `nodes`/`edges`.

Node structure for a concept:
```python
{
    "id": concept["concept_id"],
    "label": concept["name"],
    "type": "concept",
    "hop": 0,
    "topic_codes": concept.get("topic_codes", []),
    "provenance": {
        "book_chapters": concept.get("book_chapter_anchors", []),
        "bloom_level": concept.get("bloom_level", ""),
        "layer": "concept",
    },
}
```
Edge types emitted: `has_concept` (topic→concept), `prereq` (concept→concept), `anchored_by` (concept→paper), `learn_via` (concept→resource).

Also read `concept_graph_seeds.json` in the same pass as `knowledge_graph_seeds.json`.

### 5. `LEARNING_CONCEPT_ONTOLOGY.md` — NEW FILE
Human-readable reference. Sections:
- Overview of the three-layer model
- Table of all 35 concepts with cluster, book chapter, prerequisites, Bloom level
- Per-concept detail (name, why it matters, key questions, primary resources)
- Three learner pathways quick-reference

### 6. `RESOURCE_CURATOR_TEMPLATE.md` — NEW FILE
How to add new resources to the KB. Sections:
- When to add a resource (quality criteria)
- How to assign a resource ID (`LE-IC-NNN` for ICICLE harvests, `LE-PP-NNN` for programs/people)
- Required fields and examples
- How to bind a resource to concepts (update `concept_ontology.json`)
- How to trigger a rebuild

---

## Key Design References

| Document | Location | Purpose |
|----------|----------|---------|
| MSKB three-layer architecture | [wrgr/mskb README](https://github.com/wrgr/mskb) | The methodology being applied |
| MSKB concept ontology example | `wrgr/mskb LEARNING_CONCEPT_ONTOLOGY.md` | Schema and style guide |
| MSKB resource curator template | `wrgr/mskb RESOURCE_CURATOR_TEMPLATE.md` | Curation workflow |
| LE concept ontology (Layer 2) | `corpus/tables/concept_ontology.json` ✅ | 35 concepts, written |
| LE topic map (Layer 1 taxonomy) | `corpus/tables/topic_map.json` | 18 topics T00–T17 |
| LE existing resources | `corpus/tables/programs_people_registry.json` | 26 existing resources |
| LE existing graph seeds | `corpus/tables/knowledge_graph_seeds.json` | Topic-level edges |
| ICICLE resources page (scraped) | https://sagroups.ieee.org/icicle/resources/ | Source for LE-IC-* entries |
| Build pipeline entry point | `scripts/build_dataset.py` | Main graph construction |

---

## Quick Start for Next Session

```
cd learning-engineering-resources
git checkout claude/rebuild-knowledge-graph-Q1Fa3

# Files to write next (in order):
1. corpus/tables/icicle_resources_registry.json   (~40 entries, see list above)
2. corpus/tables/concept_graph_seeds.json         (concept edges)
3. corpus/tables/learning_journeys.json           (add concept_ids fields, J-05, J-06)
4. scripts/build_dataset.py                       (edit: add concept layer, ICICLE registry reader)
5. LEARNING_CONCEPT_ONTOLOGY.md
6. RESOURCE_CURATOR_TEMPLATE.md

# Then test the build:
python3 scripts/build_dataset.py

# Then push:
git add -A && git commit -m "..." && git push -u origin claude/rebuild-knowledge-graph-Q1Fa3
```
