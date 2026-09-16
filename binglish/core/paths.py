"""Filesystem paths for config, wallpaper, assets, and logs."""

from __future__ import annotations

import sys
from pathlib import Path


def app_dir() -> Path:
    """Directory that holds wallpaper/config next to the executable or script."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # package root's parent (repo root when running from source)
    return Path(__file__).resolve().parents[2]


def resource_path(relative_path: str) -> Path:
    """Resolve bundled resource (PyInstaller _MEIPASS or repo assets/)."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass) / relative_path
    # Prefer packaged assets folder when running from source
    candidate = app_dir() / "assets" / relative_path
    if candidate.exists():
        return candidate
    return Path(relative_path).resolve()


def config_path() -> Path:
    return app_dir() / "binglish.ini"


def wallpaper_path() -> Path:
    return app_dir() / "wallpaper.jpg"


def debug_log_path() -> Path:
    return app_dir() / "binglish_debug.log"


def executable_path() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    return str(Path(__file__).resolve().parents[1] / "app.py")
