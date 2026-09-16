"""Shared application state — replaces module-level globals."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AppState:
    """Thread-safe snapshot of mutable app data."""

    lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    # Word / wallpaper metadata (from EXIF or sidecar)
    word: Optional[str] = None
    dictionary_url: Optional[str] = None
    audio_url: Optional[str] = None
    copyright: Optional[str] = None
    copyright_url: Optional[str] = None
    image_id: Optional[str] = None

    # Song of the day
    music_name: Optional[str] = None
    music_url: Optional[str] = None
    music_desc: Optional[str] = None
    is_music_playing: bool = False
    music_process: Any = None
    music_check_timer: Any = None

    # Rest reminder
    is_rest_enabled: bool = False
    rest_interval_seconds: int = 2700
    idle_reset_seconds: int = 300
    rest_lock_seconds: int = 30
    overlay_color: str = "#2C3E50"
    last_activity_time: float = field(default_factory=time.time)
    last_rest_time: float = field(default_factory=time.time)
    is_overlay_showing: bool = False

    # Updates
    new_version_available: bool = False

    # Runtime handles (set by app)
    icon: Any = None
    root: Any = None

    def snapshot_word_fields(self) -> dict:
        with self.lock:
            return {
                "word": self.word,
                "dictionary_url": self.dictionary_url,
                "audio_url": self.audio_url,
                "copyright": self.copyright,
                "copyright_url": self.copyright_url,
                "image_id": self.image_id,
            }

    def clear_word_fields(self) -> None:
        with self.lock:
            self.word = None
            self.dictionary_url = None
            self.audio_url = None
            self.copyright = None
            self.copyright_url = None
            self.image_id = None

    def set_word_fields(
        self,
        *,
        word: Optional[str] = None,
        dictionary_url: Optional[str] = None,
        audio_url: Optional[str] = None,
        copyright: Optional[str] = None,
        copyright_url: Optional[str] = None,
        image_id: Optional[str] = None,
    ) -> None:
        with self.lock:
            self.word = word
            self.dictionary_url = dictionary_url
            self.audio_url = audio_url
            self.copyright = copyright
            self.copyright_url = copyright_url
            self.image_id = image_id

    def clear_music_fields(self) -> None:
        with self.lock:
            self.music_name = None
            self.music_url = None
            self.music_desc = None

    def set_music_fields(
        self,
        name: Optional[str],
        url: Optional[str],
        description: Optional[str],
    ) -> None:
        with self.lock:
            if name and url:
                self.music_name = name
                self.music_url = url
                self.music_desc = description
            else:
                self.clear_music_fields()

    def try_acquire_overlay(self) -> bool:
        """Return True if this caller should open an overlay."""
        with self.lock:
            if self.is_overlay_showing:
                return False
            self.is_overlay_showing = True
            return True

    def release_overlay(self) -> None:
        with self.lock:
            self.is_overlay_showing = False

    def touch_rest(self) -> None:
        with self.lock:
            self.last_rest_time = time.time()

    def rest_remaining_seconds(self) -> int:
        with self.lock:
            elapsed = time.time() - self.last_rest_time
            return max(0, int(self.rest_interval_seconds - elapsed))


# Process-wide singleton used by the running app.
state = AppState()
