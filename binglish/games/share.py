"""Share-text builders and clipboard helper for game results."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence

log = logging.getLogger(__name__)

_SQUARE = {
    "green": "🟩",
    "yellow": "🟨",
    "gray": "⬛",
}

# Crossword: self-solved vs system-hinted (no letters leaked)
_CW_SELF = "🟩"
_CW_HINT = "🟪"
_CW_EMPTY = "⬛"

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


def crossword_grid_rows(
    valid_cells: dict[tuple[int, int], str],
    hinted_cells: Iterable[tuple[int, int]],
    *,
    min_x: int | None = None,
    max_x: int | None = None,
    min_y: int | None = None,
    max_y: int | None = None,
) -> list[str]:
    """
    Emoji grid for crossword: 🟩 self-solved, 🟪 hinted, ⬛ empty.
    Does not include letters.
    """
    if not valid_cells:
        return []
    hinted = set(hinted_cells)
    xs = [x for x, _ in valid_cells]
    ys = [y for _, y in valid_cells]
    x0 = min(xs) if min_x is None else min_x
    x1 = max(xs) if max_x is None else max_x
    y0 = min(ys) if min_y is None else min_y
    y1 = max(ys) if max_y is None else max_y

    rows: list[str] = []
    for y in range(y0, y1 + 1):
        parts: list[str] = []
        for x in range(x0, x1 + 1):
            coord = (x, y)
            if coord not in valid_cells:
                parts.append(_CW_EMPTY)
            elif coord in hinted:
                parts.append(_CW_HINT)
            else:
                parts.append(_CW_SELF)
        rows.append("".join(parts))
    return rows


def crossword_share_text(
    *,
    time_label: str,
    hints: int,
    rank_text: str,
    grid_rows: Sequence[str] | None = None,
) -> str:
    """Crossword result with optional color grid (no letters)."""
    hint_part = "无提示" if hints <= 0 else f"提示 {hints} 次"
    lines = [f"{APP_TAG} Crossword ✅"]
    if grid_rows:
        lines.extend(grid_rows)
    lines.append(f"用时 {time_label} · {hint_part} · {rank_text}")
    if grid_rows:
        lines.append("🟩自己填出 · 🟪系统提示")
    return "\n".join(lines)


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
