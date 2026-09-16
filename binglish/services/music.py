"""Song of the Day service."""

from __future__ import annotations

import logging
import multiprocessing
from typing import Any

from binglish.core.constants import MUSIC_JSON_URL
from binglish.core.state import state
from binglish.services import http

log = logging.getLogger(__name__)


def fetch_song_of_the_day() -> bool:
    try:
        data = http.get_json(MUSIC_JSON_URL, timeout=10)
    except http.HttpError as e:
        log.warning("song fetch failed: %s", e)
        state.clear_music_fields()
        return False

    if not isinstance(data, dict):
        state.clear_music_fields()
        return False

    name = data.get("name")
    url = data.get("url")
    desc = data.get("description")
    state.set_music_fields(name, url, desc)
    if state.music_name:
        log.info("song of the day: %s", state.music_name)
        return True
    return False


def _play_task(url: str) -> None:
    try:
        from playsound3 import playsound

        playsound(url)
    except Exception as e:  # playsound can raise many backend errors
        log.error("music playback error: %s", e)


def start_playback() -> Any | None:
    """Spawn a process to play the current song. Returns process or None."""
    if not state.music_url:
        return None
    proc = multiprocessing.Process(target=_play_task, args=(state.music_url,), daemon=True)
    proc.start()
    with state.lock:
        state.music_process = proc
        state.is_music_playing = True
    log.info("music process started pid=%s", proc.pid)
    return proc


def stop_playback() -> None:
    with state.lock:
        proc = state.music_process
        state.music_process = None
        state.is_music_playing = False
        timer = state.music_check_timer
        state.music_check_timer = None
    if proc is not None and proc.is_alive():
        proc.terminate()
        log.info("music process terminated")
    if timer is not None and state.root is not None:
        try:
            state.root.after_cancel(timer)
        except Exception:
            pass
