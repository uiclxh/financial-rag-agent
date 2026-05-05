"""Download FinanceBench and SEC metadata used by the real Week 1 sample."""

from __future__ import annotations

import argparse
import http.client
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.common.io import resolve_path, write_json


FINANCEBENCH_QA_URL = "https://raw.githubusercontent.com/patronus-ai/financebench/main/data/financebench_open_source.jsonl"
FINANCEBENCH_DOCS_URL = "https://raw.githubusercontent.com/patronus-ai/financebench/main/data/financebench_document_information.jsonl"
SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik10}.json"


DEFAULT_USER_AGENT = "financial-rag-agent/0.1 research@example.com"


def fetch(url: str, target: Path, user_agent: str, attempts: int = 3) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(url, headers={"User-Agent": user_agent})
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                data = response.read()
                temp_target = target.with_suffix(target.suffix + ".tmp")
                temp_target.write_bytes(data)
                temp_target.replace(target)
                return {
                    "url": url,
                    "path": str(target),
                    "bytes": len(data),
                    "status": getattr(response, "status", None),
                    "attempts": attempt,
                }
        except (OSError, TimeoutError, http.client.IncompleteRead) as exc:
            last_error = exc
    raise RuntimeError(f"Failed to download {url} after {attempts} attempts: {last_error}")


def load_company_tickers(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return [raw[key] for key in sorted(raw.keys(), key=lambda value: int(value))]


def selected_ticker_rows(path: Path, tickers: list[str]) -> list[dict[str, Any]]:
    ticker_set = {ticker.upper() for ticker in tickers}
    rows = []
    for row in load_company_tickers(path):
        if row.get("ticker", "").upper() in ticker_set:
            rows.append(row)
    return rows


def run(output_dir: str, user_agent: str, sec_tickers: list[str]) -> dict[str, Any]:
    root = resolve_path(output_dir)
    financebench_dir = root / "financebench"
    sec_dir = root / "sec"
    submissions_dir = sec_dir / "submissions"
    submissions_dir.mkdir(parents=True, exist_ok=True)
    for stale_file in submissions_dir.glob("CIK*.json"):
        stale_file.unlink()

    downloads = [
        fetch(FINANCEBENCH_QA_URL, financebench_dir / "financebench_open_source.jsonl", user_agent),
        fetch(FINANCEBENCH_DOCS_URL, financebench_dir / "financebench_document_information.jsonl", user_agent),
        fetch(SEC_COMPANY_TICKERS_URL, sec_dir / "company_tickers.json", user_agent),
    ]

    sec_submission_downloads = []
    for row in selected_ticker_rows(sec_dir / "company_tickers.json", sec_tickers):
        cik10 = str(row["cik_str"]).zfill(10)
        target = submissions_dir / f"CIK{cik10}.json"
        sec_submission_downloads.append(fetch(SEC_SUBMISSIONS_URL.format(cik10=cik10), target, user_agent))

    manifest = {
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "sources": downloads,
        "sec_submissions": sec_submission_downloads,
        "notes": [
            "FinanceBench is used for real benchmark QA and evidence text.",
            "SEC company tickers and submissions metadata are downloaded from official SEC endpoints.",
        ],
    }
    write_json(root / "source_manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/raw/real")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT)
    parser.add_argument("--sec-tickers", default="MMM,AAPL,MSFT,ADBE,AMZN")
    args = parser.parse_args()
    manifest = run(
        output_dir=args.output_dir,
        user_agent=args.user_agent,
        sec_tickers=[ticker.strip() for ticker in args.sec_tickers.split(",") if ticker.strip()],
    )
    print(f"Downloaded {len(manifest['sources'])} primary files")
    print(f"Downloaded {len(manifest['sec_submissions'])} SEC submission files")


if __name__ == "__main__":
    main()
