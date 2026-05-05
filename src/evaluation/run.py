"""Evaluate the Week 1 BM25 retrieval baseline."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Any

from src.common.io import read_json, write_json
from src.retrieval.bm25 import retrieve


def metadata_filters(question: dict[str, Any]) -> dict[str, Any]:
    return {
        "company": question.get("company"),
        "fiscal_year": question.get("fiscal_year"),
        "filing_type": question.get("filing_type"),
    }


def required_gold_chunk_ids(question: dict[str, Any]) -> set[str]:
    return {
        evidence["chunk_id"]
        for evidence in question.get("gold_evidence", [])
        if evidence.get("required", True) and evidence.get("chunk_id")
    }


def required_gold_pages(question: dict[str, Any]) -> set[int]:
    pages = set()
    for evidence in question.get("gold_evidence", []):
        if evidence.get("required", True) and evidence.get("page") is not None:
            pages.add(int(evidence["page"]))
    return pages


def is_relaxed_relevant(chunk: dict[str, Any], question: dict[str, Any]) -> bool:
    if str(chunk.get("company", "")).lower() != str(question.get("company", "")).lower():
        return False
    if int(chunk.get("fiscal_year", -1)) != int(question.get("fiscal_year", -2)):
        return False
    if str(chunk.get("filing_type", "")).lower() != str(question.get("filing_type", "")).lower():
        return False
    question_types = set(question.get("question_type", []))
    section = str(chunk.get("section", "")).lower()
    if "risk_factor" in question_types:
        return "risk" in section
    return True


def evaluate_at_k(question: dict[str, Any], retrieved: list[dict[str, Any]], k: int) -> dict[str, Any]:
    top = retrieved[:k]
    top_chunks = [item["chunk"] for item in top]
    retrieved_ids = {chunk["chunk_id"] for chunk in top_chunks}
    gold_ids = required_gold_chunk_ids(question)
    gold_pages = required_gold_pages(question)
    retrieved_pages = {int(chunk["page"]) for chunk in top_chunks if chunk.get("page") is not None}

    strict_hits = sum(1 for chunk in top_chunks if chunk["chunk_id"] in gold_ids)
    relaxed_hits = sum(1 for chunk in top_chunks if chunk["chunk_id"] in gold_ids or is_relaxed_relevant(chunk, question))
    required_hits = len(gold_ids.intersection(retrieved_ids))

    return {
        "k": k,
        "required_gold_count": len(gold_ids),
        "required_gold_hits": required_hits,
        "question_recall_pass": bool(gold_ids) and gold_ids.issubset(retrieved_ids),
        "strict_precision": strict_hits / k if k else 0.0,
        "relaxed_precision": relaxed_hits / k if k else 0.0,
        "gold_page_hit": bool(gold_pages.intersection(retrieved_pages)) if gold_pages else False,
        "complete_gold_page_hit": bool(gold_pages) and gold_pages.issubset(retrieved_pages),
        "retrieved_chunk_ids": [chunk["chunk_id"] for chunk in top_chunks],
    }


def wrong_rates(retrieved: list[dict[str, Any]], questions: list[dict[str, Any]], top_k: int) -> dict[str, float]:
    wrong_company = 0
    wrong_year = 0
    total = 0
    for question in questions:
        if question.get("expected_behavior") != "answer":
            continue
        for item in retrieved_by_question(question, retrieved)[:top_k]:
            chunk = item["chunk"]
            total += 1
            if str(chunk.get("company", "")).lower() != str(question.get("company", "")).lower():
                wrong_company += 1
            if int(chunk.get("fiscal_year", -1)) != int(question.get("fiscal_year", -2)):
                wrong_year += 1
    return {
        "wrong_company_rate": wrong_company / total if total else 0.0,
        "wrong_year_rate": wrong_year / total if total else 0.0,
    }


def retrieved_by_question(question: dict[str, Any], retrieved_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for record in retrieved_records:
        if record["question_id"] == question["question_id"]:
            return record["retrieved"]
    return []


def aggregate(answerable_questions: list[dict[str, Any]], per_question: list[dict[str, Any]], k: int) -> dict[str, float]:
    required_total = 0
    required_hits = 0
    question_pass = 0
    strict_precision = 0.0
    relaxed_precision = 0.0
    gold_page_hits = 0

    for result in per_question:
        if result["expected_behavior"] != "answer":
            continue
        metrics = result["metrics_by_k"][str(k)]
        required_total += metrics["required_gold_count"]
        required_hits += metrics["required_gold_hits"]
        question_pass += int(metrics["question_recall_pass"])
        strict_precision += metrics["strict_precision"]
        relaxed_precision += metrics["relaxed_precision"]
        gold_page_hits += int(metrics["gold_page_hit"])

    count = len(answerable_questions)
    return {
        f"evidence_level_retrieval_recall@{k}": required_hits / required_total if required_total else 0.0,
        f"question_recall@{k}": question_pass / count if count else 0.0,
        f"strict_precision@{k}": strict_precision / count if count else 0.0,
        f"relaxed_precision@{k}": relaxed_precision / count if count else 0.0,
        f"gold_page_hit@{k}": gold_page_hits / count if count else 0.0,
    }


def failure_labels(result: dict[str, Any], max_k: int) -> list[str]:
    if result["expected_behavior"] != "answer":
        return []
    metrics = result["metrics_by_k"][str(max_k)]
    labels = []
    if not metrics["question_recall_pass"]:
        labels.append("retrieval_error")
    if not metrics["gold_page_hit"]:
        labels.append("citation_source_error")
    return labels


def run(config_path: str) -> dict[str, Any]:
    config = read_json(config_path)
    benchmark = read_json(config["benchmark_path"])
    index = read_json(config["index_path"])
    top_ks = [int(k) for k in config["top_k"]]
    max_k = max(top_ks)

    retrieved_records: list[dict[str, Any]] = []
    per_question: list[dict[str, Any]] = []

    for question in benchmark["questions"]:
        results = retrieve(index, question["question"], max_k, metadata_filters(question))
        retrieved_records.append({"question_id": question["question_id"], "retrieved": results})
        metrics_by_k = {str(k): evaluate_at_k(question, results, k) for k in top_ks}
        result = {
            "question_id": question["question_id"],
            "question": question["question"],
            "expected_behavior": question["expected_behavior"],
            "question_type": question.get("question_type", []),
            "metadata_filters": metadata_filters(question),
            "gold_chunk_ids": sorted(required_gold_chunk_ids(question)),
            "metrics_by_k": metrics_by_k,
            "top_chunks": [
                {
                    "rank": rank,
                    "chunk_id": item["chunk"]["chunk_id"],
                    "score": item["score"],
                    "company": item["chunk"]["company"],
                    "fiscal_year": item["chunk"]["fiscal_year"],
                    "page": item["chunk"]["page"],
                    "section": item["chunk"]["section"],
                }
                for rank, item in enumerate(results, start=1)
            ],
        }
        result["failure_labels"] = failure_labels(result, max_k)
        per_question.append(result)

    answerable = [q for q in benchmark["questions"] if q["expected_behavior"] == "answer"]
    unanswerable = [q for q in benchmark["questions"] if q["expected_behavior"] != "answer"]
    summary: dict[str, Any] = {
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "run_date": datetime.now(timezone.utc).isoformat(),
        "dataset_version": config["dataset_version"],
        "corpus_version": config["corpus_version"],
        "benchmark_size": len(benchmark["questions"]),
        "answerable_questions": len(answerable),
        "unanswerable_questions": len(unanswerable),
        "retrieval_config": config["retrieval_config_name"],
        "notes": "Week 1 evaluates retrieval only. Answer/citation/refusal metrics are not evaluated until Week 3-6.",
    }
    for k in top_ks:
        summary.update(aggregate(answerable, per_question, k))

    summary.update(wrong_rates(retrieved_records, benchmark["questions"], max_k))

    run_id = summary["run_id"]
    run_path = f"{config['run_dir']}/{run_id}/results.json"
    output = {
        "summary": summary,
        "per_question": per_question,
        "config_snapshot": config,
    }
    write_json(run_path, output)
    write_json(f"{config['run_dir']}/latest.json", {"run_id": run_id, "results_path": run_path})
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    output = run(args.config)
    summary = output["summary"]
    print(f"run_id={summary['run_id']}")
    print(f"evidence_level_retrieval_recall@10={summary.get('evidence_level_retrieval_recall@10', 0):.3f}")
    print(f"gold_page_hit@10={summary.get('gold_page_hit@10', 0):.3f}")
    print(f"wrong_company_rate={summary['wrong_company_rate']:.3f}")
    print(f"wrong_year_rate={summary['wrong_year_rate']:.3f}")


if __name__ == "__main__":
    main()

