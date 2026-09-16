"""INI config load/save."""

from __future__ import annotations

import configparser
import logging
import re
from pathlib import Path

from binglish.core import paths
from binglish.core.constants import (
    IDLE_RESET_DEFAULT,
    OVERLAY_COLOR_DEFAULT,
    REST_INTERVAL_DEFAULT,
    REST_LOCK_DEFAULT,
)
from binglish.core.state import state

log = logging.getLogger(__name__)

_DEFAULT_INI = """[Settings]
; 是否开启休息提醒 (0:关闭, 1:开启)
IS_REST_ENABLED = 0

; 休息间隔时间(秒)，默认45分钟
REST_INTERVAL_SECONDS = 2700

; 闲置重置时间(秒)，默认5分钟不动则重置计时
IDLE_RESET_SECONDS = 300

; 强制休息锁定时间(秒)
REST_LOCK_SECONDS = 30

; 遮罩层背景颜色 (Hex代码)
OVERLAY_COLOR = #2C3E50

; Debug 日志 (0:关闭, 1:开启)
DEBUG_ENABLED = 0
"""


def ensure_default_config() -> Path:
    path = paths.config_path()
    if not path.exists():
        try:
            path.write_text(_DEFAULT_INI, encoding="utf-8-sig")
            log.info("created default config: %s", path)
        except OSError as e:
            log.error("failed to create config: %s", e)
    return path


def load_config_into_state() -> None:
    """Populate rest-reminder settings from binglish.ini into AppState."""
    path = ensure_default_config()
    cfg = configparser.ConfigParser()
    try:
        cfg.read(path, encoding="utf-8-sig")
    except configparser.Error as e:
        log.error("config parse error: %s — using defaults", e)
        return

    if "Settings" not in cfg:
        log.warning("no [Settings] section; using defaults")
        return

    s = cfg["Settings"]
    with state.lock:
        state.is_rest_enabled = s.getboolean("IS_REST_ENABLED", fallback=False)
        state.rest_interval_seconds = s.getint(
            "REST_INTERVAL_SECONDS", fallback=REST_INTERVAL_DEFAULT
        )
        state.idle_reset_seconds = s.getint(
            "IDLE_RESET_SECONDS", fallback=IDLE_RESET_DEFAULT
        )
        state.rest_lock_seconds = s.getint(
            "REST_LOCK_SECONDS", fallback=REST_LOCK_DEFAULT
        )
        color = s.get("OVERLAY_COLOR", fallback=OVERLAY_COLOR_DEFAULT)
        color = (color or OVERLAY_COLOR_DEFAULT).strip().strip('"').strip("'")
        if color:
            state.overlay_color = color

    log.info(
        "config loaded: rest=%s interval=%ss lock=%ss color=%s",
        state.is_rest_enabled,
        state.rest_interval_seconds,
        state.rest_lock_seconds,
        state.overlay_color,
    )


def debug_enabled() -> bool:
    path = paths.config_path()
    if not path.exists():
        return False
    cfg = configparser.ConfigParser()
    try:
        cfg.read(path, encoding="utf-8-sig")
        return cfg.getboolean("Settings", "DEBUG_ENABLED", fallback=False)
    except (configparser.Error, ValueError):
        return False


def save_rest_enabled(enabled: bool) -> None:
    """Rewrite IS_REST_ENABLED while preserving comments/other keys."""
    path = ensure_default_config()
    try:
        content = path.read_text(encoding="utf-8-sig")
    except OSError as e:
        log.error("read config failed: %s", e)
        return

    new_val = "1" if enabled else "0"
    pattern = r"(?m)(?i)(^\s*IS_REST_ENABLED\s*=\s*)([^;\r\n]*)"
    if re.search(pattern, content):
        new_content = re.sub(pattern, rf"\g<1>{new_val}", content)
        path.write_text(new_content, encoding="utf-8-sig")
        log.info("saved IS_REST_ENABLED = %s", new_val)
    else:
        log.warning("IS_REST_ENABLED key not found; config not updated")
