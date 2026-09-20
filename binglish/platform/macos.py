"""macOS adapter — no AppKit in this process (tray child owns Cocoa)."""

from __future__ import annotations

import logging
import os
import plistlib
import subprocess
import threading
from pathlib import Path

from binglish.core.state import state

log = logging.getLogger(__name__)

_DEFAULT_SCREEN = (1920, 1080)
_screen_cache: tuple[int, int] | None = None
_screen_lock = threading.Lock()


def _store_screen(size: tuple[int, int]) -> tuple[int, int]:
    global _screen_cache
    with _screen_lock:
        _screen_cache = size
    return size


def warm_screen_size_from_tk(root) -> tuple[int, int]:
    """Cache screen size from Tk on the main thread (call at startup)."""
    try:
        size = (int(root.winfo_screenwidth()), int(root.winfo_screenheight()))
        if size[0] > 0 and size[1] > 0:
            return _store_screen(size)
    except Exception as e:
        log.warning("tk screen size warm-up failed: %s", e)
    return _cached_or_fetch()


def _cached_or_fetch() -> tuple[int, int]:
    global _screen_cache
    with _screen_lock:
        if _screen_cache is not None:
            return _screen_cache

    root = state.root
    if root is not None and threading.current_thread() is threading.main_thread():
        try:
            size = (int(root.winfo_screenwidth()), int(root.winfo_screenheight()))
            if size[0] > 0 and size[1] > 0:
                return _store_screen(size)
        except Exception as e:
            log.warning("tk screen size failed: %s", e)

    # Workers never touch GUI APIs; warm-up on main fills the cache at startup.
    return _store_screen(_DEFAULT_SCREEN)


class MacAdapter:
    def warm_screen_size(self, root) -> tuple[int, int]:
        return warm_screen_size_from_tk(root)

    def screen_size(self) -> tuple[int, int]:
        return _cached_or_fetch()

    def set_wallpaper(self, image_path: str) -> bool:
        script = f'''
        tell application "System Events"
            set picture of every desktop to POSIX file "{image_path}"
        end tell
        '''
        try:
            subprocess.run(["osascript", "-e", script], check=True, timeout=10)
            return True
        except Exception as e:
            log.error("mac set wallpaper failed: %s", e)
            return False

    def get_idle_seconds(self) -> float:
        try:
            out = subprocess.check_output(
                ["ioreg", "-c", "IOHIDSystem"], timeout=5, text=True
            )
            for line in out.splitlines():
                if "HIDIdleTime" in line:
                    parts = line.split("=")
                    if len(parts) >= 2:
                        nanos = int(parts[-1].strip())
                        return nanos / 1_000_000_000.0
        except Exception as e:
            log.warning("mac idle query failed: %s", e)
        return 0.0

    def is_foreground_fullscreen(self) -> bool:
        # Conservative: never suppress rest reminder on mac in this port.
        return False

    def _plist_path(self) -> Path:
        return (
            Path.home()
            / "Library"
            / "LaunchAgents"
            / "org.blueforge.binglish.plist"
        )

    def is_startup_enabled(self) -> bool:
        return self._plist_path().exists()

    def set_startup(self, enabled: bool) -> bool:
        plist = self._plist_path()
        try:
            if not enabled:
                if plist.exists():
                    plist.unlink()
                return True
            exe = os.sys.executable
            payload = {
                "Label": "org.blueforge.binglish",
                "ProgramArguments": [exe],
                "RunAtLoad": True,
            }
            plist.parent.mkdir(parents=True, exist_ok=True)
            with open(plist, "wb") as f:
                plistlib.dump(payload, f)
            return True
        except OSError as e:
            log.error("mac startup toggle failed: %s", e)
            return False

    def open_path(self, path: str) -> None:
        subprocess.Popen(["open", path])

    def beep(self, freq: int, duration_ms: int) -> None:
        try:
            subprocess.Popen(["afplay", "/System/Library/Sounds/Tink.aiff"])
        except Exception:
            pass
