"""macOS tray child process: pystray/AppKit only — never import Tk here."""

from __future__ import annotations

import logging
import queue
import sys

log = logging.getLogger(__name__)

# Keep PyObjC timer objects alive for the process lifetime.
_refs: list = []


def run_tray_process(
    icon_path: str,
    title: str,
    initial_items: list,
    cmd_q,
    event_q,
) -> None:
    """Entry point on the child main thread. Blocks until tray stops."""
    if sys.platform != "darwin":
        raise RuntimeError("tray child process is macOS-only")

    from PIL import Image
    from pystray import Icon, Menu
    from pystray import MenuItem as item

    def _handler_for(key: str | None):
        if not key:
            return None

        def _h(_icon, _item=None) -> None:
            try:
                event_q.put({"key": key})
            except Exception:
                log.exception("tray event put failed: %s", key)

        return _h

    def menu_from_spec(spec: list | None) -> Menu:
        rows = []
        for row in spec or []:
            if not row:
                continue
            if row.get("sep"):
                rows.append(Menu.SEPARATOR)
                continue
            checked = row.get("checked")
            # pystray requires None or a callable — not a bare bool.
            if checked is None:
                checked_arg = None
            else:
                checked_val = bool(checked)
                checked_arg = (lambda _item, _v=checked_val: _v)
            rows.append(
                item(
                    row.get("label") or "",
                    _handler_for(row.get("key")),
                    checked=checked_arg,
                    enabled=bool(row.get("enabled", True)),
                )
            )
        return Menu(*rows)

    def apply_cmd(cmd: dict) -> None:
        ctype = (cmd or {}).get("type")
        if ctype == "set_menu":
            icon.menu = menu_from_spec(cmd.get("items"))
        elif ctype == "quit":
            try:
                icon.stop()
            except Exception:
                log.exception("tray quit failed")
        elif ctype == "set_visible":
            try:
                icon.visible = bool(cmd.get("visible", True))
            except Exception:
                log.exception("tray set visible failed")

    def drain_cmds() -> None:
        while True:
            try:
                cmd = cmd_q.get_nowait()
            except queue.Empty:
                return
            except Exception:
                return
            try:
                apply_cmd(cmd)
            except Exception:
                log.exception("tray cmd failed: %s", cmd)

    image = Image.open(icon_path)
    icon = Icon("Binglish", image, title, menu=menu_from_spec(initial_items))

    # Install the CFRunLoop timer on THIS process main thread before NSApp.run.
    # pystray's setup callback runs on a worker thread — never touch AppKit there.
    try:
        from Foundation import NSObject, NSTimer

        class _CmdPump(NSObject):
            def tick_(self, _timer) -> None:
                try:
                    drain_cmds()
                except Exception:
                    log.exception("tray pump error")

        pump = _CmdPump.alloc().init()
        _refs.append(pump)
        _refs.append(
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.05,
                pump,
                pump.tick_,
                None,
                True,
            )
        )
        log.info("macOS tray child ready (pystray/AppKit only)")
    except Exception:
        log.exception("tray cmd pump install failed")

    def _setup(icon_obj) -> None:
        try:
            icon_obj.visible = True
        except Exception:
            log.exception("tray visible failed")

    icon.run(setup=_setup)
