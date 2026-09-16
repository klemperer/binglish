"""Thin HTTP helpers shared by services."""

from __future__ import annotations

import logging
from typing import Any

import requests

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15


class HttpError(RuntimeError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def get_json(url: str, timeout: int = DEFAULT_TIMEOUT) -> Any:
    try:
        resp = requests.get(url, timeout=timeout)
    except requests.RequestException as e:
        raise HttpError(f"request failed: {e}") from e
    if resp.status_code != 200:
        raise HttpError(f"HTTP {resp.status_code} for {url}", resp.status_code)
    try:
        return resp.json()
    except ValueError as e:
        raise HttpError(f"invalid JSON from {url}") from e


def get_text(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    try:
        resp = requests.get(url, timeout=timeout)
    except requests.RequestException as e:
        raise HttpError(f"request failed: {e}") from e
    if resp.status_code != 200:
        raise HttpError(f"HTTP {resp.status_code} for {url}", resp.status_code)
    return resp.text


def download_file(url: str, dest: str, timeout: int = 20) -> bool:
    """Stream download to dest. Returns True on success."""
    try:
        with requests.get(url, stream=True, timeout=timeout) as resp:
            if resp.status_code != 200:
                log.error("download failed status=%s url=%s", resp.status_code, url)
                return False
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=64 * 1024):
                    if chunk:
                        f.write(chunk)
        return True
    except requests.RequestException as e:
        log.error("download error: %s", e)
        return False
    except OSError as e:
        log.error("write error for %s: %s", dest, e)
        return False


def host_reachable(url: str, timeout: int = 10) -> bool:
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.RequestException:
        return False
