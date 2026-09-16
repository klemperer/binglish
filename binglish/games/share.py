"""Share-text builders and clipboard helper for game results."""

from __future__ import annotations

import logging
from typing import Sequence

log = logging.getLogger(__name__)

_SQUARE = {
    "green": "🟩",
    "yellow": "🟨",
    "gray": "⬛",
}

APP_TAG = "Binglish"


def wordle_share_text(
    guesses: Sequence[str],
    color_rows: Sequence[Sequence[str]],
    *,
    won: bool,
    max_rows: int = 6,
) -> str:
    """
    Wordle-style share block.

    guesses: submitted words in order
    color_rows: parallel list of per-letter colors ('green'|'yellow'|'gray')
    """
    n = len(guesses)
    score = f"{n}/{max_rows}" if won else f"X/{max_rows}"
    lines = [f"{APP_TAG} Wordle {score}"]
    for colors in color_rows:
        lines.append("".join(_SQUARE.get(c, "⬛") for c in colors))
    return "\n".join(lines)


def crossword_share_text(
    *,
    time_label: str,
    hints: int,
    rank_text: str,
) -> str:
    """Plain-text crossword result (no letter grid — avoids spoiling answers)."""
    hint_part = "无提示" if hints <= 0 else f"提示 {hints} 次"
    return (
        f"{APP_TAG} Crossword ✅\n"
        f"用时 {time_label} · {hint_part} · {rank_text}"
    )


def format_mmss(total_seconds: int) -> str:
    total_seconds = max(0, int(total_seconds))
    return f"{total_seconds // 60:02d}:{total_seconds % 60:02d}"


def copy_text(widget, text: str) -> bool:
    """Copy to system clipboard via Tk; fall back to clip.exe on Windows."""
    try:
        widget.clipboard_clear()
        widget.clipboard_append(text)
        try:
            widget.update_idletasks()
        except Exception:
            pass
        return True
    except Exception as e:
        log.warning("tk clipboard failed: %s", e)
    try:
        import subprocess
        import sys

        if sys.platform.startswith("win"):
            subprocess.run(
                ["clip"],
                input=text.encode("utf-8"),
                check=False,
                timeout=5,
            )
            return True
    except Exception as e:
        log.error("clip fallback failed: %s", e)
    return False
