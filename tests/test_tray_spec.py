"""Menu spec model used by the macOS tray child process."""

from __future__ import annotations

from binglish.core.state import state
from binglish.ui import tray


def test_build_menu_spec_has_about_and_quit():
    state.word = None
    state.dictionary_url = None
    state.audio_url = None
    state.music_name = None
    state.music_url = None
    state.copyright = None
    state.image_id = None
    state.is_rest_enabled = False
    spec = tray.build_menu_spec()
    keys = [row.get("key") for row in spec]
    assert "about" in keys
    assert "quit" in keys
    assert "random_review" in keys
    assert all(isinstance(row, dict) for row in spec)


def test_build_menu_spec_rest_checked():
    state.is_rest_enabled = True
    state.word = None
    state.dictionary_url = None
    state.audio_url = None
    spec = tray.build_menu_spec()
    rest = next(r for r in spec if r.get("key") == "toggle_rest")
    assert rest["checked"] is True
    state.is_rest_enabled = False
