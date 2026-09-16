from binglish.core.state import AppState


def test_overlay_lock():
    s = AppState()
    assert s.try_acquire_overlay() is True
    assert s.try_acquire_overlay() is False
    s.release_overlay()
    assert s.try_acquire_overlay() is True


def test_word_fields_roundtrip():
    s = AppState()
    s.set_word_fields(
        word="serendipity",
        dictionary_url="https://example.com/dict",
        audio_url="https://example.com/a.mp3",
        copyright="c",
        copyright_url="https://example.com",
        image_id="abc",
    )
    snap = s.snapshot_word_fields()
    assert snap["word"] == "serendipity"
    assert snap["image_id"] == "abc"
    s.clear_word_fields()
    assert s.snapshot_word_fields()["word"] is None


def test_music_fields_require_name_and_url():
    s = AppState()
    s.set_music_fields("Song", "https://example.com/s.mp3", "desc")
    assert s.music_name == "Song"
    s.set_music_fields("Song", None, "desc")
    assert s.music_name is None
