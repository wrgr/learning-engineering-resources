# Learning Engineers Study — Query Provenance Log

**Study goal:** Identify individuals who self-apply the title "learning engineer" (or close variants) across professional and academic networks.  
**Study date:** 2026-04-14  
**Lead:** [redacted]  
**Branch:** `claude/learning-engineers-research-7Ij1K`

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

Each entry records one discrete search action. `raw_file` links to the file in `people/raw/` containing unprocessed results.

---

### Q001
- **Date:** 2026-04-14
- **Source:** LI (LinkedIn)
- **Query type:** Keyword search
- **Scope:** United States
- **Query string:** `"learning engineer"`
- **Filters:** Title field only (PhantomBuster title scrape)
- **Result count:** _[to be filled]_
- **Raw file:** `people/raw/Q001_LI_keyword_US.jsonl`
- **Notes:** First pass; US-scoped to test completeness before global run.

---

<!-- Add new query blocks here. Copy the template below. -->

<!--
### QXXX
- **Date:** 2026-04-14
- **Source:** 
- **Query type:** 
- **Scope:** 
- **Query string:** 
- **Filters:** 
- **Result count:** 
- **Raw file:** `people/raw/QXXX_SOURCE_desc.jsonl`
- **Notes:** 
-->
