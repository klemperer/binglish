"""Wallpaper download + metadata extraction."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import exifread

from binglish.core import paths
from binglish.core.constants import IMAGE_URL
from binglish.core.state import state
from binglish.services import http

log = logging.getLogger(__name__)


@dataclass
class WallpaperMeta:
    word: Optional[str] = None
    dictionary_url: Optional[str] = None
    audio_url: Optional[str] = None
    copyright: Optional[str] = None
    copyright_url: Optional[str] = None
    image_id: Optional[str] = None


def _parse_copyright(raw: str) -> tuple[Optional[str], Optional[str]]:
    if not raw:
        return None, None
    if "||" in raw:
        left, right = raw.split("||", 1)
        return left.strip() or None, right.strip() or None
    return raw.strip(), None


def extract_meta(image_path: str) -> WallpaperMeta:
    meta = WallpaperMeta()
    try:
        with open(image_path, "rb") as f:
            tags = exifread.process_file(f)
    except OSError as e:
        log.error("cannot read image for EXIF: %s", e)
        return meta

    if not tags:
        log.info("no EXIF tags in %s", image_path)
        return meta

    meta.word = str(tags.get("Image Artist", "")).strip() or None
    meta.dictionary_url = str(tags.get("Image ImageDescription", "")).strip() or None
    meta.audio_url = str(tags.get("Image DocumentName", "")).strip() or None
    meta.copyright, meta.copyright_url = _parse_copyright(
        str(tags.get("Image Copyright", "")).strip()
    )
    meta.image_id = str(tags.get("Image Software", "")).strip() or None
    return meta


def build_image_url(width: int, height: int, random_review: bool = False) -> str:
    url = f"{IMAGE_URL}&w={width}&h={height}"
    if random_review:
        url += "&random"
    return url


def fetch_wallpaper(
    *,
    width: int,
    height: int,
    random_review: bool = False,
) -> bool:
    """Download wallpaper and sync metadata into AppState. True on success."""
    dest = str(paths.wallpaper_path())
    url = build_image_url(width, height, random_review)
    log.info("downloading wallpaper: %s", url)

    if not http.download_file(url, dest):
        state.clear_word_fields()
        return False

    meta = extract_meta(dest)
    state.set_word_fields(
        word=meta.word,
        dictionary_url=meta.dictionary_url,
        audio_url=meta.audio_url,
        copyright=meta.copyright,
        copyright_url=meta.copyright_url,
        image_id=meta.image_id,
    )
    log.info(
        "wallpaper ready word=%s id=%s audio=%s",
        meta.word,
        meta.image_id,
        bool(meta.audio_url),
    )
    return True


def save_wallpaper_copy() -> str:
    """Copy current wallpaper to a timestamped file. Returns dest path."""
    import shutil
    from datetime import datetime

    src = paths.wallpaper_path()
    if not src.exists():
        raise FileNotFoundError(str(src))
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = paths.app_dir() / f"binglish_wallpaper_{stamp}.jpg"
    shutil.copy2(src, dest)
    return str(dest)
