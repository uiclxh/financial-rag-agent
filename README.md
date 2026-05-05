# Financial RAG Agent

Week 1 implements the P0 retrieval baseline from `FINANCIAL_RAG_AGENT_GLOBAL_WORKFLOW.md`.

Current scope:

- fixed local sample corpus
- basic metadata ingestion
- BM25 lexical retrieval
- retrieval recall / precision / gold page hit
- wrong company / wrong year checks
- failure report

Run:

```bash
python -m src.ingestion.run --config configs/ingestion/sample.yaml
python -m src.retrieval.index --config configs/retrieval/bm25_sample.yaml
python -m src.evaluation.run --config configs/evaluation/sample_week1.yaml
python -m src.reports.build --run-id latest
```

Week 1 intentionally does not implement answer generation, citation verification, vector retrieval, reranking, XBRL, valuation, or permissions.

Release notes:

- [v1.0.0](docs/releases/1.0.0.md) records the completed Week 1 retrieval baseline.
- Latest validated run: `20260505T154304Z`.
- The release validates retrieval only; answer quality, citation faithfulness, and hallucination rate are later phases.
- [Week 2 plan](docs/week2_plan.md) defines vector retrieval, hybrid retrieval, reranking, and comparison metrics.

Real FinanceBench / SEC Week 1 run:

```bash
python -m src.data_acquisition.download_real --output-dir data/raw/real --sec-tickers MMM,AMD,BBY,AMCR,PEP,BA,PFE,ADBE,VZ,GLW,CVS,GIS,MGM,NKE,AES,AMZN,AWK,XYZ,KO,JNJ,LMT,WMT,MSFT,NFLX,ULTA,COST,KHC
python -m src.ingestion.financebench --config configs/ingestion/financebench_real.yaml
python -m src.retrieval.index --config configs/retrieval/bm25_financebench_real.yaml
python -m src.evaluation.run --config configs/evaluation/financebench_real_week1.yaml
python -m src.reports.build --run-id latest
```

The real Week 1 corpus uses FinanceBench evidence pages as retrieval chunks and downloads SEC company ticker / submissions metadata for the selected public companies.

Static progress UI:

Open [ui/index.html](ui/index.html) in a browser to view the v1.0.0 Week 1 progress snapshot. The UI has no external dependencies.
