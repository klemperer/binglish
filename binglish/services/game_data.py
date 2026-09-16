"""Game remote data + pure logic helpers."""

from __future__ import annotations

import logging
from typing import Any, Optional

from binglish.core.constants import (
    CROSSWORD_URL,
    GAME_DATA_URL,
    VOCAB_TEST_URL,
    WORDLE_VALIDATE_URL,
)
from binglish.services import http

log = logging.getLogger(__name__)


def fetch_game_catalog() -> dict:
    """Lobby catalog (sentence / wordle answers). May contain secrets — treat carefully."""
    try:
        data = http.get_json(GAME_DATA_URL, timeout=15)
    except http.HttpError as e:
        log.warning("game catalog failed: %s", e)
        return {}
    return data if isinstance(data, dict) else {}


def validate_wordle_guess(word: str) -> Optional[str]:
    """Return definition text, empty string if invalid, None on network error."""
    url = f"{WORDLE_VALIDATE_URL}?q={word}"
    try:
        text = http.get_text(url, timeout=10)
        return text.strip()
    except http.HttpError as e:
        log.warning("wordle validate failed: %s", e)
        return None


def fetch_crossword() -> Optional[dict]:
    try:
        payload = http.get_json(CROSSWORD_URL, timeout=10)
    except http.HttpError as e:
        log.warning("crossword fetch failed: %s", e)
        return None
    if isinstance(payload, dict):
        return payload.get("data")
    return None


def fetch_vocab_test() -> list[dict]:
    try:
        payload = http.get_json(VOCAB_TEST_URL, timeout=10)
    except http.HttpError as e:
        log.warning("vocab test fetch failed: %s", e)
        return []
    if isinstance(payload, dict):
        words = payload.get("test_words", [])
        return words if isinstance(words, list) else []
    return []


# --- pure logic (unit-testable) ---


def wordle_colors(guess: str, target: str) -> list[str]:
    """Return per-letter colors: green / yellow / gray."""
    g = guess.lower()
    t = target.lower()
    n = len(t)
    colors: list[Optional[str]] = [None] * n
    remaining = list(t)

    for i in range(n):
        if g[i] == t[i]:
            colors[i] = "green"
            remaining[i] = None
    for i in range(n):
        if colors[i] is None:
            if g[i] in remaining:
                colors[i] = "yellow"
                remaining[remaining.index(g[i])] = None
            else:
                colors[i] = "gray"
    return [c or "gray" for c in colors]


def vocab_score(test_words: list[dict], selected: set[str]) -> dict:
    """
    Score a vocabulary test.
    test_words: [{word, rank, is_trap}, ...]
    selected: words the user marked as known.
    """
    bucket_counts = {i: 0 for i in range(10)}
    bucket_totals = {i: 0 for i in range(10)}
    trap_count = 0

    for w in test_words:
        if not w.get("is_trap"):
            idx = (w.get("rank", 0) - 1) // 1000
            if 0 <= idx <= 9:
                bucket_totals[idx] += 1

    for w in test_words:
        word = w.get("word")
        if word not in selected:
            continue
        if w.get("is_trap"):
            trap_count += 1
        else:
            idx = (w.get("rank", 0) - 1) // 1000
            if 0 <= idx <= 9:
                bucket_counts[idx] += 1

    score = 0
    for i in range(10):
        if bucket_totals[i] > 0:
            score += (bucket_counts[i] / float(bucket_totals[i])) * 1000

    score -= trap_count * 1500
    score = max(0, int(score))

    if score >= 8500:
        rank_title = "Godlike!"
    elif score >= 6000:
        rank_title = "Walking Dictionary!"
    elif score >= 4000:
        rank_title = "Excellent!"
    elif score >= 2000:
        rank_title = "Good Start!"
    else:
        rank_title = "Keep Trying!"

    return {"score": score, "traps": trap_count, "rank_title": rank_title}


def sentence_master_rank(attempts: int) -> str:
    if attempts == 1:
        return "Godlike!"
    if attempts <= 2:
        return "Impressive!"
    if attempts <= 4:
        return "Excellent!"
    if attempts <= 6:
        return "Good Job!"
    return "Well Done!"
