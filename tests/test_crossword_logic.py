from binglish.games.crossword_logic import (
    first_unsolved_index,
    focus_target_for_word,
    next_incomplete_word,
    other_direction,
    step_in_word,
    word_at,
    word_cells,
    word_is_filled_correct,
    wrap_index,
)


def _w(number, x, y, length, answer, dir_="Across"):
    return {
        "number": number,
        "x": x,
        "y": y,
        "length": length,
        "answer": answer,
        "dir": dir_,
    }


def test_word_cells_across_down():
    assert word_cells(_w(1, 0, 0, 3, "abc")) == [(0, 0), (1, 0), (2, 0)]
    assert word_cells(_w(2, 1, 0, 3, "xyz", "Down")) == [(1, 0), (1, 1), (1, 2)]


def test_first_unsolved_skips_correct_prefix():
    w = _w(1, 0, 0, 4, "WORD")
    # letters at (0,0)=W correct, (1,0)=O correct, (2,0)=X wrong
    chars = {(0, 0): "W", (1, 0): "O", (2, 0): "X", (3, 0): ""}
    assert first_unsolved_index(w, lambda c: chars.get(c, "")) == 2


def test_first_unsolved_all_correct_returns_zero():
    w = _w(1, 0, 0, 3, "CAT")
    chars = {(0, 0): "C", (1, 0): "A", (2, 0): "T"}
    assert first_unsolved_index(w, lambda c: chars.get(c, "")) == 0


def test_wrap_index():
    assert wrap_index(2, 3, 1) == 0
    assert wrap_index(0, 3, -1) == 2


def test_step_in_word_wraps():
    cells = [(0, 0), (1, 0), (2, 0)]
    assert step_in_word(cells, (2, 0), 1) == (0, 0)
    assert step_in_word(cells, (0, 0), -1) == (2, 0)


def test_other_direction():
    assert other_direction("Across") == "Down"
    assert other_direction("Down") == "Across"


def test_word_at():
    words = [
        _w(1, 0, 0, 3, "CAT"),
        _w(2, 1, 0, 3, "ANT", "Down"),
    ]
    assert word_at(words, (1, 0), "Across")["number"] == 1
    assert word_at(words, (1, 1), "Down")["number"] == 2
    assert word_at(words, (5, 5), "Across") is None


def test_next_incomplete_word_tab_wrap():
    w1 = _w(1, 0, 0, 2, "AB")
    w2 = _w(2, 0, 1, 2, "CD")
    w3 = _w(3, 0, 2, 2, "EF")
    # w1 complete, w2/w3 incomplete
    chars = {
        (0, 0): "A",
        (1, 0): "B",
        (0, 1): "C",
        (1, 1): "",
        (0, 2): "",
        (1, 2): "F",
    }
    words = [w1, w2, w3]
    get = lambda c: chars.get(c, "")
    nxt = next_incomplete_word(words, w2, get, step=1)
    assert nxt["number"] == 3
    nxt2 = next_incomplete_word(words, w3, get, step=1)
    assert nxt2["number"] == 2  # wrap
    prev = next_incomplete_word(words, w2, get, step=-1)
    assert prev["number"] == 3


def test_focus_target_skips_correct_letters():
    w = _w(1, 0, 0, 3, "CAT")
    chars = {(0, 0): "C", (1, 0): "X"}
    assert focus_target_for_word(w, lambda c: chars.get(c, "")) == (1, 0)


def test_word_is_filled_correct():
    w = _w(1, 0, 0, 3, "CAT")
    ok = {(0, 0): "C", (1, 0): "A", (2, 0): "T"}
    bad = {(0, 0): "C", (1, 0): "A", (2, 0): "X"}
    assert word_is_filled_correct(w, lambda c: ok.get(c, ""))
    assert not word_is_filled_correct(w, lambda c: bad.get(c, ""))
