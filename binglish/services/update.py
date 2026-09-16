"""Self-update: CDN fast path + GitHub Releases as authoritative source."""

from __future__ import annotations

import hashlib
import logging
import subprocess
from collections.abc import Callable
from pathlib import Path

from binglish.core.constants import (
    APP_NAME,
    BING_HOME,
    DOWNLOAD_URL,
    GITHUB_API_LATEST,
    GITHUB_LATEST_RELEASE_URL,
    RELEASE_JSON_URL,
    VERSION,
)
from binglish.core.version import is_newer
from binglish.services import http

log = logging.getLogger(__name__)


def file_sha256(path: str | Path) -> str | None:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                h.update(block)
        return h.hexdigest()
    except OSError as e:
        log.error("hash failed: %s", e)
        return None


def github_releases_url() -> str:
    return GITHUB_LATEST_RELEASE_URL


def check_release() -> dict:
    """
    CDN channel (primary auto-update). Returns:
      status: 'update_available' | 'no_update' | 'error'
      version, notes, hash, error, source='cdn'
    """
    try:
        info = http.get_json(RELEASE_JSON_URL, timeout=20)
    except http.HttpError as e:
        return {"status": "error", "error": str(e), "source": "cdn"}

    if not isinstance(info, dict):
        return {"status": "error", "error": "unexpected release payload", "source": "cdn"}

    latest = info.get("version")
    notes = info.get("releasenotes")
    digest = info.get("hash")
    if latest and is_newer(str(latest), VERSION):
        return {
            "status": "update_available",
            "version": latest,
            "notes": notes,
            "hash": digest,
            "source": "cdn",
        }
    return {"status": "no_update", "version": latest, "source": "cdn"}


def check_github_release() -> dict:
    """
    Authoritative GitHub channel (manual / audit). Does not drive auto-download.
    Returns same shape as check_release with source='github' and html_url.
    """
    try:
        info = http.get_json(GITHUB_API_LATEST, timeout=20)
    except http.HttpError as e:
        return {"status": "error", "error": str(e), "source": "github"}

    if not isinstance(info, dict):
        return {"status": "error", "error": "unexpected GitHub payload", "source": "github"}

    tag = info.get("tag_name") or info.get("name") or ""
    latest = str(tag).lstrip("vV")
    notes = info.get("body") or info.get("name")
    html_url = info.get("html_url") or GITHUB_LATEST_RELEASE_URL

    if latest and is_newer(latest, VERSION):
        return {
            "status": "update_available",
            "version": latest,
            "notes": notes,
            "hash": None,
            "html_url": html_url,
            "source": "github",
        }
    return {
        "status": "no_update",
        "version": latest or None,
        "html_url": html_url,
        "source": "github",
    }


def check_release_dual() -> dict:
    """
    Check CDN first (drives auto-update). If CDN has no update but GitHub is
    newer, still surface GitHub so users can choose the manual path.
    """
    cdn = check_release()
    if cdn.get("status") == "update_available":
        # Enrich with GitHub link when reachable (best-effort)
        gh = check_github_release()
        if gh.get("status") == "update_available":
            cdn["github_html_url"] = gh.get("html_url")
            # Prefer the newer of the two
            if is_newer(str(gh.get("version") or ""), str(cdn.get("version") or "")):
                cdn["version"] = gh["version"]
                cdn["notes"] = gh.get("notes") or cdn.get("notes")
                cdn["hash"] = None  # newer only on GitHub → no CDN hash
                cdn["github_only"] = True
                cdn["github_html_url"] = gh.get("html_url")
        return cdn

    if cdn.get("status") == "error":
        gh = check_github_release()
        if gh.get("status") == "update_available":
            gh["cdn_error"] = cdn.get("error")
            return gh
        return cdn

    # CDN says up-to-date; still check GitHub for newer tag
    gh = check_github_release()
    if gh.get("status") == "update_available":
        return gh
    return cdn


def internet_ok() -> bool:
    """Probe the real service host (not just bing.com)."""
    return http.host_reachable(RELEASE_JSON_URL, timeout=10) or http.host_reachable(
        BING_HOME, timeout=10
    )


def download_update(
    expected_hash: str | None,
    dest_dir: Path,
    on_error: Callable[[str], None] | None = None,
) -> Path | None:
    """Download new exe and verify hash. Returns path or None."""
    dest = dest_dir / "bing_new.exe"
    log.info("downloading update from %s", DOWNLOAD_URL)
    if not http.download_file(DOWNLOAD_URL, str(dest), timeout=60):
        msg = "download failed"
        log.error(msg)
        if on_error:
            on_error(msg)
        return None

    if expected_hash:
        actual = file_sha256(dest)
        if not actual or actual.lower() != expected_hash.lower():
            log.error("hash mismatch expected=%s actual=%s", expected_hash, actual)
            try:
                dest.unlink(missing_ok=True)
            except OSError:
                pass
            if on_error:
                on_error("hash mismatch; file discarded")
            return None
        log.info("update hash verified")

    return dest


def apply_windows_update(
    new_exe: Path,
    current_exe: Path,
) -> None:
    """
    Write a helper bat that replaces the running exe after exit.
    Paths are quoted; no shell=True on the Popen call.
    """
    bat = current_exe.parent / "updater.bat"
    content = f"""@echo off
echo Waiting for {APP_NAME} to close...
taskkill /F /IM "{current_exe.name}" > nul 2>&1
timeout /t 2 /nobreak > nul
echo Replacing old version...
del "{current_exe}" 2> nul
move /Y "{new_exe}" "{current_exe}"
echo Starting new version...
start "" "{current_exe}"
echo Cleaning up...
del "%~f0"
"""
    bat.write_text(content, encoding="utf-8")
    subprocess.Popen(
        ["cmd", "/c", str(bat)],
        creationflags=subprocess.CREATE_NO_WINDOW,
        cwd=str(current_exe.parent),
    )
    log.info("updater launched: %s", bat)
