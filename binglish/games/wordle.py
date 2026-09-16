"""Binglish Wordle."""

from __future__ import annotations

import logging
import threading
import tkinter as tk

from binglish.core.constants import COLOR_BG, COLOR_GOLD, COLOR_MUTED
from binglish.games.share import copy_text, wordle_share_text
from binglish.games.sounds import play_game_sound
from binglish.services import game_data as gd

log = logging.getLogger(__name__)

_COLOR_MAP = {
    "green": "#2ECC71",
    "yellow": "#F1C40F",
    "gray": "#7F8C8D",
}


def launch(parent: tk.Misc, game_data: dict, on_exit) -> None:
    payload = game_data.get("wordle") or {}
    target = (payload.get("word") or "").lower()
    desc = payload.get("desc") or ""
    if not target:
        tk.Label(
            parent,
            text="Wordle data unavailable",
            font=("Microsoft YaHei", 16),
            fg="#E74C3C",
            bg=COLOR_BG,
        ).pack(pady=40)
        return

    t_len = len(target)
    guesses: list[str] = []
    color_rows: list[list[str]] = []
    cur_guess: list[str] = []
    game_active = True
    # Serialize submit: prevent double-Enter and edits while verifying
    submitting = False
    share_btn = {"widget": None}

    rule_f = tk.Frame(parent, bg=COLOR_BG, width=320)
    rule_f.place(relx=0.05, rely=0.5, anchor="w")
    tk.Label(
        rule_f,
        text="Binglish Wordle",
        font=("Helvetica", 24, "bold"),
        fg=COLOR_GOLD,
        bg=COLOR_BG,
        justify="left",
    ).pack(anchor="w", pady=10)
    tk.Label(
        rule_f,
        text="规则：\n1. 目标：6次机会猜出单词\n2. 绿色：字母存在且位置正确\n3. 黄色：字母存在但位置错\n4. 灰色：字母不在答案中",
        font=("Microsoft YaHei", 12),
        fg=COLOR_MUTED,
        bg=COLOR_BG,
        justify="left",
    ).pack(anchor="w")

    container = tk.Frame(parent, bg=COLOR_BG)
    container.place(relx=0.5, rely=0.55, anchor="center")

    result_msg = tk.Label(
        parent, text="", font=("Microsoft YaHei", 24, "bold"), bg=COLOR_BG
    )
    result_msg.place(relx=0.5, rely=0.1, anchor="center")
    rank_lbl = tk.Label(
        parent, text="", font=("Microsoft YaHei", 24, "bold"), fg=COLOR_GOLD, bg=COLOR_BG
    )

    grid_f = tk.Frame(container, bg=COLOR_BG)
    grid_f.pack(pady=5)
    cells: list[list[tk.Label]] = []
    for r in range(6):
        row = []
        for c in range(t_len):
            lbl = tk.Label(
                grid_f,
                text="",
                font=("Helvetica", 30, "bold"),
                width=2,
                height=1,
                fg="white",
                bg="#34495E",
                highlightbackground=COLOR_MUTED,
                highlightthickness=2,
            )
            lbl.grid(row=r, column=c, padx=4, pady=4)
            row.append(lbl)
        cells.append(row)

    kb_f = tk.Frame(container, bg=COLOR_BG)
    kb_f.pack(pady=10)
    kb_map: dict[str, tk.Label] = {}
    for row_chars in ("QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"):
        rf = tk.Frame(kb_f, bg=COLOR_BG)
        rf.pack()
        for ch in row_chars:
            key = tk.Label(
                rf,
                text=ch,
                font=("Helvetica", 12, "bold"),
                width=3,
                height=1,
                fg="white",
                bg="#5D6D7E",
                padx=5,
                pady=5,
            )
            key.pack(side="left", padx=2, pady=2)
            kb_map[ch.lower()] = key

    def_lbl = tk.Label(
        container,
        text="",
        font=("Microsoft YaHei", 14),
        fg="#A9DFBF",
        bg=COLOR_BG,
        wraplength=600,
    )
    def_lbl.pack(pady=(10, 0))

    def paint_current_row() -> None:
        if len(guesses) >= 6 or not game_active:
            return
        for i in range(t_len):
            cells[len(guesses)][i].config(text=cur_guess[i] if i < len(cur_guess) else "")

    def _show_share_button(won: bool) -> None:
        if share_btn["widget"] is not None:
            return

        def do_copy() -> None:
            text = wordle_share_text(guesses, color_rows, won=won)
            if copy_text(parent, text):
                share_btn["widget"].config(text="已复制，可粘贴分享 ✓")
            else:
                share_btn["widget"].config(text="复制失败")

        btn = tk.Button(
            parent,
            text="复制成绩",
            font=("Microsoft YaHei", 12, "bold"),
            command=do_copy,
            bg="#3498DB",
            fg="white",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
        )
        btn.place(relx=0.5, rely=0.22, anchor="center")
        share_btn["widget"] = btn

    def submit() -> None:
        nonlocal game_active, cur_guess, submitting
        if not game_active or submitting or len(cur_guess) < t_len:
            return
        submitting = True
        g_str = "".join(cur_guess).lower()

        def verify_and_continue() -> None:
            nonlocal game_active, cur_guess, submitting
            valid_def = gd.validate_wordle_guess(g_str)

            def unlock() -> None:
                nonlocal submitting
                submitting = False

            if valid_def is None:
                parent.after(
                    0,
                    lambda: (
                        result_msg.config(
                            text="无法连接验证服务器，请稍后重试",
                            fg="#E74C3C",
                            font=("Microsoft YaHei", 18, "bold"),
                        ),
                        unlock(),
                    ),
                )
                parent.after(
                    2000,
                    lambda: result_msg.config(text="") if game_active else None,
                )
                return
            if not valid_def:
                parent.after(
                    0,
                    lambda: (
                        result_msg.config(
                            text="Not in word list", fg="#E67E22"
                        ),
                        unlock(),
                    ),
                )
                parent.after(
                    2000,
                    lambda: result_msg.config(text="") if game_active else None,
                )
                return

            def apply_result() -> None:
                nonlocal game_active, cur_guess, submitting
                submitting = False
                def_lbl.config(text=f"{g_str}: {valid_def}")
                play_game_sound("submit")
                row = len(guesses)
                if row >= 6:
                    return
                colors = gd.wordle_colors(g_str, target)
                color_rows.append(list(colors))
                for i, col_name in enumerate(colors):
                    col = _COLOR_MAP[col_name]
                    cells[row][i].config(bg=col, highlightbackground=col)
                    if kb_map[g_str[i]].cget("bg") != "#2ECC71":
                        kb_map[g_str[i]].config(bg=col)
                guesses.append(g_str)
                cur_guess = []
                if g_str == target:
                    game_active = False
                    ranks = [
                        "Lucky you!",
                        "Genius!",
                        "Excellent!",
                        "Impressive!",
                        "Nice work!",
                        "Whew!",
                    ]
                    result_msg.config(text="✨ Success! ✨", fg="#2ECC71")
                    rank_lbl.config(text=ranks[row])
                    rank_lbl.place(relx=0.5, rely=0.16, anchor="center")
                    _show_share_button(won=True)
                elif len(guesses) >= 6:
                    game_active = False
                    result_msg.config(text=f"Hard Luck! ({target.upper()})", fg="#E74C3C")
                    tk.Label(
                        container,
                        text=f"{target} {desc}",
                        font=("Microsoft YaHei", 16, "bold"),
                        fg=COLOR_GOLD,
                        bg=COLOR_BG,
                        wraplength=600,
                    ).pack(pady=20)
                    _show_share_button(won=False)

            parent.after(0, apply_result)

        threading.Thread(target=verify_and_continue, daemon=True).start()

    def on_key(event) -> None:
        nonlocal cur_guess
        if not game_active:
            return "break"
        # Ignore keys while a guess is being validated
        if submitting:
            return "break"
        if event.keysym == "BackSpace" and cur_guess:
            play_game_sound("click")
            cur_guess.pop()
        elif (
            len(event.char) == 1
            and event.char.isalpha()
            and len(cur_guess) < t_len
        ):
            play_game_sound("click")
            cur_guess.append(event.char.upper())
        elif event.keysym == "Return":
            submit()
        paint_current_row()
        return "break"

    parent.bind("<Key>", on_key)
    # Keep focus on the host so letters always reach on_key
    parent.focus_set()

    tk.Button(
        parent,
        text="Exit Game (Esc)",
        font=("Microsoft YaHei", 11),
        command=on_exit,
        bg="#E74C3C",
        fg="white",
        relief="flat",
        padx=15,
        pady=4,
    ).place(relx=0.98, rely=0.08, anchor="ne")
