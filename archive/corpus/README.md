# Learning Engineering Corpus Package

This directory is a normalized build artifact generated from:

- `le_corpus_specification_v1.xlsx`
- `corpus_construction_methodology_generic.md`
- Learning Engineering Toolkit PDF endnotes (auto-detected from known Desktop/Downloads paths, or passed via `--book-pdf`)

## Build Command

```bash
python3 scripts/build_corpus.py
```

Or explicit PDF inputs:

```bash
python3 scripts/build_corpus.py \
  --book-pdf "/Users/wgray13/Desktop/Learning Engineering Toolkit_26_04_07_15_45_22A.pdf" \
  --book-pdf "/Users/wgray13/Downloads/Learning Engineering Toolkit_26_04_07_15_45_22.pdf"
```

## Outputs

- `manifest.json`: build metadata and aggregate counts
- `records.jsonl`: unified corpus records (`academic_paper` + `non_paper_resource`)
- `academic_papers.jsonl`: records from `Corpus Registry`
- `non_paper_resources.jsonl`: records from `Programs & People Registry`
- `book_endnotes_raw.jsonl`: citation-like references extracted from chapter endnotes across toolkit PDF variants
- `book_endnotes_unique.jsonl`: deduplicated endnote references with source occurrence tracking
- `book_endnotes_expansion_eligible.jsonl`: endnote references that qualify as expansion seeds (documents only)
- `book_endnotes_expansion_excluded.jsonl`: excluded endnote references with exclusion reason
- `expansion_seed_queries.jsonl`: combined expansion seeds from workbook anchors + deduplicated endnote references
- `methodology.md`: copy of the methodology source markdown
- `tables/*.json`: normalized rows for each structured workbook sheet

## Current Snapshot (v1 Workbook)

- Total records: `47`
- Academic records: `21`
- Non-paper records: `26`
- Topics: `18`
- Expansion sources: `28`
- Book endnote references (raw): `271`
- Book endnote references (unique): `270`
- Book endnote references (expansion-eligible): `268`
- Book endnote references (excluded): `2`
- Expansion seed queries (total): `295`
- Gaps tracked: `10`
- Learning journey stages: `20`
