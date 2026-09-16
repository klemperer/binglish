"""Logging bootstrap."""

from __future__ import annotations

import logging
import sys

from binglish.core import paths


def setup_logging(debug: bool = False) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if debug:
        try:
            fh = logging.FileHandler(
                paths.debug_log_path(), encoding="utf-8", delay=True
            )
            handlers.append(fh)
        except OSError:
            pass

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )
