"""Build a Markdown report from a retrieval evaluation run."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from src.common.io import read_json, resolve_path


def latest_run_id(runs_dir: str) -> str:
    latest = read_json(Path(runs_dir) / "latest.json")
    return latest["run_id"]


def format_metric(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def build_report(results: dict[str, Any]) -> str:
    summary = results["summary"]
    is_real_financebench = str(summary.get("dataset_version", "")).startswith("financebench_real")
    lines = [
        "# Week 1 Retrieval Baseline Report",
        "",
        "## Run Summary",
        "",
        f"- run_id: `{summary['run_id']}`",
        f"- run_date: `{summary['run_date']}`",
        f"- dataset_version: `{summary['dataset_version']}`",
        f"- corpus_version: `{summary['corpus_version']}`",
        f"- benchmark_size: `{summary['benchmark_size']}`",
        f"- answerable_questions: `{summary['answerable_questions']}`",
        f"- unanswerable_questions: `{summary['unanswerable_questions']}`",
        f"- retrieval_config: `{summary['retrieval_config']}`",
        "",
        "## Retrieval Metrics",
        "",
    ]

    metric_names = [
        "evidence_level_retrieval_recall@5",
        "evidence_level_retrieval_recall@10",
        "question_recall@10",
        "strict_precision@5",
        "strict_precision@10",
        "relaxed_precision@5",
        "relaxed_precision@10",
        "gold_page_hit@10",
        "wrong_company_rate",
        "wrong_year_rate",
    ]
    for name in metric_names:
        if name in summary:
            lines.append(f"- {name}: `{format_metric(summary[name])}`")

    lines.extend(
        [
            "",
            "## Answer and Citation Metrics",
            "",
            "Not evaluated in Week 1. These begin after cited answer generation and verification are implemented.",
            "",
            "## Failure Breakdown",
            "",
        ]
    )

    failures: dict[str, int] = {}
    failed_cases = []
    for item in results["per_question"]:
        for label in item["failure_labels"]:
            failures[label] = failures.get(label, 0) + 1
        if item["failure_labels"]:
            failed_cases.append(item)

    if failures:
        for label, count in sorted(failures.items()):
            lines.append(f"- {label}: `{count}`")
    else:
        lines.append("- no retrieval failures at evaluated k")

    lines.extend(["", "## Top Failed Cases", ""])
    if failed_cases:
        for item in failed_cases[:10]:
            lines.extend(
                [
                    f"### {item['question_id']}",
                    "",
                    f"- question: {item['question']}",
                    f"- expected_behavior: `{item['expected_behavior']}`",
                    f"- gold_chunk_ids: `{', '.join(item['gold_chunk_ids'])}`",
                    f"- failure_labels: `{', '.join(item['failure_labels'])}`",
                    f"- retrieved_top_chunks: `{', '.join(chunk['chunk_id'] for chunk in item['top_chunks'][:5])}`",
                    "",
                ]
            )
    else:
        lines.append("No failed retrieval cases at the evaluated cutoff.")

    lines.extend(
        [
            "",
            "## Next Fix Priority",
            "",
            "1. Add vector retrieval and reranking in Week 2.",
            "2. Review any low recall@5 cases before changing prompts.",
            "3. Keep metadata filters visible in every per-question trace.",
            "",
        ]
    )
    if not is_real_financebench:
        lines[-4] = "1. Replace synthetic smoke data with a real FinanceBench / SEC subset."
    return "\n".join(lines)


def run(run_id: str, reports_dir: str = "reports", runs_dir: str = "runs") -> Path:
    resolved_run_id = latest_run_id(runs_dir) if run_id == "latest" else run_id
    results = read_json(Path(runs_dir) / resolved_run_id / "results.json")
    report_text = build_report(results)
    target = resolve_path(Path(reports_dir) / f"{resolved_run_id}.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report_text, encoding="utf-8")
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--runs-dir", default="runs")
    args = parser.parse_args()
    target = run(args.run_id, args.reports_dir, args.runs_dir)
    print(f"Wrote report: {target}")


if __name__ == "__main__":
    main()
