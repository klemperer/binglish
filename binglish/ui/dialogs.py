"""Dialog windows (about / copyright / share QR / music)."""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox

import qrcode
from PIL import ImageTk

from binglish.core.constants import (
    PROJECT_URL,
    SHARE_URL_TEMPLATE,
    VERSION,
)
from binglish.core.state import state
from binglish.core.ui_thread import run_on_ui
from binglish.ui import theme

log = logging.getLogger(__name__)


def show_about() -> None:
    run_on_ui(_show_about)


def _show_about() -> None:
    messagebox.showinfo(
        "关于 Binglish",
        f"Binglish桌面英语 {VERSION}\n{PROJECT_URL}",
    )


def show_copyright() -> None:
    run_on_ui(_show_copyright)


def _show_copyright() -> None:
    with state.lock:
        text = state.copyright
        url = state.copyright_url
    if text and url:
        if messagebox.askyesno("图片信息", f"{text}\n\n查看相关信息？"):
            import webbrowser

            webbrowser.open(url)
    elif text:
        messagebox.showinfo("图片信息", text)
    else:
        messagebox.showinfo("图片信息", "暂无图片版权信息。")


def show_music_description() -> None:
    run_on_ui(_show_music_description)


def _show_music_description() -> None:
    with state.lock:
        name = state.music_name
        desc = state.music_desc
    if not desc:
        messagebox.showinfo(f"歌曲: {name or ''}", "没有可用的歌曲描述。")
        return
    win = tk.Toplevel(state.root)
    win.title(f"歌曲: {name}")
    win.resizable(False, False)
    win.attributes("-topmost", True)
    tk.Message(
        win,
        text=desc,
        width=600,
        justify="left",
        font=theme.ui_font(15),
    ).pack(padx=10, pady=(10, 5))
    theme.make_button(win, text="关闭", command=win.destroy).pack(pady=(5, 10))


def show_share_qr() -> None:
    run_on_ui(_show_share_qr)


def _show_share_qr() -> None:
    with state.lock:
        image_id = state.image_id
    if not image_id:
        messagebox.showerror("错误", "未找到图片ID，无法分享。")
        return
    share_url = SHARE_URL_TEMPLATE.format(image_id=image_id)
    try:
        win = tk.Toplevel(state.root)
        win.title("分享此壁纸")
        win.resizable(False, False)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(share_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        win.tk_image = ImageTk.PhotoImage(img)  # keep ref
        tk.Label(win, image=win.tk_image).pack(padx=10, pady=10)
        tk.Label(win, text="请使用手机扫一扫以分享").pack(pady=5)
        win.update_idletasks()
        x = state.root.winfo_screenwidth() // 2 - win.winfo_width() // 2
        y = state.root.winfo_screenheight() // 2 - win.winfo_height() // 2
        win.geometry(f"+{x}+{y}")
        win.focus_set()
    except Exception as e:
        log.exception("QR failed")
        messagebox.showerror("二维码错误", str(e))


def show_error(title: str, message: str) -> None:
    run_on_ui(messagebox.showerror, title, message)


def show_info(title: str, message: str) -> None:
    run_on_ui(messagebox.showinfo, title, message)
