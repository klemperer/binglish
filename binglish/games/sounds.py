"""Game UI feedback sounds — low-latency, non-blocking."""

from __future__ import annotations

import logging
import sys
import threading
import time

log = logging.getLogger(__name__)

_lock = threading.Lock()
_last_click_at = 0.0
_CLICK_MIN_INTERVAL = 0.04  # 40ms: collapse burst keystrokes


def _play_windows(sound_type: str) -> None:
    import winsound

    if sound_type == "click":
        # SystemAsterisk is short; ASYNC so we never block the UI thread.
        # Without SND_NOSTOP, a new click interrupts the previous one (typing feel).
        winsound.PlaySound(
            "SystemAsterisk",
            winsound.SND_ALIAS | winsound.SND_ASYNC,
        )
    elif sound_type == "submit":
        # Single tone via MessageBeep — lighter than two sequential Beeps.
        winsound.MessageBeep(winsound.MB_OK)
    elif sound_type == "error":
        winsound.MessageBeep(winsound.MB_ICONHAND)


def _play_macos(sound_type: str) -> None:
    import subprocess

    # Very short system sounds; ASYNC via Popen (do not wait).
    name = {
        "click": "Tink",
        "submit": "Glass",
        "error": "Basso",
    }.get(sound_type, "Tink")
    path = f"/System/Library/Sounds/{name}.aiff"
    try:
        subprocess.Popen(
            ["afplay", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        log.debug("mac sound failed: %s", e)


def play_game_sound(sound_type: str = "click") -> None:
    """
    Fire-and-forget UI sound. Safe to call from the Tk main thread.
    click: throttled + interruptible so fast typing stays in sync.
    """
    global _last_click_at

    if sound_type == "click":
        with _lock:
            now = time.monotonic()
            if now - _last_click_at < _CLICK_MIN_INTERVAL:
                return
            _last_click_at = now

    try:
        if sys.platform.startswith("win"):
            _play_windows(sound_type)
        elif sys.platform == "darwin":
            _play_macos(sound_type)
    except Exception as e:
        log.debug("game sound failed: %s", e)
