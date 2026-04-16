# Learning Engineers Study — Query Provenance Log

**Study goal:** Identify individuals who self-apply the title "learning engineer" (or close variants) across professional and academic networks.  
**Study date:** 2026-04-14  
**Lead:** [redacted]  
**Branch:** `claude/learning-engineers-research-7Ij1K`

---

## Why finding learning engineers is hard

"Learning engineer" is an **emerging, contested job title** — unlike "software engineer" or "teacher", no professional body certifies or standardizes it. This creates three compounding problems:

**1. Title fragmentation.** The same role appears under many names:
- Learning engineer / learning engineering specialist
- Instructional designer / instructional systems designer (ISD)
- Learning experience designer (LXD)
- Learning scientist / learning researcher
- Curriculum designer / curriculum technologist
- Educational technologist / ed-tech specialist
- *Ingénieur pédagogique* (French), *Ingenieur für Lerndesign* (German)

Many experienced practitioners do learning engineering work under these older titles and would not surface in a "learning engineer" search.

**2. ML/AI contamination is high.** "Learning engineer" sounds like a machine learning role. A naive search returns a large fraction of deep learning, reinforcement learning, NLP, and MLOps engineers — especially on Twitter/X and GitHub. Query-level exclusions help but don't eliminate the problem; our auto-triage pattern catches what slips through (~7–8% of LinkedIn records flagged).

**3. Network and platform bias.** Each source covers a different slice:
- **LinkedIn**: strong for US/UK/France practitioners; weak for government/defense/academic-only researchers; results are biased toward the searcher's 3rd-degree network
- **GitHub**: over-indexes on technical implementers; most learning engineers don't maintain a public GitHub presence
- **ResearchGate / Google Scholar**: covers researchers who publish; invisible to practitioners who don't write papers
- **Twitter/X**: self-reported bios only; many practitioners are not active; API access now constrained
- **Brave/web search**: sparse for individual people; `site:linkedin.com/in` rarely reproduces the headline verbatim in snippets

---

## What worked

| Approach | Yield | Quality | Notes |
|---|---|---|---|
| LinkedIn PhantomBuster — title + keyword search | 173 records | Good — ~92% true LE self-IDs | Most efficient single source; covers US, Europe, Global South |
| ResearchGate Google site: search | ~20 results → 13 usable | High — all explicit self-IDs | Good for academic practitioners; limited scale |
| Google Scholar search | ~25 results → 4 new records | Mixed | Surfaced co-author panels, not just profiles; deduplicated 1 |
| Auto-triage false-positive filter | Caught 13/173 LI records | Good | Saved manual review time; regex patterns reusable across sources |

LinkedIn was the **highest-leverage single action**: one PhantomBuster run on a pre-filtered "learning engineer distill" list of 173 returned structured data across 4 pages in minutes. The title-all sub-list (people with LE explicitly as their current title) was the cleanest signal.

---

## What didn't work / known gaps

| Issue | Impact | Mitigation |
|---|---|---|
| Brave web search per-company | 1 record from 131 companies | Snippets rarely reproduce LinkedIn headlines verbatim; structural limitation of the approach |
| LinkedIn email enrichment | 0 emails collected | Requires paid PhantomBuster enrichment step or separate tool |
| No coverage of practitioners who use older titles | Unknown but likely large | Needs a follow-on search on "instructional designer" + "data-driven" / "evidence-based" / "learning science" |
| Government / defense under-indexed | Several USAF records found by accident; probably many more | USAF, Army, DoD agencies have internal LEs who don't publish LinkedIn profiles |
| Non-English queries not run | Strong French community visible (8+ records) but no targeted French/Arabic/German/Spanish query | Run separate queries for *ingénieur pédagogique*, *ingeniero de aprendizaje*, etc. |
| Twitter/X not yet run | Unknown | Prepared; query and exclusion patterns ready |
| LinkedIn result cap | PhantomBuster returned exactly 173 records (matching the UI count) | This may be a platform cap on the specific filtered list; a broader un-filtered run might surface more |

---

## Is LinkedIn sufficient?

**For practitioners in industry and higher education: mostly yes**, with caveats:
- US/UK/Western Europe coverage appears good
- Emerging markets coverage is thin but growing (India, Philippines, Kenya, Brazil visible)
- A second LinkedIn run with alternate title variants ("learning experience engineer", "instructional engineer") would add coverage

**For researchers and academics: no** — RG and GS are needed; many LE researchers don't self-label on LinkedIn

**For government/defense: no** — this population is systematically under-indexed across all platforms

**Recommendation:** LinkedIn + one RG/GS pass + Twitter/X gives ~80% coverage for the practitioner community. Reaching the government/defense and pure-academic populations requires targeted outreach (conference contacts, task analysis interviews) rather than scraping.

---

## Methodology artifacts

| File | Purpose |
|------|---------|
| `titlesearch/data/companies.json` | Curated company seed list (~120 orgs, 11 tiers); read by scraper scripts |
| `scripts/github_le_search.py` | GitHub bio search via date-range bisection; writes to `titlesearch/data/raw/GH_bio_search_DATE.jsonl` |
| `scripts/web_le_search.py` | Brave Search per-company queries; writes to `titlesearch/data/raw/WS_company_search_DATE.jsonl` |

Run commands:
```bash
# GitHub (requires GITHUB_TOKEN env var)
python3 scripts/github_le_search.py

# Web search per company (requires BRAVE_API_KEY env var)
python3 scripts/web_le_search.py --tiers 1 2   # specific tiers
python3 scripts/web_le_search.py                # all tiers
```

---

## Source inventory

| Source ID | Platform | Access method | Known limitations |
|-----------|----------|---------------|-------------------|
| LI | LinkedIn | PhantomBuster + Business trial | US-biased; trial may be rate-limited; incomplete global coverage |
| GH | GitHub | GitHub search API / manual | Self-reported bios only; skews technical |
| GS | Google Scholar | Manual / API | Only surfaces published authors; sparse for practitioners |
| RG | ResearchGate | Manual | Academic bias; subset of GS population |
| WS | Brave Search | Brave API | Broad but unstructured; coverage varies |
| TW | Twitter/X | Manual / API | Self-reported bios; API access constrained |

---

## Query log

Each entry records one discrete search action. `raw_file` links to the file in `titlesearch/data/raw/` containing unprocessed results.

---

### Q001
- **Date:** 2026-04-14
- **Source:** LI (LinkedIn)
- **Query type:** Keyword search
- **Scope:** United States
- **Query string:** `"learning engineer"`
- **Filters:** Title field only (PhantomBuster title scrape)
- **Result count:** _[to be filled]_
- **Raw file:** `titlesearch/data/raw/Q001_LI_keyword_US.jsonl`
- **Notes:** First pass; US-scoped to test completeness before global run.

---

### Q002
- **Date:** 2026-04-14
- **Source:** RG (ResearchGate via Google site: search)
- **Query type:** Google site-scoped keyword search
- **Scope:** Global
- **Query string:** `site:researchgate.net/profile "learning engineer" -"machine learning" -"deep learning" -"reinforcement learning"`
- **URL:** `https://www.google.com/search?q=site:researchgate.net/profile+%22learning+engineer%22+-%22machine+learning%22+-%22deep+learning%22+-%22reinforcement+learning%22&start=10`
- **Result count:** ~20 shown (Google suppressed additional similar results; `start=10` = page 2 of results — **page 1 not yet captured**)
- **Raw file:** `titlesearch/data/raw/Q002_RG_google_site_search_p2.jsonl`
- **Included in CSV:** 13 records (10 explicit self-ID; 3 probable self-ID with truncated snippets)
- **Skipped:** 3 records (Rod Roscoe — descriptive panel context; Volodymyr Kukharenko — article about concept; Priyavrat Thareja — metaphorical usage); 2 publication-only results (no person profile)
- **Notes:** URL in paste shows start=10 (page 2) but user confirmed both pages were captured in the same paste; all ~20 results are logged. Three ASU people (McCaleb, Oster, Jongewaard) co-author a Jan 2026 chapter and all use "As learning engineer…"; snippets truncated so title confirmation pending. Blakesley formerly at CMU Eberly Center per a separate PDF in the same SERP.

---

### Q003
- **Date:** 2026-04-14
- **Source:** GS (Google Scholar via Google search)
- **Query type:** Google Scholar keyword search (query string not captured — reconstruct from context)
- **Scope:** Global
- **Query string:** Not provided; inferred as `"learning engineer"` on Google Scholar (similar exclusion filters to Q002 likely applied)
- **URL:** Not captured
- **Result count:** ~15 results page 1 (per Google's "omitted entries similar to the 15 already displayed" note) + 10 results page 2; both pages captured across two sequential pastes
- **Raw file:** `titlesearch/data/raw/Q003_GS_google_scholar_both_pages.jsonl`
- **New people added to people.json:** 4 (Lauren Totino, Tyree Cowell, Kyoung Whan Choe, Yongsung Kim); Gautam Yadav already in registry as LE-P-001
- **Notes:** GS surfacing mechanism is distinct from RG — query hits co-author panels on other people's profiles, so many results are profile *subjects* who are not learning engineers themselves but have an LE person in their network. Yongsung Kim's title "Machin Learning Engineer" is an apparent typo for "Machine Learning Engineer" — different field, triage=no. Kyoung Whan Choe ("Robot Learning Engineer") is a title variant worth tracking. Page 1 appeared to have ~15 results but only the last 5 were captured in the paste; full page 1 content may be incomplete.

---

<!-- Add new query blocks here. Copy the template below. -->

### Q004
- **Date:** 2026-04-14
- **Source:** LI (LinkedIn)
- **Query type:** Keyword search — broad term exclusions
- **Scope:** Global
- **Query string:** `"learning engineer" NOT ("machine" OR "deep" OR "robot" OR "reinforcement")`
- **URL:** `https://www.linkedin.com/search/results/people/?keywords=%22learning%20engineer%22%20NOT%20%28%22machine%22%20OR%20%22deep%22%20OR%20%22robot%22%20OR%20%22reinforcement%22%29&origin=FACETED_SEARCH`
- **Run count:** 1
- **Result count:** _[to be filled when results pasted]_
- **Raw file:** `titlesearch/data/raw/Q004_LI_keyword_global_broad_exclusions.jsonl`
- **Notes:** Broadest exclusion set — single words rather than phrases, so e.g. any profile mentioning "machine" at all is excluded; may over-exclude. Results to follow.

---

### Q005
- **Date:** 2026-04-14
- **Source:** LI (LinkedIn)
- **Query type:** Keyword search — phrase exclusions
- **Scope:** Global
- **Query string:** `"learning engineer" NOT ("machine learning" OR "reinforcement learning" OR "robot learning" OR "deep learning")`
- **URL:** `https://www.linkedin.com/search/results/people/?keywords=%22learning%20engineer%22%20NOT%20%28%22machine%20learning%22%20OR%20%22reinforcement%20learning%22%20OR%20%22robot%20learning%22%20OR%20%22deep%20learning%22%29&origin=TYPEAHEAD_ESCAPE_HATCH`
- **Result count:** _[to be filled when results pasted]_
- **Raw file:** `titlesearch/data/raw/Q005_LI_keyword_global_phrase_exclusions.jsonl`
- **Notes:** Narrower exclusion logic than Q004 (full phrases, not single words); should retain more true LE results. Origin=TYPEAHEAD_ESCAPE_HATCH suggests it was entered via the main search bar.

---

### Q006
- **Date:** 2026-04-14
- **Source:** LI (LinkedIn)
- **Query type:** Title field search — phrase exclusions
- **Scope:** Global
- **Query string:** `title:"learning engineer" NOT ("machine learning" OR "reinforcement learning" OR "robot learning" OR "deep learning")`
- **URL:** `https://www.linkedin.com/search/results/people/?keywords=title%3A%22learning%20engineer%22%20NOT%20%28%22machine%20learning%22%20OR%20%22reinforcement%20learning%22%20OR%20%22robot%20learning%22%20OR%20%22deep%20learning%22%29&origin=GLOBAL_SEARCH_HEADER`
- **Result count:** _[to be filled when results pasted]_
- **Raw file:** `titlesearch/data/raw/Q006_LI_title_global_phrase_exclusions.jsonl`
- **Notes:** Title-scoped search; most precise of the three LI queries — requires "learning engineer" to appear in the job title field specifically. Should yield highest-confidence self-IDs.

---

### Q007
- **Date:** 2026-04-14
- **Source:** WS (Brave Search API)
- **Query type:** Per-company web search — two queries per company (open web + `site:linkedin.com/in`)
- **Scope:** Global (131 companies, all tiers)
- **Query strings (per company):**
  1. `"{company}" "learning engineer" -"machine learning" -"reinforcement learning" -"deep learning"`
  2. `site:linkedin.com/in "learning engineer" "{company}" -"machine learning"`
- **Script:** `scripts/web_le_search.py` (run via `BRAVE_API_KEY=… python3 scripts/web_le_search.py`)
- **Result count:** 1 extracted person record; all 131 companies searched
- **Raw file:** `titlesearch/data/raw/WS_company_search_2026-04-14.jsonl`
- **Person found:** Charlotte Bell — "Learning Engineer, Cognitive and Behavioural Specialist" at Multiverse (UK); LinkedIn: `linkedin.com/in/charlotte-d-bell/`
- **Notes:** Low yield is structural, not a script bug. Brave snippets for `site:linkedin.com/in` results rarely reproduce the LinkedIn headline verbatim — they typically show description/recommendation text where the company name appears, but not the "Learning Engineer" headline. The extractor requires "learning engineer" in the combined title+snippet text (`is_le_hit`), so hits without the title in the snippet are silently dropped. Charlotte Bell's result succeeded because Brave happened to reproduce her full LinkedIn page title ("Charlotte Bell - Learning Engineer … - Multiverse | LinkedIn") in the snippet. To improve yield: (1) relax `is_le_hit` for `site:linkedin.com/in` URLs where the Brave result *title* (not just snippet) contains "learning engineer", or (2) log all raw Brave result titles so manual review is possible.

---

### Q008
- **Date:** 2026-04-14
- **Source:** WS (Brave Search API)
- **Query type:** Per-company web search — query-level ML exclusions removed; filtering delegated to `is_le_hit()` post-retrieval
- **Scope:** Global (131 companies, all tiers)
- **Query strings (per company):**
  1. `"{company}" "learning engineer"`
  2. `site:linkedin.com/in "learning engineer" "{company}"`
- **Script:** `scripts/web_le_search.py` (after fix to `build_queries()` removing `-"machine learning"` etc.)
- **Result count:** 3 extracted person records
- **Raw file:** `titlesearch/data/raw/WS_company_search_2026-04-14_v2.jsonl`
- **People found:**
  - Charlotte Bell — "Learning Engineer, Cognitive and Behavioural Specialist" at Multiverse (UK); `linkedin.com/in/charlotte-d-bell/` (also in Q007)
  - Avi Chawla — "Senior Learning Engineer" at Carnegie Mellon University; `linkedin.com/in/avi-chawla-40265357/` (**new**)
  - Qinglin Feng — "Learning Engineer @ CMU | METALS '22" at Carnegie Mellon University; `linkedin.com/in/qinglin-feng/` (**new**)
- **Notes:** Removing query-level exclusions improved yield from 1 → 3 records, but the structural ceiling remains: Brave snippets for `site:linkedin.com/in` results only reproduce the LinkedIn headline verbatim in a small fraction of cases. All three hits succeeded because the Brave page title contained the full "Name - Learning Engineer … | LinkedIn" string. The two new records are both CMU (expected — CMU coined the title and METALS alumni are active on LinkedIn). Brave web search is confirmed as a low-yield supplemental source; LinkedIn PhantomBuster remains the primary instrument.

---

### Q009
- **Date:** 2026-04-14
- **Source:** WS (Brave Search API) + direct page fetch
- **Query type:** Alumni directory scrape — CMU METALS program + ASU Learning Engineering Institute team page
- **Scope:** CMU METALS Classes 2014–2025; ASU LEI team
- **URLs fetched:**
  - `https://metals.hcii.cmu.edu/alumni/` — METALS alumni directory
  - `https://learningengineering.asu.edu/our-team/` — ASU LEI affiliates
- **Result count:** 7 new records added (LE-P-205 through LE-P-211); 7 already in registry from prior queries
- **New people added:**
  - LE-P-205 Michael Sambou — Associate Learning Engineer, CMU (METALS '25)
  - LE-P-206 Xiaolin Ni — Learning Engineer, CMU (METALS '23)
  - LE-P-207 Safiyyah Scott — Learning Engineer, CMU (METALS '23)
  - LE-P-208 Gabriel Winter Clark — Learning Engineer, CMU (METALS '22)
  - LE-P-209 Caitlin Lim — Learning Engineer, OLI/CMU (METALS '21)
  - LE-P-210 Zachary Mineroff — Assistant Director of Learning Engineering, CMU (METALS '18)
  - LE-P-211 Erin Czerwinski — Manager, Learning Engineering, CMU Simon Initiative/OLI (staff, not METALS; confirmed via EDUCAUSE profile)
- **Already in registry (skipped):** Qinglin Feng (LE-P-204), Manvi Teki, Yue Wang, Tyree Cowell, Henry Chang, Gautam Yadav (LE-P-001), Harley Chang, Tanvi Domadia
- **ASU LEI notes:** `learningengineering.asu.edu/our-team/` lists 73 affiliates by name only — no titles rendered in the page. Individual profile visits would be required. One METALS '20 alumna (Lilian Gong) is listed as "Research Professional" at ASU — connection between METALS pipeline and ASU LEI confirmed.
- **Key observation:** The METALS alumni page is the single highest-density source of confirmed LE title-holders found so far. Approximately 15–20% of METALS graduates take explicit "Learning Engineer" titles; the rest go into UX design, product management, or instructional design roles.

---

### Q010
- **Date:** 2026-04-14
- **Source:** WS (direct page fetch via WebFetch + agent)
- **Query type:** Institution team page scrape — CMU Eberly Center, CMU OLI, WGU Labs, MIT ODL, ICICLE, LEVI + company team pages
- **URLs fetched:** `cmu.edu/teaching/aboutus`, `oli.cmu.edu/learning-engineering/the-team/`, `wgulabs.org/team`, `openlearning.mit.edu`, `learningengineering-virtual-institute.org/teams/`, plus 8 company about pages
- **Result count:** 2 new records added; 2 title updates applied
- **New people added:**
  - LE-P-212 Laura Delince Ceballos — "Learning Engineer, Product Analyst" at CMU OLI (METALS '23; title on OLI page supersedes alumni page title)
  - LE-P-213 Vipin Verma — "Assistant Research Scientist" at ASU PRV Learning Engineering Institute Operations (NEEDS_REVIEW — no explicit LE title)
- **Title updates:** LE-P-009 Tanvi Domadia and LE-P-209 Caitlin Lim both updated to "Senior Learning Engineer" per current OLI team page
- **Company pages verdict:** Company about/team pages are almost uniformly unhelpful — either 404, no staff listing, or only executive leadership shown. Carnegie Learning, Khan Academy, Newsela, Amplify, EdPlus, Duolingo, and Renaissance Learning team pages returned no LE title-holders.
- **ASU LEI full verdict:** All 56 affiliates are faculty/professors; none hold the "Learning Engineer" title. The LEI is a research institute with faculty collaborators. Actual LE staff are embedded in EdPlus and program units, not listed on the LEI page.

<!--
### QXXX
- **Date:** 2026-04-14
- **Source:** 
- **Query type:** 
- **Scope:** 
- **Query string:** 
- **Filters:** 
- **Result count:** 
- **Raw file:** `titlesearch/data/raw/QXXX_SOURCE_desc.jsonl` (all paths relative to repo root)
- **Notes:** 
-->
