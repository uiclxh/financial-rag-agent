"""Build the BM25 index for Week 1."""

from __future__ import annotations

import argparse

from src.common.io import read_json, read_jsonl, write_json
from src.retrieval.bm25 import build_index


def run(config_path: str) -> dict[str, object]:
    config = read_json(config_path)
    chunks = read_jsonl(config["chunks_path"])
    index = build_index(
        chunks=chunks,
        token_pattern=config["token_pattern"],
        k1=float(config["k1"]),
        b=float(config["b"]),
    )
    write_json(config["index_path"], index)
    return {
        "index_path": config["index_path"],
        "document_count": index["document_count"],
        "avg_doc_length": index["avg_doc_length"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    summary = run(args.config)
    print(f"Indexed {summary['document_count']} chunks")
    print(f"avg_doc_length={summary['avg_doc_length']:.2f}")


if __name__ == "__main__":
    main()

