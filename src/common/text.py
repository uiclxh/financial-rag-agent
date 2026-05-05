"""Tokenization utilities shared by retrieval and evaluation."""

from __future__ import annotations

import re


DEFAULT_TOKEN_PATTERN = r"[A-Za-z0-9$%.-]+"


def tokenize(text: str, token_pattern: str = DEFAULT_TOKEN_PATTERN) -> list[str]:
    return [token.lower() for token in re.findall(token_pattern, text)]

