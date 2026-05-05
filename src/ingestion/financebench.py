"""Convert FinanceBench open-source QA into the Week 1 benchmark/corpus schema."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from src.common.io import read_json, read_jsonl, write_json, write_jsonl


AVOID_MVP_SECTORS = {"Financials", "Real Estate"}


def clean_text(text: str) -> str:
    """Normalize common PDF extraction noise without changing meaning."""
    if any(marker in text for marker in ("â", "Â", "Ã")):
        try:
            text = text.encode("latin1").decode("utf-8")
        except UnicodeError:
            pass
    text = text.replace("\u00a0", " ")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_doc_type(doc_type: str | None) -> str:
    doc_type = (doc_type or "").lower().replace("-", "")
    if doc_type == "10k":
        return "10-K"
    if doc_type == "10q":
        return "10-Q"
    return (doc_type or "unknown").upper()


def infer_section(text: str, question_type: str) -> str:
    lowered = text.lower()
    if "risk factor" in lowered:
        return "Item 1A. Risk Factors"
    if "cash flow" in lowered:
        return "Cash Flow Statement"
    if "balance sheet" in lowered:
        return "Balance Sheet"
    if "income statement" in lowered or "statement of operations" in lowered:
        return "Income Statement"
    if "management" in lowered or "discussion and analysis" in lowered:
        return "Item 7. Management Discussion and Analysis"
    if "segment" in lowered:
        return "Segment Information"
    if "metrics" in question_type.lower():
        return "Financial Statement Table"
    return "FinanceBench Evidence Page"


def stable_chunk_id(doc_name: str, page: int, text: str) -> str:
    digest = hashlib.sha1(f"{doc_name}|{page}|{text}".encode("utf-8")).hexdigest()[:12]
    safe_doc = re.sub(r"[^A-Za-z0-9]+", "_", doc_name).strip("_").lower()
    return f"fb_{safe_doc}_p{page}_{digest}"


def load_doc_info(path: str) -> dict[str, dict[str, Any]]:
    return {row["doc_name"]: row for row in read_jsonl(path)}


def load_sec_ticker_map(path: str | None, aliases: dict[str, str]) -> dict[str, dict[str, str]]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    by_ticker = {
        str(row["ticker"]).upper(): {"ticker": str(row["ticker"]).upper(), "cik": str(row["cik_str"]).zfill(10)}
        for row in raw.values()
    }
    mapped = {}
    for company, ticker in aliases.items():
        if ticker.upper() in by_ticker:
            mapped[company] = by_ticker[ticker.upper()]
    return mapped


def load_filing_date_map(submissions_dir: str | None, sec_map: dict[str, dict[str, str]]) -> dict[tuple[str, str, int], str]:
    if not submissions_dir:
        return {}
    filing_dates: dict[tuple[str, str, int], str] = {}
    root = Path(submissions_dir)
    if not root.is_absolute():
        from src.common.io import resolve_path

        root = resolve_path(root)
    cik_to_company = {identity["cik"]: company for company, identity in sec_map.items()}
    for path in root.glob("CIK*.json"):
        with path.open("r", encoding="utf-8") as handle:
            submission = json.load(handle)
        cik = str(submission.get("cik", "")).zfill(10)
        company = cik_to_company.get(cik)
        if not company:
            continue
        recent = submission.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        filing_dates_raw = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        for form, filing_date, report_date in zip(forms, filing_dates_raw, report_dates):
            normalized_form = normalize_doc_type(form)
            if normalized_form not in {"10-K", "10-Q"} or not report_date:
                continue
            try:
                year = int(str(report_date)[:4])
            except ValueError:
                continue
            key = (company, normalized_form, year)
            current = filing_dates.get(key)
            if not current or filing_date > current:
                filing_dates[key] = filing_date
    return filing_dates


def eligible_rows(rows: list[dict[str, Any]], doc_info: dict[str, dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    allowed_doc_types = {doc_type.lower() for doc_type in config["allowed_doc_types"]}
    min_evidence_chars = int(config["min_evidence_chars"])
    cleaned = []
    rejected = Counter()

    for row in rows:
        info = doc_info.get(row.get("doc_name"))
        if not info:
            rejected["missing_doc_info"] += 1
            continue
        if str(info.get("doc_type", "")).lower() not in allowed_doc_types:
            rejected["unsupported_doc_type"] += 1
            continue
        evidence = row.get("evidence") or []
        if not evidence:
            rejected["missing_evidence"] += 1
            continue
        valid_evidence = []
        for item in evidence:
            text = clean_text(item.get("evidence_text_full_page") or item.get("evidence_text") or "")
            if len(text) < min_evidence_chars:
                rejected["short_evidence"] += 1
                continue
            valid = dict(item)
            valid["clean_text"] = text
            valid_evidence.append(valid)
        if not valid_evidence:
            continue
        updated = dict(row)
        updated["evidence"] = valid_evidence
        cleaned.append(updated)

    return cleaned


def select_companies(rows: list[dict[str, Any]], doc_info: dict[str, dict[str, Any]], max_companies: int) -> list[str]:
    counts = Counter(row["company"] for row in rows)
    company_sector: dict[str, str] = {}
    for info in doc_info.values():
        company_sector.setdefault(info["company"], info.get("gics_sector", "Unknown"))

    ranked = [
        company
        for company, _ in counts.most_common()
        if company_sector.get(company) not in AVOID_MVP_SECTORS
    ]

    selected: list[str] = []
    sectors: set[str] = set()
    for company in ranked:
        sector = company_sector.get(company, "Unknown")
        if len(selected) < max_companies and (len(sectors) < 3 or sector not in sectors):
            selected.append(company)
            sectors.add(sector)
    for company in ranked:
        if len(selected) >= max_companies:
            break
        if company not in selected:
            selected.append(company)
    return selected[:max_companies]


def ranked_companies(rows: list[dict[str, Any]], doc_info: dict[str, dict[str, Any]]) -> list[str]:
    counts = Counter(row["company"] for row in rows)
    company_sector: dict[str, str] = {}
    for info in doc_info.values():
        company_sector.setdefault(info["company"], info.get("gics_sector", "Unknown"))
    return [
        company
        for company, _ in counts.most_common()
        if company_sector.get(company) not in AVOID_MVP_SECTORS
    ]


def build_chunks_and_questions(rows: list[dict[str, Any]], doc_info: dict[str, dict[str, Any]], config: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    sec_map = load_sec_ticker_map(config.get("sec_company_tickers_path"), config.get("company_ticker_aliases", {}))
    filing_date_map = load_filing_date_map(config.get("sec_submissions_dir"), sec_map)
    selected_companies = select_companies(rows, doc_info, int(config["max_companies"]))
    answerable_target = int(config["answerable_questions"])
    excluded_missing_filing_date = 0

    def row_filing_date(row: dict[str, Any]) -> str:
        info = doc_info[row["doc_name"]]
        filing_type = normalize_doc_type(info.get("doc_type"))
        fiscal_year = int(info.get("doc_period", 0) or 0)
        return filing_date_map.get((row["company"], filing_type, fiscal_year), "")

    def rows_for_companies(companies: set[str]) -> list[dict[str, Any]]:
        nonlocal excluded_missing_filing_date
        selected = []
        excluded_missing_filing_date = 0
        for row in rows:
            if row["company"] not in companies:
                continue
            if not row_filing_date(row):
                excluded_missing_filing_date += 1
                continue
            selected.append(row)
            if len(selected) >= answerable_target:
                break
        return selected

    selected_set = set(selected_companies)
    selected_rows = rows_for_companies(selected_set)
    auto_extended = False
    if len(selected_rows) < answerable_target:
        for company in ranked_companies(rows, doc_info):
            if len(selected_rows) >= answerable_target:
                break
            if company in selected_set:
                continue
            selected_set.add(company)
            selected_companies.append(company)
            selected_rows = rows_for_companies(selected_set)
            auto_extended = True

    chunks_by_id: dict[str, dict[str, Any]] = {}
    questions: list[dict[str, Any]] = []

    for row in selected_rows:
        info = doc_info[row["doc_name"]]
        sec_identity = sec_map.get(row["company"], {"ticker": "", "cik": ""})
        filing_type = normalize_doc_type(info.get("doc_type"))
        fiscal_year = int(info.get("doc_period", 0) or 0)
        filing_date = filing_date_map.get((row["company"], filing_type, fiscal_year), "")
        gold_evidence = []
        for evidence_index, evidence in enumerate(row["evidence"], start=1):
            page = int(evidence.get("evidence_page_num", 0) or 0)
            text = evidence["clean_text"]
            chunk_id = stable_chunk_id(row["doc_name"], page, text)
            section = infer_section(text, row.get("question_type", ""))
            chunks_by_id.setdefault(
                chunk_id,
                {
                    "chunk_id": chunk_id,
                    "document_id": row["doc_name"],
                    "company": row["company"],
                    "ticker": sec_identity["ticker"],
                    "cik": sec_identity["cik"],
                    "filing_type": filing_type,
                    "fiscal_year": fiscal_year,
                    "filing_date": filing_date,
                    "section": section,
                    "page": page,
                    "paragraph_id": f"page_{page}",
                    "table_row_id": None,
                    "source_type": "financebench_evidence_page",
                    "source_url": info.get("doc_link", ""),
                    "text": text,
                },
            )
            gold_evidence.append(
                {
                    "evidence_id": f"{row['financebench_id']}_ev{evidence_index}",
                    "chunk_id": chunk_id,
                    "required": True,
                    "page": page,
                    "section": section,
                }
            )

        questions.append(
            {
                "question_id": row["financebench_id"],
                "question": clean_text(row["question"]),
                "company": row["company"],
                "ticker": sec_identity["ticker"],
                "cik": sec_identity["cik"],
                "filing_type": filing_type,
                "fiscal_year": fiscal_year,
                "question_type": [str(row.get("question_type", "financebench")).lower()],
                "expected_behavior": "answer",
                "gold_answer": clean_text(row.get("answer", "")),
                "gold_evidence": gold_evidence,
            }
        )

    questions.extend(make_unanswerable_questions(selected_companies, doc_info, int(config["unanswerable_questions"])))

    report = {
        "selected_companies": selected_companies,
        "configured_max_companies": int(config["max_companies"]),
        "auto_extended_companies_to_hit_answerable_target": auto_extended,
        "answerable_target": answerable_target,
        "answerable_questions": len(selected_rows),
        "unanswerable_questions": int(config["unanswerable_questions"]),
        "chunk_count": len(chunks_by_id),
        "company_distribution": dict(Counter(row["company"] for row in selected_rows)),
        "section_distribution": dict(Counter(chunk["section"] for chunk in chunks_by_id.values())),
        "sec_identity_missing_companies": [company for company in selected_companies if company not in sec_map],
        "filing_date_missing_chunks": sum(1 for chunk in chunks_by_id.values() if not chunk.get("filing_date")),
        "excluded_rows_missing_sec_filing_date": excluded_missing_filing_date,
    }
    return list(chunks_by_id.values()), questions, report


def make_unanswerable_questions(companies: list[str], doc_info: dict[str, dict[str, Any]], total: int) -> list[dict[str, Any]]:
    by_company: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for info in doc_info.values():
        if info["company"] in companies and str(info.get("doc_type", "")).lower() == "10k":
            by_company[info["company"]].append(info)

    templates = [
        ("wacc", "What WACC did {company} disclose in its FY{year} 10-K?", ["valuation", "unanswerable"]),
        ("market_price", "What was the latest market price for {company}?", ["market_data", "unanswerable"]),
    ]
    questions = []
    for company in companies:
        infos = sorted(by_company.get(company, []), key=lambda item: int(item.get("doc_period", 0) or 0), reverse=True)
        if not infos:
            continue
        info = infos[0]
        for suffix, template, question_type in templates:
            if len(questions) >= total:
                return questions
            year = int(info.get("doc_period", 0) or 0)
            questions.append(
                {
                    "question_id": f"unanswerable_{re.sub(r'[^a-z0-9]+', '_', company.lower()).strip('_')}_{year}_{suffix}",
                    "question": template.format(company=company, year=year),
                    "company": company,
                    "ticker": "",
                    "cik": "",
                    "filing_type": "10-K",
                    "fiscal_year": year,
                    "question_type": question_type,
                    "expected_behavior": "refuse",
                    "gold_answer": "",
                    "gold_evidence": [],
                }
            )
    return questions


def run(config_path: str) -> dict[str, Any]:
    config = read_json(config_path)
    qa_rows = read_jsonl(config["financebench_qa_path"])
    doc_info = load_doc_info(config["financebench_doc_info_path"])
    rows = eligible_rows(qa_rows, doc_info, config)
    chunks, questions, report = build_chunks_and_questions(rows, doc_info, config)

    benchmark = {
        "benchmark_id": "financebench_real_week1_v0",
        "description": "Real FinanceBench open-source subset converted to the P0 Week 1 retrieval schema.",
        "questions": questions,
    }
    write_jsonl(config["processed_chunks_path"], chunks)
    write_json(config["benchmark_path"], benchmark)
    write_json(config["cleaning_report_path"], report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    report = run(args.config)
    print(f"Selected companies: {', '.join(report['selected_companies'])}")
    print(f"Answerable questions: {report['answerable_questions']}")
    print(f"Unanswerable questions: {report['unanswerable_questions']}")
    print(f"Chunks: {report['chunk_count']}")


if __name__ == "__main__":
    main()
