"""On This Day overlay."""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import messagebox

from binglish.core.state import state
from binglish.core.ui_thread import run_on_ui
from binglish.services import history as history_svc
from binglish.ui import theme

log = logging.getLogger(__name__)


def open_history_overlay(events: list, date_str: str) -> None:
    if state.root is None:
        return
    if not state.try_acquire_overlay():
        return

    color = state.overlay_color
    overlay = theme.make_overlay(state.root, "On This Day", color=color, fade=True)
    w = state.root.winfo_screenwidth()

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
        font=theme.ui_font(12),
        fg="#7F8C8D",
        bg=color,
    ).pack(pady=(0, 20))

    holder = tk.Frame(main, bg=color)
    holder.pack(expand=True, fill="both")
    canvas = tk.Canvas(holder, bg=color, highlightthickness=0)
    scrollable = tk.Frame(canvas, bg=color)
    canvas.create_window((w // 2 - 50), 0, window=scrollable, anchor="n", tags="content")
    canvas.pack(side="left", fill="both", expand=True)

    def _sync_scrollregion(_e=None) -> None:
        try:
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Ensure window item fills canvas width for hit-testing / wheel.
            canvas.itemconfigure("content", width=max(canvas.winfo_width() - 2, 1))
        except tk.TclError:
            pass

    scrollable.bind("<Configure>", _sync_scrollregion)
    canvas.bind("<Configure>", _sync_scrollregion)

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
            font=theme.ui_font(16),
            fg="#95A5A6",
            bg=color,
            wraplength=w - 200,
            justify="left",
        ).pack(anchor="w", pady=(5, 0))

    def on_wheel(event) -> None:
        # Windows: delta is ±120 per notch.
        # macOS Tk Aqua: often ±1 (or small ints); Button-4/5 on some setups.
        if getattr(event, "num", None) == 4:
            canvas.yview_scroll(-1, "units")
            return
        if getattr(event, "num", None) == 5:
            canvas.yview_scroll(1, "units")
            return
        delta = getattr(event, "delta", 0) or 0
        if delta == 0:
            return
        units = (
            int(-1 * (delta / 120)) if abs(delta) >= 120 else (-1 if delta > 0 else 1)
        )
        if units:
            canvas.yview_scroll(units, "units")

    def _bind_wheel(widget) -> None:
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            try:
                widget.bind(seq, on_wheel)
            except tk.TclError:
                pass

    for w in (canvas, scrollable, holder, overlay, main):
        _bind_wheel(w)
    for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
        try:
            canvas.bind_all(seq, on_wheel)
        except tk.TclError:
            pass

    close_f = tk.Frame(overlay, bg=color)
    close_f.pack(side="bottom", pady=40)

    def on_close(_event=None) -> None:
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            try:
                canvas.unbind_all(seq)
            except tk.TclError:
                pass
        state.release_overlay()
        try:
            overlay.destroy()
        except tk.TclError:
            pass

    theme.make_button(
        close_f,
        text="我知道了 (Close)",
        font=theme.ui_font(14),
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
        if theme.IS_MAC:
            try:
                overlay.attributes("-alpha", target)
            except tk.TclError:
                pass
            return
        if current < target:
            new = min(target, current + alpha_step)
            overlay.attributes("-alpha", new)
            overlay.after(step, fade, new)

    fade(0)
    theme.focus_widget(overlay, delay_ms=50)


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

        run_on_ui(apply)

    threading.Thread(target=worker, daemon=True).start()
