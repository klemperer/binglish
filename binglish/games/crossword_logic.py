"""Pure crossword navigation helpers (unit-testable, no Tk)."""

from __future__ import annotations

from collections.abc import Callable, Sequence

Coord = tuple[int, int]
Dir = str  # "Across" | "Down"


def word_cells(word: dict) -> list[Coord]:
    cells: list[Coord] = []
    x, y = word["x"], word["y"]
    for i in range(word["length"]):
        if word["dir"] == "Across":
            cells.append((x + i, y))
        else:
            cells.append((x, y + i))
    return cells


def word_id(word: dict) -> str:
    return f"{word['dir']}_{word['number']}"


def ordered_words(words: Sequence[dict]) -> list[dict]:
    return sorted(
        words,
        key=lambda w: (0 if w["dir"] == "Across" else 1, int(w.get("number", 0))),
    )


def first_unsolved_index(
    word: dict,
    get_char: Callable[[Coord], str],
) -> int:
    """Index of first letter that is empty or incorrect. 0 if all correct."""
    answer = word.get("answer") or ""
    for i, coord in enumerate(word_cells(word)):
        ch = (get_char(coord) or "").strip().upper()
        if i >= len(answer) or ch != answer[i].upper():
            return i
    return 0


def wrap_index(index: int, length: int, delta: int) -> int:
    if length <= 0:
        return 0
    return (index + delta) % length


def step_in_word(
    cells: Sequence[Coord],
    current: Coord,
    delta: int,
) -> Coord | None:
    """Move within the word by delta cells with wrap. None if current not in word."""
    try:
        idx = list(cells).index(current)
    except ValueError:
        return None
    return cells[wrap_index(idx, len(cells), delta)]


def word_at(
    words: Sequence[dict],
    coord: Coord,
    direction: Dir,
) -> dict | None:
    for w in words:
        if w.get("dir") != direction:
            continue
        if coord in word_cells(w):
            return w
    return None


def word_is_filled_correct(word: dict, get_char: Callable[[Coord], str]) -> bool:
    answer = word.get("answer") or ""
    chars = [(get_char(c) or "").strip().upper() for c in word_cells(word)]
    return "".join(chars) == answer.upper()


def next_incomplete_word(
    words: Sequence[dict],
    current: dict | None,
    get_char: Callable[[Coord], str],
    step: int = 1,
) -> dict | None:
    """
    Next/previous word that is not fully correct.
    Order: Across then Down, by number. Wraps around.
    step: +1 forward (Tab), -1 backward (Shift+Tab).
    """
    seq = ordered_words(words)
    if not seq:
        return None
    incomplete = [w for w in seq if not word_is_filled_correct(w, get_char)]
    if not incomplete:
        # all done — still cycle through all words
        incomplete = seq

    if current is None:
        return incomplete[0] if step >= 0 else incomplete[-1]

    ids = [word_id(w) for w in incomplete]
    try:
        pos = ids.index(word_id(current))
    except ValueError:
        # current word is complete; start from next in full order
        full_ids = [word_id(w) for w in seq]
        try:
            full_pos = full_ids.index(word_id(current))
        except ValueError:
            return incomplete[0] if step >= 0 else incomplete[-1]
        for k in range(len(seq)):
            j = (full_pos + (k + 1) * (1 if step >= 0 else -1)) % len(seq)
            cand = seq[j]
            if not word_is_filled_correct(cand, get_char) or cand is current:
                if not word_is_filled_correct(cand, get_char):
                    return cand
        return incomplete[0]

    return incomplete[(pos + step) % len(incomplete)]


def focus_target_for_word(
    word: dict,
    get_char: Callable[[Coord], str],
) -> Coord:
    cells = word_cells(word)
    i = first_unsolved_index(word, get_char)
    return cells[i]


def other_direction(direction: Dir) -> Dir:
    return "Down" if direction == "Across" else "Across"
