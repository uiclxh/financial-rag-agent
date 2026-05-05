"""Validate raw corpus records and write normalized chunks."""

from __future__ import annotations

import argparse
from typing import Any

from src.common.io import read_json, read_jsonl, write_json, write_jsonl


def normalize_chunk(record: dict[str, Any], required_metadata: list[str]) -> dict[str, Any]:
    missing = [field for field in required_metadata if field not in record or record[field] in ("", None)]
    if missing:
        raise ValueError(f"Chunk {record.get('chunk_id', '<missing>')} missing required metadata: {missing}")

    normalized = dict(record)
    normalized["fiscal_year"] = int(normalized["fiscal_year"])
    normalized["page"] = int(normalized["page"])
    normalized["text"] = " ".join(str(normalized["text"]).split())
    return normalized


def run(config_path: str) -> dict[str, Any]:
    config = read_json(config_path)
    raw_records = read_jsonl(config["raw_corpus_path"])
    required_metadata = list(config["required_metadata"])
    chunks = [normalize_chunk(record, required_metadata) for record in raw_records]

    write_jsonl(config["processed_chunks_path"], chunks)

    present_count = sum(
        1
        for chunk in chunks
        for field in required_metadata
        if field in chunk and chunk[field] not in ("", None)
    )
    total_required = len(chunks) * len(required_metadata)
    summary = {
        "raw_corpus_path": config["raw_corpus_path"],
        "processed_chunks_path": config["processed_chunks_path"],
        "chunk_count": len(chunks),
        "required_metadata_count": len(required_metadata),
        "required_metadata_present_rate": present_count / total_required if total_required else 0.0,
    }
    write_json("data/processed/ingestion_summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    summary = run(args.config)
    print(f"Ingested {summary['chunk_count']} chunks")
    print(f"required_metadata_present_rate={summary['required_metadata_present_rate']:.3f}")


if __name__ == "__main__":
    main()

