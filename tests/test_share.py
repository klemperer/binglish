from binglish.games.share import (
    crossword_share_text,
    format_mmss,
    wordle_share_text,
)


def test_wordle_share_win():
    text = wordle_share_text(
        ["crane", "binglish"[0:5]],  # noqa: just two guesses
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


def test_crossword_share():
    text = crossword_share_text(
        time_label=format_mmss(83),
        hints=0,
        rank_text="Genius!",
    )
    assert "Binglish Crossword ✅" in text
    assert "01:23" in text
    assert "无提示" in text
    assert "Genius!" in text


def test_crossword_share_with_hints():
    text = crossword_share_text(
        time_label="00:45",
        hints=2,
        rank_text="Excellent!",
    )
    assert "提示 2 次" in text


def test_format_mmss():
    assert format_mmss(0) == "00:00"
    assert format_mmss(59) == "00:59"
    assert format_mmss(65) == "01:05"
    assert format_mmss(-5) == "00:00"
