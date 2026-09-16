"""On This Day overlay."""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import messagebox

from binglish.core.state import state
from binglish.services import history as history_svc

log = logging.getLogger(__name__)


def open_history_overlay(events: list, date_str: str) -> None:
    if state.root is None:
        return
    if not state.try_acquire_overlay():
        return

    color = state.overlay_color
    overlay = tk.Toplevel(state.root)
    overlay.title("On This Day")
    w = state.root.winfo_screenwidth()
    h = state.root.winfo_screenheight()
    overlay.geometry(f"{w}x{h}+0+0")
    overlay.overrideredirect(True)
    overlay.attributes("-topmost", True, "-alpha", 0.0)
    overlay.configure(bg=color)

    main = tk.Frame(overlay, bg=color)
    main.pack(expand=True, fill="both", padx=50, pady=50)
    tk.Label(
        main,
        text=f"What Happened Today In History ({date_str})",
        font=("Helvetica", 36, "bold"),
        fg="white",
        bg=color,
    ).pack(pady=(20, 20))
    tk.Label(
        main,
        text="↓ Use mouse wheel to scroll / 使用滚轮查看更多 ↓",
        font=("Microsoft YaHei", 12),
        fg="#7F8C8D",
        bg=color,
    ).pack(pady=(0, 20))

    holder = tk.Frame(main, bg=color)
    holder.pack(expand=True, fill="both")
    canvas = tk.Canvas(holder, bg=color, highlightthickness=0)
    scrollable = tk.Frame(canvas, bg=color)
    scrollable.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )
    canvas.create_window((w // 2 - 50), 0, window=scrollable, anchor="n")
    canvas.pack(side="left", fill="both", expand=True)

    for event in events:
        frame = tk.Frame(scrollable, bg=color)
        frame.pack(fill="x", pady=15)
        year = event.get("year", "")
        tk.Label(
            frame,
            text=f"[{year}] {event.get('text_en', '')}",
            font=("Helvetica", 18),
            fg="white",
            bg=color,
            wraplength=w - 200,
            justify="left",
        ).pack(anchor="w")
        tk.Label(
            frame,
            text=event.get("text_cn", ""),
            font=("Microsoft YaHei", 16),
            fg="#95A5A6",
            bg=color,
            wraplength=w - 200,
            justify="left",
        ).pack(anchor="w", pady=(5, 0))

    def on_wheel(event) -> None:
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", on_wheel)

    close_f = tk.Frame(overlay, bg=color)
    close_f.pack(side="bottom", pady=40)

    def on_close(_event=None) -> None:
        canvas.unbind_all("<MouseWheel>")
        state.release_overlay()
        try:
            overlay.destroy()
        except tk.TclError:
            pass

    tk.Button(
        close_f,
        text="我知道了 (Close)",
        font=("Microsoft YaHei", 14),
        command=on_close,
        bg="white",
        fg=color,
        relief="flat",
        padx=30,
        pady=10,
        cursor="hand2",
    ).pack()
    overlay.bind("<Escape>", on_close)

    target = 0.95
    step = 20
    alpha_step = target / (1000 / step)

    def fade(current=0.0) -> None:
        if current < target:
            new = min(target, current + alpha_step)
            overlay.attributes("-alpha", new)
            overlay.after(step, fade, new)

    fade(0)
    overlay.focus_force()


def open_history_from_menu() -> None:
    """Background fetch then show on main thread."""
    if state.root is None:
        return

    def worker() -> None:
        events, date_str = history_svc.fetch_on_this_day()

        def apply() -> None:
            if events:
                open_history_overlay(events, date_str)
            else:
                messagebox.showinfo(
                    "On This Day",
                    "暂无相关历史内容。\nNo historical events found for today.",
                )

        state.root.after(0, apply)

    threading.Thread(target=worker, daemon=True).start()
