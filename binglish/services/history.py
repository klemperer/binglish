"""History / facts / word-audio fetchers."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from binglish.core.constants import HISTORY_URL_BASE, USELESS_FACT_URL
from binglish.services import http

log = logging.getLogger(__name__)


def fetch_on_this_day() -> tuple[list[dict], str]:
    """Return (events, date_label). Empty list if none/failure."""
    now = datetime.now()
    date_str = now.strftime("%b. %d")
    url = f"{HISTORY_URL_BASE}?mm={now.month}&dd={now.day}"
    try:
        data = http.get_json(url, timeout=10)
    except http.HttpError as e:
        log.warning("history fetch failed: %s", e)
        return [], date_str
    if isinstance(data, list) and data:
        return data, date_str
    return [], date_str


def fetch_useless_fact() -> tuple[str, str]:
    """Return (en, cn); empty strings on failure."""
    try:
        data = http.get_json(USELESS_FACT_URL, timeout=10)
    except http.HttpError as e:
        log.warning("fact fetch failed: %s", e)
        return "", ""
    if not isinstance(data, dict):
        return "", ""
    return data.get("en") or "", data.get("cn") or ""
