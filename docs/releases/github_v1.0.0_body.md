# v1.0.0 Week 1 Retrieval Baseline

This release is the first reproducible baseline for an evaluation-first Financial RAG Agent.

It focuses on one question:

```text
Can the system reliably retrieve the right financial evidence before any answer-generation agent is introduced?
```

For the current real FinanceBench / SEC sample, the answer is yes at `top_k=10`.

## What This Release Includes

- Global Financial RAG Agent workflow protocol.
- Real FinanceBench open-source data acquisition.
- SEC company ticker and submissions metadata download.
- Strict FinanceBench cleaning and metadata alignment.
- P0 benchmark conversion with answerable and unanswerable questions.
- BM25 lexical retrieval baseline.
- Retrieval evaluation metrics.
- Markdown report generation.
- Static progress UI under `ui/`.
- Reproducible validation script.

## Real Data Snapshot

```text
source: FinanceBench open-source QA + SEC company tickers/submissions metadata
benchmark_size: 60
answerable_questions: 50
unanswerable_questions: 10
chunks: 52
required_metadata_missing: 0
```

Selected companies:

```text
3M
AMD
Adobe
Amcor
Best Buy
Boeing
PepsiCo
Pfizer
```

## Latest Validated Metrics

```text
run_id: 20260505T154304Z
evidence_level_retrieval_recall@5: 0.914
evidence_level_retrieval_recall@10: 1.000
question_recall@10: 1.000
strict_precision@5: 0.212
strict_precision@10: 0.116
relaxed_precision@5: 0.736
relaxed_precision@10: 0.420
gold_page_hit@10: 1.000
wrong_company_rate: 0.000
wrong_year_rate: 0.000
```

## How To Reproduce

```bash
python -m src.data_acquisition.download_real --output-dir data/raw/real --sec-tickers MMM,AMD,BBY,AMCR,PEP,BA,PFE,ADBE,VZ,GLW,CVS,GIS,MGM,NKE,AES,AMZN,AWK,XYZ,KO,JNJ,LMT,WMT,MSFT,NFLX,ULTA,COST,KHC
python -m src.ingestion.financebench --config configs/ingestion/financebench_real.yaml
python -m src.retrieval.index --config configs/retrieval/bm25_financebench_real.yaml
python -m src.evaluation.run --config configs/evaluation/financebench_real_week1.yaml
python -m src.reports.build --run-id latest
```

Or run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\validate_week1.ps1
```

## Not Included Yet

This release validates retrieval only. It does not include:

- answer generation
- material claim extraction
- citation verification
- hallucination and faithfulness scoring
- vector retrieval
- reranking
- XBRL calculation workflows
- valuation workflows
- production service deployment

## Week 2 Direction

Week 2 will add vector retrieval, hybrid retrieval, and reranking.

The objective is not prompt optimization. It is to reduce top-k noise, improve gold evidence rank, and compare:

```text
BM25
BM25 + vector hybrid retrieval
BM25 + vector hybrid retrieval + reranker
```

Planned Week 2 metrics include:

```text
MRR
gold_rank_mean
gold_rank_median
top1_gold_hit_rate
top3_gold_hit_rate
top5_gold_hit_rate
gold_rank_improvement_vs_bm25
```

See `docs/week2_plan.md` for the full Week 2 plan.

