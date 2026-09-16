"""Single-instance guard so two copies do not fight over wallpaper/config."""

from __future__ import annotations

import logging
import sys

log = logging.getLogger(__name__)

_mutex = None


def acquire_single_instance(name: str = "Binglish_SingleInstance") -> bool:
    """Return True if this process owns the instance lock."""
    global _mutex
    if not sys.platform.startswith("win"):
        return True
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.CreateMutexW(None, False, name)
        last_error = kernel32.GetLastError()
        ERROR_ALREADY_EXISTS = 183
        if not handle:
            log.warning("CreateMutex failed")
            return True
        if last_error == ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return False
        _mutex = handle
        return True
    except Exception as e:
        log.warning("single-instance check failed: %s", e)
        return True


def release_single_instance() -> None:
    global _mutex
    if _mutex is None:
        return
    try:
        import ctypes

        ctypes.windll.kernel32.CloseHandle(_mutex)
    except Exception:
        pass
    _mutex = None
