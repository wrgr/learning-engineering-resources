# Corpus Construction Methodology for Domain Knowledge Bases
## A Bibliometrically-Grounded Framework

*Version 1.0 | April 2026*
*Companion to: MS Knowledge Base Corpus Design Decisions*

---

## Purpose

This document describes a general methodology for constructing curated literature corpora intended to ground domain-specific AI knowledge bases, retrieval-augmented generation (RAG) systems, or structured learning resources. It is designed to be reusable across domains.

The methodology draws on established principles from bibliometrics, information science, and knowledge organization. Where design choices are made, the reasoning and supporting literature are documented so that practitioners can evaluate, adapt, or challenge them for their own domain.

---

## 1. The Core Problem: From Seeds to Corpus

A knowledge base corpus requires selecting a subset of a field's literature that is:

1. **Representative** — covering the field's canonical topics without systematic gaps
2. **Coherent** — internally consistent in scope and intellectual framing
3. **Balanced** — not over-representing dominant subfields, institutions, or methodologies at the expense of important minorities
4. **Auditable** — every document's inclusion can be justified with a specific rationale
5. **Updatable** — the selection process can be re-run as the field evolves

No automated process fully satisfies all five criteria. This methodology combines algorithmic filtering with structured human judgment, using each where it has comparative advantage.

---

## 2. Theoretical Foundations

### 2.1 Citation Analysis as Knowledge Organization

The use of citation networks to organize scientific knowledge has a long history in information science. Co-citation, defined as the frequency with which two documents are cited together, was introduced by Small (1973) as a new measure of the relationship between documents. The intuition is that the scientific community's collective citation behavior encodes semantic relationships: papers cited together are being used together to build arguments, and therefore are intellectually related.

**Key reference:** Small H. Co-citation in the scientific literature: A new measure of the relationship between two documents. *Journal of the American Society for Information Science* 1973;24(4):265–269. DOI: 10.1002/asi.4630240406

The complementary measure, bibliographic coupling (Kessler 1963), identifies similarity through shared references rather than shared citations: two papers that cite many of the same predecessors are likely working on related problems. Bibliographic coupling occurs when two works reference a common third work in their bibliographies, with coupling strength increasing with the number of shared references.

**Key reference:** Kessler MM. Bibliographic coupling between scientific papers. *American Documentation* 1963;14(1):10–25. DOI: 10.1002/asi.5090140103

### 2.2 Which Citation Approach Best Represents the Research Front?

Boyack and Klavans (2010) compared co-citation analysis, bibliographic coupling, direct citation, and hybrid approaches across 2,153,769 biomedical articles, finding that bibliographic coupling slightly outperforms co-citation analysis using both within-cluster textual coherence and concentration measures; direct citation is the least accurate mapping approach by far.

This finding is important for corpus construction: bibliographic coupling — which identifies papers that share predecessors — is better at capturing the current research front, while co-citation — which identifies papers that are cited together — better captures historically established relationships. For a knowledge base intended to support current practitioners, bibliographic coupling has advantages; for foundational coverage, co-citation is stronger. The methodology described here uses a hybrid approach that captures both.

**Key reference:** Boyack KW, Klavans R. Co-citation analysis, bibliographic coupling, and direct citation: Which citation approach represents the research front most accurately? *Journal of the American Society for Information Science and Technology* 2010;61(12):2389–2404. DOI: 10.1002/asi.21419

### 2.3 Graph Centrality and Structural Importance

Raw citation counts are a poor proxy for field importance because they conflate popularity with influence and are highly field-dependent. A paper with 200 citations in a small subfield may be more important to that subfield than a paper with 2,000 citations in a large one.

PageRank — originally developed for web ranking by Brin and Page (1998) — provides a structurally-grounded alternative. PageRank partially addresses citation count limitations because it does not ignore the importance of citing papers: a citation from a ground-breaking, highly cited work carries more weight than one from an obscure paper. Additionally, the number of citations is ill-suited to compare the impact of papers from different scientific fields due to widely varying citation practices.

When computed on a domain-specific citation subgraph rather than the full literature, PageRank identifies papers that are structurally central within the domain — papers that serve as hubs connecting diverse parts of the field — regardless of absolute citation count or institutional origin.

**Key reference:** Brin S, Page L. The anatomy of a large-scale hypertextual web search engine. *Computer Networks and ISDN Systems* 1998;30:107–117.

### 2.4 Within-Subdomain Normalization

Citation counts vary systematically across subfields. An average paper is cited approximately 6 times in life sciences, 3 times in physics, and less than 1 time in mathematics. Within a single domain like medicine, clinical trial papers typically accumulate far more citations than qualitative studies, implementation science papers, or equity research — not because they are more important but because citation practices differ.

Using raw citation counts to rank papers across subdomains systematically disadvantages methodologically distinct subfields. Within-subdomain percentile normalization corrects this by asking "how important is this paper relative to its peers?" rather than "how many citations does it have?" This is consistent with the Leiden Manifesto's principle that metrics should be adjusted for field differences.

**Key reference:** Hicks D, Wouters P, Waltman L, de Rijcke S, Rafols I. Bibliometrics: The Leiden Manifesto for research metrics. *Nature* 2015;520(7548):429–431. DOI: 10.1038/520429a. PMID: 25903611

### 2.5 Citation Velocity as a Leading Indicator

Established citation counts measure historical influence. Citation velocity — the rate at which a paper is accumulating citations — provides a leading indicator of emerging importance, identifying papers that the field is beginning to treat as important before they have accumulated the citation mass of established works. This is particularly valuable for:

- Capturing work from early-career researchers and non-dominant institutions before it becomes well-known
- Identifying emerging paradigm shifts before they are consolidated in review articles
- Ensuring the corpus does not systematically lag the field by 5–10 years

Velocity = citations received in last N years / paper age in years. The choice of N (recommended: 2 years) reflects a balance between signal (long enough for meaningful accumulation) and recency (short enough to identify genuinely emerging work).

---

## 3. The Pipeline Architecture

### Step 0: Seed Selection

Seeds are manually curated anchor documents representing the field's canonical topics. They serve three functions:

1. **Conceptual anchors** — defining the intellectual scope of the corpus
2. **Citation network origins** — expansion sources for algorithmic candidate generation
3. **Quality anchors** — the reference points against which candidate connectivity is measured

**Seed selection criteria:**
- Explicit topic coverage: every major topic in the domain's orientation map should have at least two seeds
- Diversity of document type: seeds should represent consensus/guideline, systematic review, landmark trial, natural history, mechanistic review, epidemiological, equity/SDOH, and advocacy document types proportionally
- Author and institutional diversity: seeds should not over-represent any single research group, country, or institution
- Recency balance: seeds should include both foundational anchors (papers that established the conceptual frame) and current papers (papers reflecting the present state of the field)

Seeds are the primary quality gate for the entire pipeline. A poor seed set cannot be compensated by algorithmic sophistication downstream.

### Step 1: Expansion Source Augmentation

In addition to seeds, include a small set (5–8) of high-quality, comprehensive review articles as expansion sources. These serve a distinct function from seeds: they are hub documents with large, expertly curated reference lists that extend the algorithmic candidate pool into areas that may not be well-connected to the seed set.

**Selection criteria for review expansion sources:**
- Comprehensive scope: covering the field broadly rather than a single topic
- High authority venue
- Recent enough to capture the current literature (within 5–7 years)
- Institutionally and geographically diverse authorship
- Covering topics with thin seed coverage (equity, implementation science, global burden)

**Critical constraint:** Review articles are expansion sources only. Cross-seed connectivity is scored against seeds, not review articles. A paper that appears only in a review article's reference list but has no connection to any seed has not earned structural importance in the field's citation network and should not pass the connectivity filter automatically.

### Step 2: One-Hop Expansion

Perform one-hop citation expansion from all expansion sources (seeds + review anchors):
- **Backward citations:** papers cited by the source (the source's reference list)
- **Forward citations:** papers that cite the source (the source's citing papers)

Both directions are necessary. Backward captures the papers a source treats as foundational; forward captures the papers the field has recognized as building on the source.

**Implementation:** OpenAlex API (api.openalex.org) provides free, open access to citation data for the vast majority of academic literature. It is the recommended implementation platform.

**Reference:** Priem J, Piwowar H, Orr R. OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. *arXiv preprint* 2022; arXiv:2205.01833.

Expected candidate pool size: 5,000–15,000 papers depending on domain and seed set size.

### Step 3: Cross-Seed Connectivity Filter

For each candidate paper, compute:

```
cross_seed_score = count of seeds (not review anchors) in whose
                  one-hop neighborhood the candidate appears
```

**Threshold:** Retain candidates with cross_seed_score ≥ 2 for Tier 2. Relax to ≥ 1 for Tier 3 (velocity-selected emerging papers).

**Rationale:** A paper appearing in the neighborhood of multiple seeds has structural importance in the field's citation network, independent of which institution produced it or what its absolute citation count is. This is the most defensible selection criterion because it is grounded in the collective citation behavior of the field itself rather than any single metric.

**Multi-topic bridge signal:** Record when a candidate's connected seeds span multiple topic areas. These bridging papers are often the most valuable in a knowledge base — they enable cross-topic queries that would otherwise fail.

### Step 4: Topic Assignment

Assign each surviving candidate to topic categories:
- **Primary topic** (required, one only): the topic this paper most centrally addresses
- **Secondary topics** (optional, 0–3): topics for which the paper has substantive content — dedicated methods, results, or discussion sections — not merely citations or passing mentions

Multi-topic assignment enables papers to compete in multiple subdomain citation percentile calculations, which is essential for papers that legitimately bridge topic areas. The content test distinguishes genuine cross-topic relevance from superficial citation overlap.

### Step 5: Within-Subdomain Citation Score

For each assigned topic T:

```
citation_percentile(paper, T) = percentile rank of paper's citation count
                                 among all candidates assigned to T

velocity_percentile(paper, T) = percentile rank of paper's citation velocity
                                  among all candidates assigned to T

subdomain_score(paper, T) = max(citation_percentile(paper, T),
                                 velocity_percentile(paper, T))
```

Retain candidates where subdomain_score ≥ topic_threshold in any assigned topic.

**Threshold setting:** Set topic thresholds to yield the target document count for each topic in the orientation map. Thresholds will differ across topics because candidate pool sizes differ. This is correct and intentional: different thresholds reflect different subdomain sizes, not differential quality standards.

The max() function ensures that papers important by either historical citation accumulation or current velocity are captured, without requiring both simultaneously. A foundational paper with high citation count but low velocity and a new paper with high velocity but modest total citations are both retained by their respective criteria.

### Step 6: Emerging Literature (Tier 3)

Run a separate pass for recent papers (e.g., published within 4 years) using velocity_percentile ≥ 80th as the primary filter, with cross_seed_score ≥ 1 as a relaxed connectivity floor.

This tier is the mechanism for:
- Capturing important work from non-dominant researchers before it becomes well-cited
- Catching emerging paradigm shifts not yet reflected in seed neighborhoods
- Preventing systematic lag in the corpus relative to the field's frontier

Manual review is required for Tier 3 candidates to confirm genuine relevance.

### Step 7: Expert Signal Tier (Tier 4)

A small, high-precision set of documents selected by explicit expert signals:
- Conference best paper awards from the field's primary meetings
- Research priority documents from field-level advocacy and funding organizations
- Explicitly underrepresented population/geographic cohort studies (manual identification required — algorithmic methods systematically miss these)
- Documents cited in the field's strategic planning documents

Every Tier 4 document must have its selection source documented. No algorithmic filter applies to this tier. Keep it small (5–15% of corpus) so every document is individually defensible.

### Step 8: Manual Review and Balance Check

Review all algorithmic candidates:
1. **Topic balance**: does each topic approach its target count?
2. **Source diversity**: do non-dominant institutions and non-Western contexts appear?
3. **Document type balance**: are all document types represented proportionally?
4. **Patient/community voice**: are patient-generated or community-partnership documents represented where relevant?

Set status = APPROVED or REJECTED (with documented reason) for each document.

---

## 4. Quality Assurance

### 4.1 QA Overlap Check

After pipeline completion, for each review anchor, compute:

```
overlap_pct = (anchor's references in final corpus) / (total anchor references)
```

Expected result: >70% overlap per anchor. Interpretation:
- >70% — seeds are well-chosen and the pipeline is capturing the field correctly
- 60–70% — acceptable, monitor
- <60% for a specific topic — seeds are thin for that topic; augment seeds or add manual documents

Papers in anchor reference lists not in the corpus should be reviewed individually.

### 4.2 Structural Validity of Seed Selection

Seeds can be validated by checking that: (a) the orientation map topic coverage is complete, (b) review anchor overlap percentages are in the expected range, and (c) the cross-seed connectivity score distribution of the final corpus is not bimodal (if it is, seeds may be clustered into disconnected subcommunities).

### 4.3 Known Limitations

Every corpus construction methodology has systematic biases that should be documented:

- **Recency bias of velocity filter**: very recent papers have inflated velocity scores that decay as the field catches up
- **English-language bias**: OpenAlex has better coverage of English-language literature; non-English publications are systematically underrepresented
- **Institutional bias**: papers from well-connected institutions accumulate cross-seed connectivity faster than equivalent papers from peripheral institutions
- **Document type imbalance**: RCTs and basic science papers generate more citations than qualitative studies, implementation science, or policy documents, creating systematic under-representation of these document types if not corrected by subdomain normalization
- **Grey literature gap**: conference abstracts, preprints, and advocacy documents are not well-covered by citation APIs and require explicit Tier 4 mechanisms

Document all known gaps in a Gap Tracker as part of the corpus specification.

---

## 5. Metadata Schema Requirements

Every document in the corpus should carry metadata sufficient to:
1. Justify its inclusion (selection tier, cross-seed score, subdomain score)
2. Route queries appropriately (topic assignment, document type, evidence type)
3. Flag recency concerns (recency flag, year, velocity score)
4. Contextualize findings (geographic scope, population)
5. Enable audit (selection source, reviewed by, date reviewed)

The metadata schema should be designed before ingestion begins, not retrofitted afterward. See the companion domain-specific document for a complete field-by-field schema definition.

---

## 6. Adaptations for Different Domains

This methodology was developed in a biomedical context but is domain-agnostic. Key adaptations when applying to other domains:

**Humanities and social sciences:** Citation norms differ substantially. Books are more important than journal articles; citation accumulation is slower; the velocity window may need to extend to 5 years rather than 2. Adjust thresholds accordingly.

**Engineering and applied sciences:** Conference proceedings are primary venues alongside journals. Expand expansion sources to include major conference proceedings.

**Policy and practice domains:** Grey literature (government reports, agency guidelines, advocacy documents) is more important. Tier 4 should be proportionally larger. Citation APIs have poor coverage; manual identification is more important.

**Rapidly evolving fields (AI, genomics):** Preprints are an important signal. Consider including bioRxiv/arXiv via velocity as a Tier 3 source with appropriate caveats about preprint quality.

**Fields with strong international diversity:** The equity concern about non-Western literature is not unique to medicine. Explicitly allocate Tier 4 slots to non-Western cohort studies and non-English publications in any domain where geographic diversity matters.

---

## 7. Implementation Tools

**Citation data:** OpenAlex API (api.openalex.org) — free, open, no authentication required for standard queries. Priem J, Piwowar H, Orr R. arXiv:2205.01833 (2022).

**PageRank on citation subgraphs:** Python NetworkX library (`nx.pagerank()`). Computationally tractable for subgraphs up to ~50,000 nodes on standard hardware.

**Visualization:** VOSviewer or CiteSpace for citation network visualization during quality review.

**Tracking:** The companion corpus specification workbook provides the schema, registry, and gap tracker in a single auditable Excel file.

---

## 8. Reference Summary

| Reference | Role in methodology |
|-----------|-------------------|
| Small 1973, *JASIS* 24:265–269 | Foundational basis for co-citation as knowledge organization |
| Kessler 1963, *American Documentation* 14:10–25 | Foundational basis for bibliographic coupling |
| Boyack & Klavans 2010, *JASIST* 61:2389–2404 | Empirical comparison of citation approaches; basis for hybrid approach |
| Brin & Page 1998, *Computer Networks* 30:107–117 | PageRank algorithm; basis for subgraph structural importance |
| Hicks et al. 2015, *Nature* 520:429–431 | Leiden Manifesto; basis for within-field normalization and responsible metrics use |
| Priem et al. 2022, *arXiv*:2205.01833 | OpenAlex API; recommended implementation platform |

---

*This document is intended as a living methodological reference. Update the version number and document changes in the Update Log of the associated corpus specification workbook when the methodology evolves.*
