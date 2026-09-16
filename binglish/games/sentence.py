"""Sentence Master: unscramble a sentence."""

from __future__ import annotations

import random
import re
import tkinter as tk

from binglish.core.constants import COLOR_BG, COLOR_GOLD, COLOR_MUTED
from binglish.games.sounds import play_game_sound
from binglish.services.game_data import sentence_master_rank


def launch(parent: tk.Misc, game_data: dict, on_exit) -> None:
    payload = game_data.get("shuffle") or {}
    raw_sentence = payload.get("en") or ""
    cn = payload.get("cn") or ""
    if not raw_sentence:
        tk.Label(
            parent,
            text="Sentence data unavailable",
            font=("Microsoft YaHei", 16),
            fg="#E74C3C",
            bg=COLOR_BG,
        ).pack(pady=40)
        return

    words_only = re.findall(r"[\w']+", raw_sentence)
    indexed_pool = [{"id": i, "word": w} for i, w in enumerate(words_only)]
    shuffled_pool = indexed_pool[:]
    random.shuffle(shuffled_pool)
    tokens = re.findall(r"[\w']+|[^\w\s]", raw_sentence)
    user_order: list = [None] * len(words_only)
    slot_btns: list[tk.Button] = []
    pool_btns: dict[int, tk.Button] = {}
    attempts_var = tk.IntVar(value=1)
    game_active = True

    container = tk.Frame(parent, bg=COLOR_BG)
    container.pack(expand=True)

    tk.Label(
        container,
        text="Sentence Master",
        font=("Helvetica", 32, "bold"),
        fg=COLOR_GOLD,
        bg=COLOR_BG,
    ).pack(pady=5)
    tk.Label(
        container,
        text="还原被打乱的句子，点击下方单词填入横线，点击横线上的单词重填。",
        font=("Microsoft YaHei", 14),
        fg=COLOR_MUTED,
        bg=COLOR_BG,
    ).pack(pady=(0, 10))

    attempts_lbl = tk.Label(
        parent,
        text="",
        font=("Helvetica", 22, "bold"),
        fg=COLOR_GOLD,
        bg=COLOR_BG,
    )
    attempts_lbl.place(relx=0.82, rely=0.02, anchor="ne")
    result_msg = tk.Label(
        parent, text="", font=("Microsoft YaHei", 24, "bold"), bg=COLOR_BG
    )
    result_msg.place(relx=0.5, rely=0.1, anchor="center")

    def update_attempts_ui() -> None:
        attempts_lbl.config(text=f"尝试次数: {attempts_var.get()}")

    update_attempts_ui()

    def check_win() -> None:
        nonlocal game_active
        if None in user_order or not game_active:
            return
        is_correct = all(
            user_order[i]["word"].lower() == words_only[i].lower()
            for i in range(len(words_only))
        )
        if not is_correct:
            attempts_var.set(attempts_var.get() + 1)
            update_attempts_ui()
            return

        game_active = False
        play_game_sound("submit")
        for btn in slot_btns:
            btn.config(bg="#27AE60", state="disabled")
        for b in pool_btns.values():
            b.config(state="disabled")
        rank_text = sentence_master_rank(attempts_var.get())
        result_msg.config(text=f"🎉 {rank_text} 🎉", fg="#2ECC71")
        tk.Label(
            container,
            text=cn,
            font=("Microsoft YaHei", 14),
            fg=COLOR_MUTED,
            bg=COLOR_BG,
            wraplength=800,
        ).pack(pady=20)

    def on_pool_click(obj) -> None:
        if not game_active:
            return
        for i in range(len(user_order)):
            if user_order[i] is None:
                play_game_sound("click")
                user_order[i] = obj
                pool_btns[obj["id"]].pack_forget()
                if obj["word"].lower() == words_only[i].lower():
                    slot_btns[i].config(text=obj["word"], fg="white", bg="#27AE60")
                else:
                    slot_btns[i].config(text=obj["word"], fg="white", bg=COLOR_BG)
                    attempts_var.set(attempts_var.get() + 1)
                    update_attempts_ui()
                check_win()
                break

    def on_slot_click(idx: int) -> None:
        if not game_active or user_order[idx] is None:
            return
        if user_order[idx]["word"].lower() == words_only[idx].lower():
            return
        play_game_sound("click")
        obj = user_order[idx]
        user_order[idx] = None
        slot_btns[idx].config(text="______", fg="#5D6D7E", bg=COLOR_BG)
        pool_btns[obj["id"]].pack(side="left", padx=5, pady=5)

    slots_wrap = tk.Frame(container, bg=COLOR_BG)
    slots_wrap.pack(pady=20)
    current_row = tk.Frame(slots_wrap, bg=COLOR_BG)
    current_row.pack(pady=10)

    w_idx, row_chars = 0, 0
    MAX_ROW = 60
    for t in tokens:
        if row_chars > MAX_ROW:
            current_row = tk.Frame(slots_wrap, bg=COLOR_BG)
            current_row.pack(pady=8)
            row_chars = 0
        if re.match(r"[\w']+", t):
            curr = w_idx
            btn = tk.Button(
                current_row,
                text="______",
                font=("Helvetica", 16),
                fg="#5D6D7E",
                bg=COLOR_BG,
                relief="flat",
                command=lambda i=curr: on_slot_click(i),
            )
            btn.pack(side="left", padx=5)
            slot_btns.append(btn)
            w_idx += 1
            row_chars += 10
        else:
            tk.Label(
                current_row,
                text=t,
                font=("Helvetica", 18, "bold"),
                fg="white",
                bg=COLOR_BG,
            ).pack(side="left")
            row_chars += 2

    pool_wrap = tk.Frame(container, bg=COLOR_BG)
    pool_wrap.pack(pady=20)
    pool_row = tk.Frame(pool_wrap, bg=COLOR_BG)
    pool_row.pack(pady=5)
    pool_chars = 0
    for obj in shuffled_pool:
        if pool_chars > MAX_ROW:
            pool_row = tk.Frame(pool_wrap, bg=COLOR_BG)
            pool_row.pack(pady=5)
            pool_chars = 0
        b = tk.Button(
            pool_row,
            text=obj["word"],
            font=("Helvetica", 14),
            bg="#ECF0F1",
            fg=COLOR_BG,
            padx=15,
            pady=5,
            command=lambda o=obj: on_pool_click(o),
        )
        b.pack(side="left", padx=5, pady=5)
        pool_btns[obj["id"]] = b
        pool_chars += len(obj["word"]) + 4

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
