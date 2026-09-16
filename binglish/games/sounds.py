"""Game UI feedback sounds."""

from __future__ import annotations

import logging
import sys
import threading

log = logging.getLogger(__name__)


def play_game_sound(sound_type: str = "click") -> None:
    def _play() -> None:
        try:
            if sys.platform.startswith("win"):
                import ctypes

                if sound_type == "click":
                    ctypes.windll.kernel32.Beep(800, 30)
                elif sound_type == "submit":
                    ctypes.windll.kernel32.Beep(600, 50)
                    ctypes.windll.kernel32.Beep(900, 50)
        except Exception as e:
            log.debug("game sound failed: %s", e)

    threading.Thread(target=_play, daemon=True).start()
