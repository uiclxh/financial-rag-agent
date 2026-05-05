# Changelog

## 1.0.0 - 2026-05-05

Initial Week 1 retrieval-baseline release.

- Added the global Financial RAG Agent workflow protocol.
- Added real FinanceBench / SEC data acquisition.
- Added strict FinanceBench cleaning and P0 benchmark conversion.
- Added BM25 lexical retrieval baseline.
- Added retrieval evaluation metrics and Markdown report generation.
- Added a static progress UI under `ui/`.
- Verified the real Week 1 benchmark with 50 answerable questions, 10 unanswerable questions, and 52 cleaned chunks.

Latest validated run:

```text
run_id: 20260505T154304Z
evidence_level_retrieval_recall@5: 0.914
evidence_level_retrieval_recall@10: 1.000
question_recall@10: 1.000
gold_page_hit@10: 1.000
wrong_company_rate: 0.000
wrong_year_rate: 0.000
```

Not included in this release:

- answer generation
- claim extraction
- citation verification
- hallucination / faithfulness scoring
- vector retrieval
- reranking
- valuation workflows

