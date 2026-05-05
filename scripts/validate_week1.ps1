$ErrorActionPreference = "Stop"

python -m src.ingestion.financebench --config configs/ingestion/financebench_real.yaml
python -m src.retrieval.index --config configs/retrieval/bm25_financebench_real.yaml
python -m src.evaluation.run --config configs/evaluation/financebench_real_week1.yaml
python -m src.reports.build --run-id latest

Write-Host "Week 1 validation completed."

