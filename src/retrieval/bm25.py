"""Minimal BM25 implementation for the Week 1 lexical baseline."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any

from src.common.text import tokenize


def build_index(chunks: list[dict[str, Any]], token_pattern: str, k1: float, b: float) -> dict[str, Any]:
    documents = []
    doc_freq: Counter[str] = Counter()
    total_length = 0

    for chunk in chunks:
        tokens = tokenize(chunk["text"], token_pattern)
        token_counts = Counter(tokens)
        total_length += len(tokens)
        doc_freq.update(token_counts.keys())
        documents.append(
            {
                "chunk": chunk,
                "token_counts": dict(token_counts),
                "length": len(tokens),
            }
        )

    avg_doc_length = total_length / len(documents) if documents else 0.0
    return {
        "documents": documents,
        "doc_freq": dict(doc_freq),
        "avg_doc_length": avg_doc_length,
        "document_count": len(documents),
        "token_pattern": token_pattern,
        "k1": k1,
        "b": b,
    }


def score_document(query_tokens: list[str], document: dict[str, Any], index: dict[str, Any]) -> float:
    score = 0.0
    document_count = index["document_count"]
    avg_doc_length = index["avg_doc_length"] or 1.0
    k1 = index["k1"]
    b = index["b"]
    doc_length = document["length"] or 1
    term_counts = document["token_counts"]

    for token in query_tokens:
        tf = term_counts.get(token, 0)
        if tf == 0:
            continue
        df = index["doc_freq"].get(token, 0)
        idf = math.log(1 + (document_count - df + 0.5) / (df + 0.5))
        denominator = tf + k1 * (1 - b + b * doc_length / avg_doc_length)
        score += idf * (tf * (k1 + 1) / denominator)
    return score


def metadata_match(chunk: dict[str, Any], filters: dict[str, Any]) -> bool:
    for key, value in filters.items():
        if value in (None, "", []):
            continue
        if key not in chunk:
            continue
        if str(chunk[key]).lower() != str(value).lower():
            return False
    return True


def retrieve(index: dict[str, Any], query: str, top_k: int, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    query_tokens = tokenize(query, index["token_pattern"])
    filters = filters or {}
    scored = []
    for document in index["documents"]:
        chunk = document["chunk"]
        if not metadata_match(chunk, filters):
            continue
        score = score_document(query_tokens, document, index)
        if score > 0:
            scored.append({"chunk": chunk, "score": score})
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]

