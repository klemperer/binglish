"""Windows-specific OS integration."""

from __future__ import annotations

import ctypes
import logging
import os
import winreg
from ctypes import wintypes

from binglish.core.constants import APP_NAME, REG_KEY_PATH

log = logging.getLogger(__name__)

SPI_SETDESKWALLPAPER = 20


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]


class WindowsAdapter:
    def set_wallpaper(self, image_path: str) -> bool:
        try:
            abs_path = os.path.abspath(image_path)
            ok = ctypes.windll.user32.SystemParametersInfoW(
                SPI_SETDESKWALLPAPER, 0, abs_path, 3
            )
            log.info("wallpaper set ok=%s path=%s", bool(ok), abs_path)
            return bool(ok)
        except Exception as e:
            log.error("set wallpaper failed: %s", e)
            return False

    def get_idle_seconds(self) -> float:
        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            millis = ctypes.windll.kernel32.GetTickCount() - info.dwTime
            return millis / 1000.0
        return 0.0

    def is_foreground_fullscreen(self) -> bool:
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return False
            screen_w = user32.GetSystemMetrics(0)
            screen_h = user32.GetSystemMetrics(1)
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            if not (
                rect.left <= 0
                and rect.top <= 0
                and rect.right >= screen_w
                and rect.bottom >= screen_h
            ):
                return False
            buf = ctypes.create_unicode_buffer(255)
            user32.GetClassNameW(hwnd, buf, 255)
            if buf.value in ("Progman", "WorkerW", "Shell_TrayWnd"):
                return False
            return True
        except Exception:
            return False

    def is_startup_enabled(self) -> bool:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ
            ) as key:
                winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        except OSError as e:
            log.warning("startup check failed: %s", e)
            return False

    def set_startup(self, enabled: bool) -> bool:
        try:
            if enabled:
                from binglish.core import paths

                exe = paths.executable_path()
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE
                ) as key:
                    winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe}"')
                log.info("startup enabled")
            else:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE
                ) as key:
                    winreg.DeleteValue(key, APP_NAME)
                log.info("startup disabled")
            return True
        except OSError as e:
            log.error("toggle startup failed: %s", e)
            return False

    def screen_size(self) -> tuple[int, int]:
        try:
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
            dc = user32.GetDC(None)
            width = gdi32.GetDeviceCaps(dc, 8)
            height = gdi32.GetDeviceCaps(dc, 10)
            user32.ReleaseDC(None, dc)
            if width > 0 and height > 0:
                return int(width), int(height)
        except Exception as e:
            log.warning("screen size via GDI failed: %s", e)
        try:
            return int(user32.GetSystemMetrics(0)), int(ctypes.windll.user32.GetSystemMetrics(1))
        except Exception:
            return 1920, 1080

    def open_path(self, path: str) -> None:
        os.startfile(path)  # type: ignore[attr-defined]

    def beep(self, freq: int, duration_ms: int) -> None:
        try:
            ctypes.windll.kernel32.Beep(freq, duration_ms)
        except Exception:
            pass
