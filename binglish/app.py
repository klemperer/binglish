"""Application entry: wire services, platform, tray, and background jobs."""

from __future__ import annotations

import logging
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox

from binglish.core import config as config_mod
from binglish.core.constants import (
    DOWNLOAD_RETRY_INTERVAL_SECONDS,
    ICON_FILENAME,
    INTERNET_CHECK_INTERVAL_SECONDS,
    UPDATE_INTERVAL_SECONDS,
    VERSION,
)
from binglish.core.logging_setup import setup_logging
from binglish.core.paths import resource_path
from binglish.core.state import state
from binglish.core.ui_thread import run_on_ui
from binglish.platform import get_platform
from binglish.services import music as music_svc
from binglish.services import update as update_svc
from binglish.services import wallpaper as wallpaper_svc
from binglish.ui import tray

log = logging.getLogger(__name__)

_platform = None


def _platform_adapter():
    global _platform
    if _platform is None:
        _platform = get_platform()
    return _platform


def update_wallpaper_job(is_random: bool = False) -> bool:
    """Download wallpaper, extract meta, set desktop background."""
    # silent update probe
    threading.Thread(target=_silent_update_check, daemon=True).start()

    music_svc.stop_playback()
    state.clear_word_fields()
    state.clear_music_fields()
    music_svc.fetch_song_of_the_day()
    tray.refresh_menu()

    width, height = _platform_adapter().screen_size()
    if not wallpaper_svc.fetch_wallpaper(
        width=width, height=height, random_review=is_random
    ):
        return False

    from binglish.core.paths import wallpaper_path

    ok = _platform_adapter().set_wallpaper(str(wallpaper_path()))
    tray.refresh_menu()
    return ok


def _silent_update_check() -> None:
    time.sleep(2)
    result = update_svc.check_release_dual()
    if result.get("status") == "update_available":
        state.new_version_available = True
        log.info(
            "update available: %s (source=%s)",
            result.get("version"),
            result.get("source"),
        )
        tray.refresh_menu()


def run_scheduler() -> None:
    log.info("waiting for network...")
    while not update_svc.internet_ok():
        log.info("offline; retry in %ss", INTERNET_CHECK_INTERVAL_SECONDS)
        time.sleep(INTERNET_CHECK_INTERVAL_SECONDS)

    threading.Thread(target=_silent_update_check, daemon=True).start()

    while not update_wallpaper_job():
        if state.icon is not None and not state.icon.visible:
            log.info("user quit before first wallpaper")
            return
        log.info("wallpaper failed; retry in %ss", DOWNLOAD_RETRY_INTERVAL_SECONDS)
        time.sleep(DOWNLOAD_RETRY_INTERVAL_SECONDS)

    log.info("first wallpaper ok; interval=%ss", UPDATE_INTERVAL_SECONDS)
    while state.icon is None or state.icon.visible:
        time.sleep(UPDATE_INTERVAL_SECONDS)
        if state.icon is not None and not state.icon.visible:
            break
        if update_svc.internet_ok():
            update_wallpaper_job()
        else:
            log.info("offline; skip scheduled update")


def rest_monitor_loop() -> None:
    last_menu_refresh = time.time()
    while True:
        try:
            time.sleep(5)
            if state.is_rest_enabled and state.icon is not None:
                if time.time() - last_menu_refresh > 60:
                    tray.refresh_menu()
                    last_menu_refresh = time.time()

            if not state.is_rest_enabled:
                continue

            idle = _platform_adapter().get_idle_seconds()
            if idle > state.idle_reset_seconds:
                if time.time() - state.last_rest_time > 60:
                    log.info("idle %.1fs — reset rest timer", idle)
                state.touch_rest()
                if state.icon is not None:
                    tray.refresh_menu()
                continue

            elapsed = time.time() - state.last_rest_time
            if elapsed > state.rest_interval_seconds:
                if _platform_adapter().is_foreground_fullscreen():
                    log.info("fullscreen — defer rest reminder")
                elif not state.is_overlay_showing and state.root is not None:
                    log.info("trigger rest overlay")
                    run_on_ui(_open_rest)
        except Exception:
            log.exception("rest monitor error")
            time.sleep(10)


def _open_rest() -> None:
    from binglish.ui.overlays.rest import open_rest_overlay

    open_rest_overlay()


def _manual_update() -> None:
    """Background network check; all Tk dialogs on the main thread."""
    threading.Thread(target=_manual_update_worker, daemon=True).start()


def _manual_update_worker() -> None:
    result = update_svc.check_release_dual()
    run_on_ui(_manual_update_ui, result)


def _manual_update_ui(result: dict) -> None:
    """
    Dual-track update UI (must run on Tk main thread):
    - CDN (if hash present): one-click auto update
    - GitHub Releases: always offered as the audit / manual path
    """
    if result["status"] == "update_available":
        version = result.get("version")
        notes = result.get("notes") or "(无)"
        can_auto = bool(result.get("hash")) and not result.get("github_only")
        source = result.get("source", "cdn")
        gh_url = result.get("html_url") or result.get("github_html_url")

        lines = [
            f"有新版本 ({version}) 可用。",
            f"来源: {'CDN 快速通道' if source == 'cdn' and can_auto else 'GitHub Releases'}",
            "",
            f"更新说明:\n{notes}",
            "",
        ]
        if can_auto:
            lines.append("「是」= 从 CDN 自动更新并替换当前程序")
            lines.append("「否」= 打开 GitHub Releases，自行下载并校验哈希")
            if messagebox.askyesno("发现新版本", "\n".join(lines)):
                threading.Thread(
                    target=_do_download_update,
                    args=(result.get("hash"),),
                    daemon=True,
                ).start()
            else:
                _open_url(gh_url or update_svc.github_releases_url())
        else:
            lines.append("本次更新仅在 GitHub 提供（或 CDN 无哈希）。")
            lines.append("将打开 Releases 页面，请下载后核对 checksums.txt。")
            messagebox.showinfo("发现新版本", "\n".join(lines))
            _open_url(gh_url or update_svc.github_releases_url())
    elif result["status"] == "no_update":
        messagebox.showinfo(
            "没有更新",
            "您使用的已是最新版本。\n\n"
            "如需核对权威构建，可点菜单「前往 GitHub Releases」。",
        )
    else:
        err = result.get("error") or "未知错误"
        gh_fallback = update_svc.github_releases_url()
        if messagebox.askyesno(
            "检查更新失败",
            f"{err}\n\n是否改为打开 GitHub Releases 手动查看？",
        ):
            _open_url(gh_fallback)


def _open_url(url: str) -> None:
    import webbrowser

    try:
        webbrowser.open(url)
    except Exception as e:
        log.error("open url failed: %s", e)


def _do_download_update(expected_hash) -> None:
    from pathlib import Path

    from binglish.core import paths
    from binglish.core.ui_thread import run_on_ui

    new_exe = update_svc.download_update(
        expected_hash,
        paths.app_dir(),
        on_error=lambda msg: run_on_ui(messagebox.showerror, "更新失败", msg),
    )
    if new_exe is None:
        return
    if sys.platform.startswith("win"):
        update_svc.apply_windows_update(new_exe, Path(paths.executable_path()))
        run_on_ui(tray._quit)
    else:
        log.warning("auto-apply not implemented for this OS: %s", new_exe)


def main() -> None:
    # Pre-log setup for debug detection
    setup_logging(debug=config_mod.debug_enabled())
    config_mod.load_config_into_state()
    if config_mod.debug_enabled():
        setup_logging(debug=True)

    log.info("Binglish %s starting", VERSION)

    from binglish.core.single_instance import acquire_single_instance

    if not acquire_single_instance():
        log.warning("another instance is already running; exiting")
        # Best-effort user notice without creating a second tray icon
        # Use module-level tk/messagebox — do NOT import tk here (would shadow local name).
        try:
            r = tk.Tk()
            r.withdraw()
            messagebox.showinfo("Binglish", "程序已在运行，请查看系统托盘。")
            r.destroy()
        except Exception:
            pass
        return

    if sys.platform.startswith("win"):
        try:
            import ctypes

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    root = tk.Tk()
    root.withdraw()
    state.root = root
    if sys.platform == "darwin":
        # Prefer a real macOS CJK face for widgets that hardcode YaHei fallbacks.
        try:
            from binglish.ui.theme import CJK_FAMILY

            root.option_add("*Font", f"{{{CJK_FAMILY}}} 13")
        except Exception:
            pass
    from binglish.ui.ui_queue import start_pump

    start_pump(root)

    icon_path = resource_path(ICON_FILENAME)
    if not icon_path.exists():
        log.error("icon not found: %s", icon_path)
        sys.exit(1)

    tray.bind_jobs(
        wallpaper_job=update_wallpaper_job,
        check_update=_manual_update,
    )

    # Warm screen-size cache on the Tk main thread before workers start.
    try:
        adapter = _platform_adapter()
        warm = getattr(adapter, "warm_screen_size", None)
        if callable(warm):
            warm(root)
        else:
            adapter.screen_size()
    except Exception:
        log.exception("screen size warm-up failed")

    icon = tray.run_tray(icon_path)

    threading.Thread(target=run_scheduler, daemon=True).start()
    threading.Thread(target=rest_monitor_loop, daemon=True).start()

    log.info("running in tray; look for the icon near the clock")
    try:
        if sys.platform == "darwin":
            # Tray icon lives in a child process; this process is Tk-only.
            log.info("macOS: Tk mainloop in parent; tray in child process")
        else:
            threading.Thread(target=icon.run, daemon=True).start()
        root.mainloop()
    finally:
        from binglish.core.single_instance import release_single_instance

        release_single_instance()


if __name__ == "__main__":
    try:
        import multiprocessing

        multiprocessing.freeze_support()
    except Exception:
        pass
    main()
