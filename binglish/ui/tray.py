"""System tray menu construction and refresh.

Windows: in-process pystray + Tk mainloop.
macOS:   tray runs in a child process (AppKit); this process is Tk-only.
"""

from __future__ import annotations

import logging
import sys
import threading
import webbrowser
from functools import partial

from binglish.core import config as config_mod
from binglish.core.constants import PLAYPHRASE_URL
from binglish.core.paths import config_path, wallpaper_path
from binglish.core.state import state
from binglish.core.ui_thread import run_on_ui
from binglish.platform import get_platform
from binglish.services import music as music_svc
from binglish.services import wallpaper as wallpaper_svc
from binglish.ui import dialogs
from binglish.ui.overlays import open_history_from_menu

log = logging.getLogger(__name__)

_IS_MAC = sys.platform == "darwin"

# Set by app after services are ready
_wallpaper_job = None
_check_update = None

# macOS child-process control
_tray_proc = None
_tray_cmd_q = None
_tray_event_q = None
_tray_event_thread = None
_handlers: dict = {}


class MacTrayProxy:
    """Stand-in for pystray.Icon when the real icon lives in a child process."""

    def __init__(self, proc, cmd_q) -> None:
        self._proc = proc
        self._cmd_q = cmd_q
        self.visible = True

    def stop(self) -> None:
        self.visible = False
        try:
            self._cmd_q.put_nowait({"type": "quit"})
        except Exception:
            log.exception("mac tray quit enqueue failed")


def bind_jobs(*, wallpaper_job, check_update) -> None:
    global _wallpaper_job, _check_update
    _wallpaper_job = wallpaper_job
    _check_update = check_update
    _handlers.clear()
    _handlers.update(
        {
            "open_dict": _open_dictionary,
            "play_word": _play_word,
            "watch_clip": _watch_clip,
            "random_review": _random_review,
            "save_copy": _save_copy,
            "copyright": dialogs.show_copyright,
            "share_qr": dialogs.show_share_qr,
            "toggle_rest": _toggle_rest,
            "history": open_history_from_menu,
            "games": _open_games,
            "music": _toggle_music,
            "music_desc": dialogs.show_music_description,
            "toggle_startup": _toggle_startup,
            "github": _open_github_releases,
            "config": _open_config,
            "about": dialogs.show_about,
            "quit": _quit,
        }
    )
    if _check_update:
        _handlers["check_update"] = _check_update


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
            err = e
            log.error("word audio failed: %s", err)
            run_on_ui(dialogs.show_error, "播放失败", str(err))

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

    run_on_ui(open_games_overlay)


def _open_config() -> None:
    path = config_path()
    if not path.exists():
        config_mod.ensure_default_config()
    try:
        get_platform().open_path(str(path))
    except Exception as e:
        dialogs.show_error("错误", f"无法打开配置文件: {e}")


def _rest_label() -> str:
    if state.is_rest_enabled:
        mins = state.rest_remaining_seconds() // 60
        return f"提醒休息 (剩余{mins}分)"
    return "提醒休息"


def build_menu_spec() -> list[dict]:
    """Serializable menu model (used by the macOS tray child)."""
    items: list[dict] = []
    if state.dictionary_url and state.word:
        items.append({"key": "open_dict", "label": f"查单词 {state.word}"})
    if state.audio_url and state.word:
        items.append({"key": "play_word", "label": f"听单词 {state.word}"})
    if state.word:
        items.append({"key": "watch_clip", "label": f"看单词 {state.word}"})
    if state.dictionary_url or state.audio_url:
        items.append({"sep": True})

    items.append({"key": "random_review", "label": "随机复习"})
    if wallpaper_path().exists():
        items.append({"key": "save_copy", "label": "复制保存"})
    if state.copyright:
        items.append({"key": "copyright", "label": "壁纸信息"})
    if state.image_id:
        items.append({"key": "share_qr", "label": "分享壁纸"})

    items.append({"sep": True})
    items.append(
        {
            "key": "toggle_rest",
            "label": _rest_label(),
            "checked": bool(state.is_rest_enabled),
        }
    )

    items.append({"sep": True})
    items.append({"key": "history", "label": "Today in History"})
    items.append({"key": "games", "label": "Binglish Games"})
    if state.music_name and state.music_url:
        items.append(
            {
                "key": None,
                "label": "==Song of the Day==",
                "enabled": False,
            }
        )
        if state.music_desc:
            items.append(
                {"key": "music_desc", "label": f"  {state.music_name}"}
            )
        else:
            items.append(
                {
                    "key": None,
                    "label": f"  {state.music_name}",
                    "enabled": False,
                }
            )
        play_stop = "停止播放" if state.is_music_playing else "播放歌曲"
        items.append({"key": "music", "label": f"  {play_stop}"})
        items.append({"sep": True})

    startup_on = False
    try:
        startup_on = bool(get_platform().is_startup_enabled())
    except Exception:
        pass
    items.append(
        {
            "key": "toggle_startup",
            "label": "开机运行",
            "checked": startup_on,
        }
    )

    if getattr(sys, "frozen", False) and _check_update:
        label = "检查更新 (有新版本)" if state.new_version_available else "检查更新"
        items.append({"key": "check_update", "label": label})
        items.append({"key": "github", "label": "前往 GitHub Releases"})
    elif _check_update:
        items.append({"key": "github", "label": "前往 GitHub Releases"})

    items.append({"key": "config", "label": "设置"})
    items.append({"key": "about", "label": "关于"})
    items.append({"key": "quit", "label": "退出"})
    return items


def build_menu_items() -> tuple:
    """In-process pystray Menu (Windows)."""
    from pystray import Menu
    from pystray import MenuItem as item

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
    items.append(
        item(_rest_label(), _toggle_rest, checked=lambda _i: state.is_rest_enabled)
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


def _dispatch_mac_event(key: str) -> None:
    fn = _handlers.get(key)
    if fn is None:
        log.warning("no tray handler for key=%s", key)
        return
    try:
        fn()
    except Exception:
        log.exception("tray handler failed: %s", key)


def _start_mac_event_loop(event_q) -> None:
    global _tray_event_thread
    if _tray_event_thread is not None:
        return

    def loop() -> None:
        while True:
            try:
                msg = event_q.get(timeout=0.5)
            except Exception:
                if state.icon is not None and not getattr(state.icon, "visible", True):
                    break
                continue
            key = (msg or {}).get("key")
            if not key:
                continue
            # Handlers that touch Tk must run on the Tk main loop via the pump.
            run_on_ui(_dispatch_mac_event, key)

    _tray_event_thread = threading.Thread(target=loop, daemon=True, name="mac-tray-events")
    _tray_event_thread.start()


def _start_macos_tray_process(icon_path, title: str):
    global _tray_proc, _tray_cmd_q, _tray_event_q
    import multiprocessing

    from binglish.ui import tray_proc

    ctx = multiprocessing.get_context("spawn")
    _tray_cmd_q = ctx.Queue()
    _tray_event_q = ctx.Queue()
    spec = build_menu_spec()

    _tray_proc = ctx.Process(
        target=tray_proc.run_tray_process,
        args=(str(icon_path), title, spec, _tray_cmd_q, _tray_event_q),
        daemon=True,
        name="binglish-tray",
    )
    _tray_proc.start()
    log.info("macOS tray child started pid=%s", _tray_proc.pid)

    proxy = MacTrayProxy(_tray_proc, _tray_cmd_q)
    state.icon = proxy
    _start_mac_event_loop(_tray_event_q)
    return proxy


def refresh_menu() -> None:
    if state.icon is None:
        return

    if _IS_MAC:
        if _tray_cmd_q is None:
            return
        try:
            _tray_cmd_q.put({"type": "set_menu", "items": build_menu_spec()})
        except Exception:
            log.exception("mac menu refresh enqueue failed")
        return

    def _apply() -> None:
        from pystray import Menu

        icon = state.icon
        if icon is None:
            return
        try:
            icon.menu = Menu(*build_menu_items())
        except Exception as e:
            log.warning("menu refresh failed: %s", e)

    _apply()


def run_tray(icon_path, title: str = "Binglish桌面英语"):
    """Return a tray handle; caller runs it only on Windows."""
    if _IS_MAC:
        return _start_macos_tray_process(icon_path, title)

    from PIL import Image
    from pystray import Icon, Menu

    image = Image.open(icon_path)
    icon = Icon("Binglish", image, title, menu=Menu(*build_menu_items()))
    state.icon = icon
    return icon
