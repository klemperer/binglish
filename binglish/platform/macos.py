"""macOS adapter (subset; port of original mac helpers)."""

from __future__ import annotations

import logging
import os
import plistlib
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


class MacAdapter:
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

    def screen_size(self) -> tuple[int, int]:
        try:
            from AppKit import NSScreen  # type: ignore

            frame = NSScreen.mainScreen().frame()
            return int(frame.size.width), int(frame.size.height)
        except Exception:
            return 1920, 1080

    def open_path(self, path: str) -> None:
        subprocess.Popen(["open", path])

    def beep(self, freq: int, duration_ms: int) -> None:
        try:
            subprocess.Popen(["afplay", "/System/Library/Sounds/Tink.aiff"])
        except Exception:
            pass
