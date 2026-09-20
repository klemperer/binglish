"""Thread-safe UI job queue drained by Tk's main loop."""

from __future__ import annotations

import logging
import queue
from collections.abc import Callable
from typing import Any

log = logging.getLogger(__name__)

_q: queue.SimpleQueue = queue.SimpleQueue()
_pumping = False


def is_pumping() -> bool:
    return _pumping


def post(fn: Callable[[], Any]) -> None:
    """Queue a callable to run on the Tk main loop."""
    _q.put(fn)


def start_pump(root, interval_ms: int = 50) -> None:
    """Poll the queue from Tk after(); safe for cross-thread UI posts."""
    global _pumping
    if _pumping:
        return
    _pumping = True

    def _tick() -> None:
        while True:
            try:
                fn = _q.get_nowait()
            except queue.Empty:
                break
            except Exception:
                break
            try:
                fn()
            except Exception:
                log.exception("ui job failed: %s", getattr(fn, "__name__", fn))
        try:
            if root.winfo_exists():
                root.after(interval_ms, _tick)
        except Exception:
            pass

    try:
        root.after(interval_ms, _tick)
    except Exception:
        _pumping = False
        log.exception("ui pump start failed")
