"""Cross-platform Tk styling (fonts + buttons that honor colors on macOS)."""

from __future__ import annotations

import logging
import sys
import tkinter as tk

log = logging.getLogger(__name__)

IS_MAC = sys.platform == "darwin"

# Not accepted by some Windows Tk builds — strip before tk.Button().
_TK_BUTTON_UNSUPPORTED = frozenset({"activeborderwidth"})

# Windows ships Microsoft YaHei; macOS uses PingFang SC.
CJK_FAMILY = "PingFang SC" if IS_MAC else "Microsoft YaHei"

_WIN_CJK = "Microsoft YaHei"
_MAC_CJK = "PingFang SC"


def fix_font(font):
    """Rewrite Windows CJK font tuples for macOS."""
    if not IS_MAC or not font:
        return font
    if isinstance(font, (tuple, list)) and font and font[0] == _WIN_CJK:
        return (_MAC_CJK, *font[1:])
    return font


def ui_font(size: int, *style: str):
    """Portable CJK UI font: (family, size[, weight...])."""
    return (CJK_FAMILY, size, *style)


def _sanitize_button_cnf(cnf: dict) -> dict:
    return {k: v for k, v in cnf.items() if k not in _TK_BUTTON_UNSUPPORTED}


# tkmacosx paints wrong/ignores colors on some builds and crashes on destroy
# (_main_win). macOS colored controls use a Label-based button instead.
_COLOR_BTN_SKIP = frozenset(
    {
        "mac_native",
        "relief",
        "borderwidth",
        "bd",
        "highlightthickness",
        "highlightbackground",
        "highlightcolor",
        "activebackground",
        "activeforeground",
        "activeborderwidth",
        "overrelief",
        "background",
        "foreground",
        "height",
    }
) | _TK_BUTTON_UNSUPPORTED


class ColorButton:
    """Label-as-button with reliable bg/fg on macOS Aqua (and harmless on win)."""

    def __init__(self, master, **kwargs) -> None:
        self._command = kwargs.pop("command", None)
        state = kwargs.pop("state", "normal")
        self._enabled = state != "disabled"
        textvariable = kwargs.pop("textvariable", None)
        text = kwargs.pop("text", "")
        bg = kwargs.pop("bg", None) or kwargs.pop("background", "#34495E")
        fg = kwargs.pop("fg", None) or kwargs.pop("foreground", "white")
        font = fix_font(kwargs.pop("font", None))
        padx = kwargs.pop("padx", 8)
        pady = kwargs.pop("pady", 4)
        cursor = kwargs.pop("cursor", "hand2")
        width = kwargs.pop("width", None)
        # Drop leftovers that Labels do not accept / that Aqua ignores.
        for key in list(kwargs):
            if key in _COLOR_BTN_SKIP:
                kwargs.pop(key)

        label_kw = {
            "master": master,
            "bg": bg,
            "fg": fg,
            "padx": padx,
            "pady": pady,
            "cursor": cursor if self._enabled else "arrow",
        }
        if font is not None:
            label_kw["font"] = font
        if textvariable is not None:
            label_kw["textvariable"] = textvariable
        else:
            label_kw["text"] = text
        if isinstance(width, int) and not IS_MAC:
            # Tk Label width is characters; only meaningful when caller used chars.
            label_kw["width"] = width
        elif isinstance(width, int) and IS_MAC:
            # Callers may still pass char-like widths; Labels honor chars too.
            label_kw["width"] = width
        self._widget = tk.Label(**label_kw)
        self._widget.bind("<Button-1>", self._on_click)

    @property
    def _bg(self) -> str:
        try:
            return str(self._widget.cget("bg"))
        except tk.TclError:
            return "#34495E"

    @property
    def _fg(self) -> str:
        try:
            return str(self._widget.cget("fg"))
        except tk.TclError:
            return "white"

    def _on_click(self, _event=None) -> None:
        if self._enabled and self._command is not None:
            self._command()

    def pack(self, **kw):
        self._widget.pack(**kw)
        return self

    def pack_forget(self) -> None:
        try:
            self._widget.pack_forget()
        except tk.TclError:
            pass

    def grid(self, **kw):
        self._widget.grid(**kw)
        return self

    def place(self, **kw):
        self._widget.place(**kw)
        return self

    def config(self, **kw) -> None:
        self.configure(**kw)

    def configure(self, **kw) -> None:
        kw = dict(kw)
        if "command" in kw:
            self._command = kw.pop("command")
        if "state" in kw:
            st = kw.pop("state")
            self._enabled = st != "disabled"
            kw["cursor"] = "hand2" if self._enabled else "arrow"
        for key in list(kw):
            if key in _COLOR_BTN_SKIP:
                kw.pop(key)
        if "font" in kw:
            kw["font"] = fix_font(kw["font"])
        if kw:
            try:
                self._widget.config(**kw)
            except tk.TclError:
                log.debug("ColorButton.config ignored: %s", kw)

    def destroy(self) -> None:
        try:
            self._widget.destroy()
        except tk.TclError:
            pass

    def bind(self, *args, **kwargs) -> None:
        self._widget.bind(*args, **kwargs)

    def lift(self, *args) -> None:
        try:
            self._widget.lift(*args)
        except tk.TclError:
            pass

    def winfo_exists(self) -> bool:
        try:
            return bool(self._widget.winfo_exists())
        except tk.TclError:
            return False

    def cget(self, key: str):
        return self._widget.cget(key)


def make_button(parent, **kwargs):
    """Cross-platform button.

    Windows: real tk.Button (unchanged behavior).
    macOS: ColorButton (Label) so bg/fg always apply; avoids tkmacosx
    color/destroy bugs. Aqua tk.Button ignores custom colors anyway.
    """
    kwargs = dict(kwargs)
    kwargs.pop("mac_native", None)
    font = kwargs.get("font")
    if font is not None:
        kwargs["font"] = fix_font(font)

    bg = kwargs.get("bg") or kwargs.get("background")
    fg = kwargs.get("fg") or kwargs.get("foreground")

    if IS_MAC:
        # Interactive colored control → ColorButton.
        if bg is not None or kwargs.get("command") is not None:
            cb_kwargs = {
                "text": kwargs.get("text", ""),
                "command": kwargs.get("command"),
                "bg": bg or "#34495E",
                "fg": fg or "white",
                "font": kwargs.get("font"),
                "padx": kwargs.get("padx", 8),
                "pady": kwargs.get("pady", 4),
                "cursor": kwargs.get("cursor", "hand2"),
                "state": kwargs.get("state", "normal"),
            }
            if "textvariable" in kwargs:
                cb_kwargs["textvariable"] = kwargs["textvariable"]
            if isinstance(kwargs.get("width"), int):
                cb_kwargs["width"] = kwargs["width"]
            return ColorButton(parent, **cb_kwargs)
        return tk.Button(parent, **_sanitize_button_cnf(kwargs))

    if bg:
        if "borderwidth" in kwargs or kwargs.get("relief") == "flat":
            kwargs.setdefault("highlightthickness", 0)
    return tk.Button(parent, **_sanitize_button_cnf(kwargs))


def make_checkbutton(parent, **kwargs):
    """Checkbutton with stable colors on macOS when bg/fg are set."""
    kwargs = dict(kwargs)
    font = kwargs.get("font")
    if font is not None:
        kwargs["font"] = fix_font(font)

    if IS_MAC:
        bg = kwargs.get("bg") or kwargs.get("background")
        if bg:
            kwargs.setdefault("activebackground", bg)
            kwargs.setdefault("highlightthickness", 0)
            kwargs.setdefault("highlightbackground", bg)
            kwargs.setdefault("relief", "flat")
            if "selectcolor" not in kwargs and kwargs.get("fg"):
                # Keep the on-state readable if selectcolor is omitted.
                kwargs["selectcolor"] = kwargs.get("fg")
        fg = kwargs.get("fg")
        if fg:
            kwargs.setdefault("activeforeground", fg)

    return tk.Checkbutton(parent, **kwargs)


def make_label(parent, **kwargs):
    """Label with macOS CJK font mapping (colors already work on Labels)."""
    kwargs = dict(kwargs)
    font = kwargs.get("font")
    if font is not None:
        kwargs["font"] = fix_font(font)
    return tk.Label(parent, **kwargs)


def make_overlay(root, title: str, *, color: str | None = None, fade: bool = True):
    """
    Fullscreen overlay that can take keyboard focus on macOS.

    Aqua will not deliver <Key> events to overrideredirect windows, so on
    macOS we use a real fullscreen Toplevel instead of a borderless one.
    """
    overlay = tk.Toplevel(root)
    overlay.title(title)
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()
    overlay.geometry(f"{w}x{h}+0+0")
    if IS_MAC:
        try:
            overlay.overrideredirect(False)
        except tk.TclError:
            pass
        try:
            overlay.attributes("-fullscreen", True)
        except tk.TclError:
            pass
        overlay.attributes("-topmost", True)
        # Fullscreen + alpha is flaky on macOS Tk; stay opaque.
        fade = False
    else:
        overlay.overrideredirect(True)
        if fade:
            overlay.attributes("-topmost", True, "-alpha", 0.0)
        else:
            overlay.attributes("-topmost", True)
    if color:
        overlay.configure(bg=color)
    return overlay


def bind_keys(widget, handler) -> None:
    """Bind <Key> on the widget and its toplevel (macOS focus is picky)."""
    try:
        widget.bind("<Key>", handler)
    except tk.TclError:
        pass
    try:
        widget.winfo_toplevel().bind("<Key>", handler)
    except tk.TclError:
        pass


def focus_widget(widget, delay_ms: int = 30) -> None:
    """Lift the toplevel and give the widget keyboard focus."""
    def _do() -> None:
        try:
            top = widget.winfo_toplevel()
            top.lift()
            top.focus_force()
            widget.focus_set()
        except tk.TclError:
            pass

    if delay_ms <= 0:
        _do()
        return
    try:
        widget.after(delay_ms, _do)
    except tk.TclError:
        _do()
