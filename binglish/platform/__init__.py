"""Platform adapters: wallpaper, idle, startup, fullscreen."""

from __future__ import annotations

import sys
from typing import Protocol


class PlatformAdapter(Protocol):
    def set_wallpaper(self, image_path: str) -> bool: ...
    def get_idle_seconds(self) -> float: ...
    def is_foreground_fullscreen(self) -> bool: ...
    def is_startup_enabled(self) -> bool: ...
    def set_startup(self, enabled: bool) -> bool: ...
    def screen_size(self) -> tuple[int, int]: ...
    def open_path(self, path: str) -> None: ...


def get_platform() -> PlatformAdapter:
    if sys.platform.startswith("win"):
        from binglish.platform.windows import WindowsAdapter

        return WindowsAdapter()
    if sys.platform == "darwin":
        from binglish.platform.macos import MacAdapter

        return MacAdapter()
    raise RuntimeError(f"unsupported platform: {sys.platform}")
