"""Rest reminder full-screen overlay."""

from __future__ import annotations

import logging
import random
import threading
import tkinter as tk

from binglish.core.quotes import REST_QUOTES
from binglish.core.state import state
from binglish.services import history as history_svc

log = logging.getLogger(__name__)

_WORD_HINTS = [
    "思考时间：你知道 {w} 的读音、含义和用法吗？",
    "考考你：{w} 这个词怎么读，是什么意思？",
    "趁休息回忆一下：{w} 通常在什么语境下使用？",
    "试着在脑海里造一个包含 {w} 的句子。",
    "不查字典，你能准确解释 {w} 的含义吗？",
    "闭上眼尝试拼写一下：{w}。",
    "小挑战：你能自信地大声读出 {w} 吗？",
    "灵魂拷问：你真的完全掌握 {w} 了吗？",
    "想想 {w} 可以在什么场景使用。",
    "别只顾着发呆，回顾一下 {w} 的中文意思。",
    "如果让你给别人讲解 {w}，你会怎么说？",
    "快速问答：{w} 是名词、动词还是形容词？",
    "今天的重点单词是 {w}，你记住了吗？",
    "记忆检查：{w} 有没有什么常见的同义词？",
    "{w} —— 看到它，你脑海里浮现出的第一个画面是什么？",
    "在休息结束前，请在心里把 {w} 默念三遍。",
    "假如现在英语考试，{w} 这道题你会做吗？",
    "嘿，放松眼睛的同时，别忘了复习一下：{w}。",
]


def open_rest_overlay() -> None:
    """Main thread only."""
    if state.root is None:
        return
    if not state.try_acquire_overlay():
        return

    color = state.overlay_color
    lock_seconds = state.rest_lock_seconds
    quote_en, quote_cn = random.choice(REST_QUOTES)

    overlay = tk.Toplevel(state.root)
    overlay.title("Time to Rest")
    w = state.root.winfo_screenwidth()
    h = state.root.winfo_screenheight()
    overlay.geometry(f"{w}x{h}+0+0")
    overlay.overrideredirect(True)
    overlay.attributes("-topmost", True, "-alpha", 0.0)
    overlay.configure(bg=color)

    container = tk.Frame(overlay, bg=color)
    container.pack(expand=True, fill="both")

    bottom = tk.Frame(container, bg=color)
    bottom.pack(side="bottom", fill="x", pady=(0, 60), padx=50)
    lbl_fact_en = tk.Label(
        bottom,
        text="",
        font=("Helvetica", 14, "italic"),
        fg="#BDC3C7",
        bg=color,
        wraplength=w - 200,
    )
    lbl_fact_en.pack(side="top", pady=(0, 5))
    lbl_fact_cn = tk.Label(
        bottom,
        text="正在获取冷知识...",
        font=("Microsoft YaHei", 12),
        fg="#7F8C8D",
        bg=color,
        wraplength=w - 200,
    )
    lbl_fact_cn.pack(side="top")

    center = tk.Frame(container, bg=color)
    center.place(relx=0.5, rely=0.45, anchor="center")
    tk.Label(
        center,
        text=quote_en,
        font=("Helvetica", 32, "bold"),
        fg="white",
        bg=color,
        wraplength=w - 100,
    ).pack(pady=(0, 20))
    tk.Label(
        center,
        text=quote_cn,
        font=("Microsoft YaHei", 24),
        fg="#BDC3C7",
        bg=color,
        wraplength=w - 100,
    ).pack(pady=(0, 40))

    word = state.word
    lbl_word = None
    if word:
        hint = random.choice(_WORD_HINTS).format(w=word)
        lbl_word = tk.Label(
            center,
            text=hint,
            font=("Microsoft YaHei", 18, "bold"),
            fg="#A9DFBF",
            bg=color,
            wraplength=w - 100,
        )

    remaining = [lock_seconds]
    btn_text = tk.StringVar(value=f"我休息好了 ({remaining[0]}s)")

    def on_close(_event=None) -> None:
        state.release_overlay()
        state.touch_rest()
        try:
            overlay.destroy()
        except tk.TclError:
            pass
        from binglish.ui import tray

        tray.refresh_menu()

    btn = tk.Button(
        center,
        textvariable=btn_text,
        font=("Microsoft YaHei", 14),
        command=on_close,
        state="disabled",
        bg="#ECF0F1",
        fg=color,
        relief="flat",
        padx=30,
        pady=10,
    )
    btn.pack()

    def fetch_fact() -> None:
        en, cn = history_svc.fetch_useless_fact()

        def apply() -> None:
            if not state.is_overlay_showing:
                return
            if en and cn:
                lbl_fact_en.config(text=f"Did you know? {en}")
                lbl_fact_cn.config(text=cn)
            else:
                lbl_fact_cn.config(text="")

        overlay.after(0, apply)

    threading.Thread(target=fetch_fact, daemon=True).start()

    target_alpha = 0.95
    step = 20
    alpha_step = target_alpha / (1000 / step)

    def start_countdown() -> None:
        show_at = lock_seconds // 2
        if remaining[0] == show_at and lbl_word:
            lbl_word.pack(pady=(0, 40), before=btn)
        if remaining[0] > 0:
            remaining[0] -= 1
            btn_text.set(f"我休息好了 ({remaining[0]}s)")
            overlay.after(1000, start_countdown)
        else:
            btn_text.set("我休息好了")
            btn.config(state="normal", bg="white", cursor="hand2")
            overlay.bind("<Return>", on_close)
            overlay.focus_force()

    def fade_in(current=0.0) -> None:
        if current < target_alpha:
            new = min(target_alpha, current + alpha_step)
            overlay.attributes("-alpha", new)
            overlay.after(step, fade_in, new)
        else:
            start_countdown()

    fade_in(0)
    overlay.focus_force()
