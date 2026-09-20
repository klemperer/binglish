"""Test Your Vocabulary."""

from __future__ import annotations

import threading
import tkinter as tk

from binglish.core.constants import COLOR_BG, COLOR_GOLD, COLOR_MUTED
from binglish.services import game_data as gd
from binglish.ui import theme

_WORD_OFF = "#34495E"
_WORD_ON = "#27AE60"
_WORD_TRAP = "#E74C3C"


def launch(parent: tk.Misc, game_data: dict, on_exit, on_started=None, on_game_end=None) -> None:
    container = tk.Frame(parent, bg=COLOR_BG)
    container.place(relx=0.5, rely=0.50, anchor="center")

    header = tk.Frame(container, bg=COLOR_BG)
    header.pack(fill="x", pady=(0, 10))
    tk.Label(
        header,
        text="Test Your Vocabulary",
        font=("Helvetica", 36, "bold"),
        fg=COLOR_GOLD,
        bg=COLOR_BG,
    ).pack(pady=(0, 5))
    tk.Label(
        header,
        text="请如实勾选您“确定认识”的单词。注意：内含不存在的钓鱼假词，错选将面临严厉扣分！",
        font=theme.ui_font(14),
        fg="#E74C3C",
        bg=COLOR_BG,
    ).pack(pady=(0, 15))

    action_f = tk.Frame(header, bg=COLOR_BG)
    action_f.pack()
    theme.make_button(
        action_f,
        text="退出测试 (Esc)",
        font=theme.ui_font(14),
        command=on_exit,
        bg="#E74C3C",
        fg="white",
        relief="flat",
        borderwidth=0,
        highlightthickness=0,
        padx=20,
        pady=5,
        cursor="hand2",
    ).pack(side="right", padx=10)

    result_msg = tk.Label(
        parent, text="", font=theme.ui_font(20, "bold"), bg=COLOR_BG
    )
    result_msg.place(relx=0.5, rely=0.12, anchor="center")

    grid_f = tk.Frame(container, bg=COLOR_BG)
    grid_f.pack(pady=10)
    loading_lbl = tk.Label(
        grid_f,
        text="正在从服务器获取测试词库，请稍候...",
        font=theme.ui_font(16),
        fg=COLOR_MUTED,
        bg=COLOR_BG,
    )
    loading_lbl.pack(pady=50)

    selected_vars: dict[str, tuple] = {}
    word_btns: dict[str, tk.Widget] = {}
    test_words: list[dict] = []
    game_active = True

    def _disable_btn(btn) -> None:
        try:
            btn.config(state="disabled")
        except tk.TclError:
            pass

    def submit_vocab() -> None:
        nonlocal game_active
        if not game_active:
            return
        selected = {w for w, (var, _) in selected_vars.items() if var.get()}
        result = gd.vocab_score(test_words, selected)
        for word, (var, w_info) in selected_vars.items():
            btn = word_btns.get(word)
            if btn is None:
                continue
            if w_info.get("is_trap") and var.get():
                btn.config(bg=_WORD_TRAP, fg="white")
            elif var.get():
                btn.config(bg=_WORD_ON, fg="white")
            else:
                btn.config(bg=_WORD_OFF, fg=COLOR_MUTED)
            _disable_btn(btn)

        color = "#2ECC71" if result["traps"] == 0 else "#E67E22"
        trap_msg = (
            f" (触发了 {result['traps']} 个假词惩罚，已被标红！)"
            if result["traps"]
            else " (火眼金睛，完美避开所有假词！)"
        )
        result_msg.config(
            text=(
                f"你的词汇量约为: {result['score']} 词\n"
                f"✨ {result['rank_title']} ✨\n{trap_msg}"
            ),
            fg=color,
        )
        game_active = False
        if on_game_end is not None:
            try:
                on_game_end()
            except Exception:
                pass

    def _toggle_word(word: str) -> None:
        if not game_active:
            return
        info = selected_vars.get(word)
        if not info:
            return
        var, _ = info
        var.set(not var.get())
        btn = word_btns.get(word)
        if btn is None:
            return
        if var.get():
            btn.config(bg=_WORD_ON, fg="white")
        else:
            btn.config(bg=_WORD_OFF, fg="white")

    submit_btn = theme.make_button(
        action_f,
        text="✔ 选好了，提交",
        font=theme.ui_font(14, "bold"),
        command=submit_vocab,
        bg="#2ECC71",
        fg="white",
        relief="flat",
        borderwidth=0,
        highlightthickness=0,
        padx=20,
        pady=5,
        cursor="hand2",
    )

    def render_vocab_grid(words: list) -> None:
        nonlocal test_words
        test_words = words or []
        loading_lbl.pack_forget()
        submit_btn.pack(side="left", padx=10)
        cols = 8
        word_btns.clear()
        for i, w_info in enumerate(test_words):
            word = w_info.get("word", "")
            var = tk.BooleanVar(value=False)
            selected_vars[word] = (var, w_info)
            # Toggle Buttons (not Checkbutton): Aqua checkbuttons are unreliable
            # for clicks when heavily restyled / inside fullscreen overlays.
            btn = theme.make_button(
                grid_f,
                text=word,
                font=("Helvetica", 13, "bold"),
                command=lambda w=word: _toggle_word(w),
                bg=_WORD_OFF,
                fg="white",
                activebackground="#1ABC9C",
                activeforeground="white",
                relief="flat",
                borderwidth=0,
                highlightthickness=0,
                cursor="hand2",
                width=12,
                padx=8,
                pady=6,
            )
            word_btns[word] = btn
            btn.grid(row=i // cols, column=i % cols, padx=6, pady=6)

    def load_vocab() -> None:
        words = gd.fetch_vocab_test()
        parent.after(
            0,
            lambda: render_vocab_grid(words)
            if words
            else loading_lbl.config(text="无法连接到服务器", fg="#E74C3C"),
        )

    threading.Thread(target=load_vocab, daemon=True).start()
