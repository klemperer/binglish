from binglish.services.game_data import sentence_master_rank, vocab_score, wordle_colors


def test_wordle_all_green():
    assert wordle_colors("crane", "crane") == ["green"] * 5


def test_wordle_mixed():
    colors = wordle_colors("abcde", "axcye")
    assert colors[0] == "green"
    assert colors[2] == "green"
    assert colors[4] == "green"
    assert colors[1] == "gray"
    assert colors[3] == "gray"


def test_wordle_yellow_duplicate_handling():
    # target has a single 'a' at index 1; guess places 'a' at 0 and 1
    colors = wordle_colors("aabcd", "xaxxx")
    assert colors[1] == "green"  # exact match consumes the only 'a'
    assert colors[0] == "gray"   # second 'a' has no remaining match


def test_vocab_score_traps_penalize():
    words = [
        {"word": "apple", "rank": 100, "is_trap": False},
        {"word": "zzzzfake", "rank": 0, "is_trap": True},
    ]
    clean = vocab_score(words, {"apple"})
    dirty = vocab_score(words, {"apple", "zzzzfake"})
    assert clean["traps"] == 0
    assert dirty["traps"] == 1
    assert dirty["score"] < clean["score"]


def test_sentence_rank():
    assert sentence_master_rank(1) == "Godlike!"
    assert sentence_master_rank(8) == "Well Done!"
