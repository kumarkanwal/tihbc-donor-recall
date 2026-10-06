"""Prompt-file loading for reply-agent nodes."""

from functools import lru_cache
from pathlib import Path

PROMPT_DIRECTORY = Path(__file__).parent


@lru_cache
def load_prompt(name: str) -> str:
    """Load one reviewed prompt template from disk."""
    return (PROMPT_DIRECTORY / name).read_text(encoding="utf-8")
