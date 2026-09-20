"""Marshal UI work onto the Tk main thread."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from binglish.core.state import state
from binglish.ui import ui_queue

log = logging.getLogger(__name__)


def run_on_ui(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    """Schedule fn on the Tk main thread (or run inline if no root yet)."""

    def _call() -> None:
        try:
            fn(*args, **kwargs)
        except Exception:
            log.exception("run_on_ui failed: %s", getattr(fn, "__name__", fn))

    root = state.root
    if root is None:
        _call()
        return

    # Prefer the thread-safe pump (macOS tray events + any cross-thread posts).
    if ui_queue.is_pumping():
        ui_queue.post(_call)
        return

    try:
        root.after(0, _call)
    except Exception:
        log.warning("root.after unavailable; running inline")
        _call()
