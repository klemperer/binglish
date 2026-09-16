"""System tray menu construction and refresh."""

from __future__ import annotations

import logging
import sys
import threading
import webbrowser
from functools import partial

from pystray import Menu, MenuItem as item

from binglish.core import config as config_mod
from binglish.core.constants import PLAYPHRASE_URL, PROJECT_URL
from binglish.core.paths import config_path, wallpaper_path
from binglish.core.state import state
from binglish.platform import get_platform
from binglish.services import music as music_svc
from binglish.services import wallpaper as wallpaper_svc
from binglish.ui import dialogs
from binglish.ui.overlays import open_history_from_menu, open_rest_overlay

log = logging.getLogger(__name__)

# Set by app after services are ready
_wallpaper_job = None
_check_update = None


def bind_jobs(*, wallpaper_job, check_update) -> None:
    global _wallpaper_job, _check_update
    _wallpaper_job = wallpaper_job
    _check_update = check_update


def _open_dictionary() -> None:
    if state.dictionary_url:
        webbrowser.open(state.dictionary_url)


def _watch_clip() -> None:
    if state.word:
        webbrowser.open(PLAYPHRASE_URL.format(word=state.word))


def _play_word() -> None:
    if not state.audio_url:
        return

    def worker() -> None:
        try:
            from playsound3 import playsound

            playsound(state.audio_url)
        except Exception as e:
            log.error("word audio failed: %s", e)
            if state.root:
                state.root.after(
                    0, lambda: dialogs.show_error("播放失败", str(e))
                )

    threading.Thread(target=worker, daemon=True).start()


def _random_review() -> None:
    if _wallpaper_job:
        threading.Thread(
            target=partial(_wallpaper_job, True), daemon=True
        ).start()


def _save_copy() -> None:
    try:
        dest = wallpaper_svc.save_wallpaper_copy()
        dialogs.show_info("已保存", f"壁纸已复制到:\n{dest}")
    except FileNotFoundError:
        dialogs.show_error("错误", "当前没有可保存的壁纸。")
    except OSError as e:
        dialogs.show_error("错误", str(e))


def _toggle_rest() -> None:
    with state.lock:
        state.is_rest_enabled = not state.is_rest_enabled
        enabled = state.is_rest_enabled
        if enabled:
            state.last_rest_time = __import__("time").time()
    config_mod.save_rest_enabled(enabled)
    log.info("rest reminder %s", "enabled" if enabled else "disabled")
    refresh_menu()


def _toggle_startup() -> None:
    platform = get_platform()
    current = platform.is_startup_enabled()
    ok = platform.set_startup(not current)
    if not ok:
        dialogs.show_error("错误", "修改开机启动失败。")
    refresh_menu()


def _toggle_music() -> None:
    if state.is_music_playing:
        music_svc.stop_playback()
    else:
        if not music_svc.start_playback():
            dialogs.show_info("提示", "当前没有可播放的歌曲。")
    refresh_menu()
    if state.is_music_playing and state.root is not None:
        _schedule_music_poll()


def _schedule_music_poll() -> None:
    def poll() -> None:
        with state.lock:
            proc = state.music_process
            playing = state.is_music_playing
        if playing and proc is not None and not proc.is_alive():
            with state.lock:
                state.is_music_playing = False
                state.music_process = None
            refresh_menu()
            return
        if playing and state.root is not None:
            state.music_check_timer = state.root.after(1000, poll)

    if state.root is not None:
        state.music_check_timer = state.root.after(1000, poll)


def _open_games() -> None:
    from binglish.games.host import open_games_overlay

    if state.root is not None:
        state.root.after(0, open_games_overlay)
    else:
        open_games_overlay()


def _open_config() -> None:
    path = config_path()
    if not path.exists():
        config_mod.ensure_default_config()
    try:
        get_platform().open_path(str(path))
    except Exception as e:
        dialogs.show_error("错误", f"无法打开配置文件: {e}")


def build_menu_items() -> tuple:
    items = []
    if state.dictionary_url and state.word:
        items.append(item(f"查单词 {state.word}", _open_dictionary))
    if state.audio_url and state.word:
        items.append(item(f"听单词 {state.word}", _play_word))
    if state.word:
        items.append(item(f"看单词 {state.word}", _watch_clip))
    if state.dictionary_url or state.audio_url:
        items.append(Menu.SEPARATOR)

    items.append(item("随机复习", _random_review))
    if wallpaper_path().exists():
        items.append(item("复制保存", _save_copy))
    if state.copyright:
        items.append(item("壁纸信息", dialogs.show_copyright))
    if state.image_id:
        items.append(item("分享壁纸", dialogs.show_share_qr))

    items.append(Menu.SEPARATOR)
    if state.is_rest_enabled:
        mins = state.rest_remaining_seconds() // 60
        rest_label = f"提醒休息 (剩余{mins}分)"
    else:
        rest_label = "提醒休息"
    items.append(
        item(rest_label, _toggle_rest, checked=lambda _i: state.is_rest_enabled)
    )

    items.append(Menu.SEPARATOR)
    items.append(item("Today in History", open_history_from_menu))
    items.append(item("Binglish Games", _open_games))
    if state.music_name and state.music_url:
        items.append(item("==Song of the Day==", None, enabled=False))
        if state.music_desc:
            items.append(
                item(f"  {state.music_name}", dialogs.show_music_description)
            )
        else:
            items.append(item(f"  {state.music_name}", None, enabled=False))
        play_stop = "停止播放" if state.is_music_playing else "播放歌曲"
        items.append(item(f"  {play_stop}", _toggle_music))
        items.append(Menu.SEPARATOR)

    items.append(
        item(
            "开机运行",
            _toggle_startup,
            checked=lambda _i: get_platform().is_startup_enabled(),
        )
    )

    if getattr(sys, "frozen", False) and _check_update:
        label = "检查更新 (有新版本)" if state.new_version_available else "检查更新"
        items.append(item(label, _check_update))
        items.append(item("前往 GitHub Releases", _open_github_releases))
    elif _check_update:
        # Dev/source run: still offer the audit path
        items.append(item("前往 GitHub Releases", _open_github_releases))

    items.append(item("设置", _open_config))
    items.append(item("关于", dialogs.show_about))
    items.append(item("退出", _quit))
    return tuple(items)


def _open_github_releases() -> None:
    """Open the authoritative GitHub Releases page for manual download/verify."""
    from binglish.core.constants import GITHUB_LATEST_RELEASE_URL
    from binglish.services.update import github_releases_url

    try:
        url = github_releases_url() or GITHUB_LATEST_RELEASE_URL
    except Exception:
        url = GITHUB_LATEST_RELEASE_URL
    webbrowser.open(url)
    log.info("opened GitHub Releases: %s", url)


def _quit() -> None:
    music_svc.stop_playback()
    if state.icon is not None:
        state.icon.stop()
    if state.root is not None:
        try:
            state.root.destroy()
        except Exception:
            pass


def refresh_menu() -> None:
    if state.icon is None:
        return
    try:
        state.icon.menu = Menu(*build_menu_items())
    except Exception as e:
        log.warning("menu refresh failed: %s", e)


def run_tray(icon_image, title: str = "Binglish桌面英语"):
    """Create and return a pystray Icon (caller runs it)."""
    from pystray import Icon

    icon = Icon("Binglish", icon_image, title, menu=Menu(*build_menu_items()))
    state.icon = icon
    return icon
