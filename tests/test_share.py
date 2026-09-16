from binglish.games.share import (
    crossword_grid_rows,
    crossword_share_text,
    format_mmss,
    wordle_share_text,
)


def test_wordle_share_win():
    text = wordle_share_text(
        ["crane", "bingl"],
        [
            ["gray", "yellow", "gray", "gray", "green"],
            ["green", "green", "green", "green", "green"],
        ],
        won=True,
    )
    lines = text.splitlines()
    assert lines[0] == "Binglish Wordle 2/6"
    assert lines[1] == "⬛🟨⬛⬛🟩"
    assert lines[2] == "🟩🟩🟩🟩🟩"


def test_wordle_share_lose():
    text = wordle_share_text(
        ["aaaaa"],
        [["gray"] * 5],
        won=False,
    )
    assert text.splitlines()[0] == "Binglish Wordle X/6"
    assert text.splitlines()[1] == "⬛⬛⬛⬛⬛"


def test_crossword_grid_self_vs_hint():
    # 3x2 grid with one empty black cell and one hinted
    valid = {
        (0, 0): "A",
        (1, 0): "B",
        (2, 0): "C",
        (0, 1): "D",
        (1, 1): "E",
        # (2,1) missing → black
    }
    rows = crossword_grid_rows(valid, hinted_cells={(1, 0)})
    assert rows == ["🟩🟪🟩", "🟩🟩⬛"]


def test_crossword_share_with_grid():
    grid = ["🟩🟪🟩", "🟩🟩⬛"]
    text = crossword_share_text(
        time_label="01:23",
        hints=1,
        rank_text="Excellent!",
        grid_rows=grid,
    )
    lines = text.splitlines()
    assert lines[0] == "Binglish Crossword ✅"
    assert lines[1] == "🟩🟪🟩"
    assert lines[2] == "🟩🟩⬛"
    assert "01:23" in lines[3]
    assert "提示 1 次" in lines[3]
    assert "🟩自己填出" in lines[4]


def test_crossword_share_without_grid():
    text = crossword_share_text(
        time_label=format_mmss(83),
        hints=0,
        rank_text="Genius!",
    )
    assert "Binglish Crossword ✅" in text
    assert "01:23" in text
    assert "无提示" in text
    assert "Genius!" in text
    assert "🟩" not in text.splitlines()[0]


def test_format_mmss():
    assert format_mmss(0) == "00:00"
    assert format_mmss(59) == "00:59"
    assert format_mmss(65) == "01:05"
    assert format_mmss(-5) == "00:00"

