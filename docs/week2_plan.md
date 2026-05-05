# Week 2 Plan: Hybrid Retrieval and Reranking

Week 2 starts after `v1.0.0 Week 1 Retrieval Baseline`.

Week 1 proved that the real FinanceBench / SEC sample can be ingested, cleaned, indexed with BM25, and evaluated reproducibly. Week 2 must not change agent prompts or introduce answer generation. The goal is retrieval quality: reduce top-k noise, improve gold evidence rank, and compare BM25 against hybrid retrieval and hybrid + reranker.

## Current Week 1 Baseline

Latest release:

```text
tag: v1.0.0
run_id: 20260505T154304Z
benchmark_size: 60
answerable_questions: 50
unanswerable_questions: 10
chunks: 52
required_metadata_missing: 0
```

BM25-only metrics:

```text
evidence_level_retrieval_recall@5: 0.914
evidence_level_retrieval_recall@10: 1.000
question_recall@10: 1.000
strict_precision@10: 0.116
relaxed_precision@10: 0.420
gold_page_hit@10: 1.000
wrong_company_rate: 0.000
wrong_year_rate: 0.000
```

## Week 2 Objective

Add and evaluate:

```text
BM25 baseline
BM25 + vector hybrid retrieval
BM25 + vector hybrid retrieval + reranker
```

Week 2 success is not measured by answer fluency. It is measured by retrieval behavior:

```text
gold evidence rank improves
top-k noise decreases
precision improves without hurting recall
metadata filters remain visible in every per-question trace
wrong company and wrong year remain at zero or near-zero
```

## Files To Add

Required new files:

```text
configs/retrieval/hybrid_financebench_real.yaml
src/retrieval/vector.py
src/retrieval/hybrid.py
src/retrieval/rerank.py
```

Required updates:

```text
src/evaluation/run.py
src/reports/build.py
README.md
docs/releases/1.0.0.md if release notes need a pointer to Week 2
```

Optional later files:

```text
configs/evaluation/financebench_hybrid_week2.yaml
reports/week2_comparison.md
```

## Retrieval Pipeline

The Week 2 pipeline follows the global workflow:

```text
query normalization
  -> entity / period / section extraction
  -> metadata filters
  -> BM25 top 50
  -> vector top 50
  -> merge and deduplicate
  -> rerank top 20
  -> parent page / paragraph expansion
  -> final evidence
```

BM25 must remain in the system. Financial retrieval depends on exact terms such as company name, fiscal year, filing type, account names, ticker, and table labels. Vector retrieval must complement BM25, not replace it.

## Vector Retrieval Requirement

Week 2 vector retrieval should start with a local, reproducible embedding baseline.

Acceptable first implementation:

```text
deterministic TF-IDF vector retrieval
or a local embedding model if dependencies are explicitly documented
```

For the first Week 2 commit, prefer a deterministic local implementation over an external API. This keeps the benchmark reproducible and avoids API-key dependency.

Vector retriever output must include:

```json
{
  "chunk_id": "string",
  "vector_score": 0.0,
  "rank": 1
}
```

## Hybrid Merge Requirement

Hybrid retrieval must merge BM25 and vector results with traceable scores.

Required trace fields:

```json
{
  "chunk_id": "string",
  "bm25_rank": 1,
  "bm25_score": 0.0,
  "vector_rank": 3,
  "vector_score": 0.0,
  "hybrid_score": 0.0,
  "retrieval_sources": ["bm25", "vector"]
}
```

Recommended first scoring:

```text
reciprocal rank fusion
```

Example:

```text
hybrid_score = 1 / (k + bm25_rank) + 1 / (k + vector_rank)
```

Use a configurable `rrf_k`, defaulting to `60`.

## Reranker Requirement

The first reranker can be lightweight and local.

Acceptable first implementation:

```text
lexical overlap reranker
query-token coverage reranker
metadata consistency bonus
```

Reranker must not use answer-generation prompts. It should only rank retrieved evidence.

Required reranker output:

```json
{
  "chunk_id": "string",
  "hybrid_score": 0.0,
  "reranker_score": 0.0,
  "final_rank": 1
}
```

## Evaluation Updates

Week 2 evaluation must compare:

```text
bm25
hybrid
hybrid_plus_reranker
```

Existing metrics to keep:

```text
evidence_level_retrieval_recall@5
evidence_level_retrieval_recall@10
question_recall@10
strict_precision@5
strict_precision@10
relaxed_precision@5
relaxed_precision@10
gold_page_hit@10
wrong_company_rate
wrong_year_rate
```

New Week 2 metrics:

```text
MRR
gold_rank_mean
gold_rank_median
top1_gold_hit_rate
top3_gold_hit_rate
top5_gold_hit_rate
gold_rank_improvement_vs_bm25
```

Definitions:

```text
MRR =
mean reciprocal rank of the first required gold evidence unit

gold_rank_mean =
mean rank of required gold evidence units when retrieved

top1_gold_hit_rate =
answerable questions with required gold evidence at rank 1 / answerable questions

gold_rank_improvement_vs_bm25 =
bm25_gold_rank_mean - candidate_gold_rank_mean
```

## Report Requirements

The Week 2 report must include:

```text
run_id
dataset_version
corpus_version
retrieval_modes_compared
BM25 metrics
hybrid metrics
hybrid_plus_reranker metrics
delta vs BM25
top failed cases
low recall@5 cases
metadata filter trace examples
next fix priority
```

The report must make it obvious whether hybrid retrieval actually helped, not merely that it was added.

## Acceptance Gates

Minimum Week 2 gate:

```text
evidence_level_retrieval_recall@10 >= BM25 baseline
question_recall@10 >= BM25 baseline
wrong_company_rate <= 0.03
wrong_year_rate <= 0.10
metadata filters present in every per-question trace
```

Preferred Week 2 improvement:

```text
gold_rank_mean improves vs BM25
top1_gold_hit_rate improves vs BM25
strict_precision@5 improves vs BM25
relaxed_precision@5 improves vs BM25
```

No regression rule:

```text
If hybrid or reranking lowers recall@10, keep BM25 as the default retrieval mode and mark the candidate as experimental.
```

## Out of Scope for Week 2

Do not implement:

```text
answer generation
material claim extraction
paragraph-level answer citation
citation verification
hallucination_rate
unsupported_claim_rate
uncited_claim_rate
answer_faithfulness
valuation route
prompt optimization for answer style
```

Week 2 is retrieval engineering only.

## Implementation Order

1. Add `src/retrieval/vector.py`.
2. Add `src/retrieval/hybrid.py`.
3. Add `configs/retrieval/hybrid_financebench_real.yaml`.
4. Add `src/retrieval/rerank.py`.
5. Update evaluation to support multiple retrieval modes.
6. Add MRR and gold-rank metrics.
7. Update reports with BM25 vs hybrid vs hybrid+reranker comparison.
8. Run the real FinanceBench / SEC benchmark.
9. Review low recall@5 and poor gold-rank cases.
10. Decide whether BM25, hybrid, or hybrid+reranker becomes the default retrieval mode.

## Final Week 2 Deliverable

Week 2 is complete only when the repository contains:

```text
working vector retrieval
working hybrid merge
working reranker
comparison report against BM25
MRR and gold-rank metrics
per-question trace with metadata filters
clear default retrieval recommendation
```

