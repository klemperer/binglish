"""Game lobby host — opens overlay and routes to individual games."""

from __future__ import annotations

import logging
import threading
import tkinter as tk

from binglish.core.constants import COLOR_BG, COLOR_GOLD, COLOR_MUTED
from binglish.core.state import state
from binglish.games import crossword, sentence, vocab, wordle
from binglish.services import game_data as gd

log = logging.getLogger(__name__)

_BTN_STYLE = {
    "font": ("Microsoft YaHei", 14, "bold"),
    "width": 20,
    "height": 2,
    "relief": "flat",
    "cursor": "hand2",
}


def open_games_overlay() -> None:
    """Must be called on the Tk main thread."""
    if state.root is None:
        return
    if not state.try_acquire_overlay():
        return

    overlay = tk.Toplevel(state.root)
    overlay.title("Binglish Games")
    w = state.root.winfo_screenwidth()
    h = state.root.winfo_screenheight()
    overlay.geometry(f"{w}x{h}+0+0")
    overlay.overrideredirect(True)
    overlay.attributes("-topmost", True, "-alpha", 0.0)
    overlay.configure(bg=COLOR_BG)

    game_data: dict = {}
    loading = tk.Label(
        overlay,
        text="正在加载游戏数据...",
        font=("Microsoft YaHei", 16),
        fg=COLOR_MUTED,
        bg=COLOR_BG,
    )
    loading.place(relx=0.5, rely=0.5, anchor="center")

    timer_var = tk.StringVar(value="Time: 00:00")
    timer_state = {"active": False, "start": 0.0}

    timer_lbl = tk.Label(
        overlay,
        textvariable=timer_var,
        font=("Helvetica", 20, "bold"),
        fg=COLOR_MUTED,
        bg=COLOR_BG,
    )
    timer_lbl.place(relx=0.02, rely=0.02, anchor="nw")

    def update_timer() -> None:
        if not timer_state["active"] or not state.is_overlay_showing:
            return
        elapsed = int(__import__("time").time() - timer_state["start"])
        timer_var.set(f"Time: {elapsed // 60:02d}:{elapsed % 60:02d}")
        overlay.after(1000, update_timer)

    def on_close_game(_event=None) -> None:
        timer_state["active"] = False
        state.release_overlay()
        try:
            overlay.destroy()
        except tk.TclError:
            pass

    def fade(a=0.0) -> None:
        if a < 0.95:
            a += 0.05
            overlay.attributes("-alpha", a)
            overlay.after(20, fade, a)

    def show_lobby() -> None:
        loading.destroy()
        lobby = tk.Frame(overlay, bg=COLOR_BG)
        lobby.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(
            lobby,
            text="Binglish Games",
            font=("Helvetica", 40, "bold"),
            fg=COLOR_GOLD,
            bg=COLOR_BG,
        ).pack(pady=40)
        tk.Label(
            lobby,
            text="请选择一个单词游戏开始挑战：",
            font=("Microsoft YaHei", 16),
            fg=COLOR_MUTED,
            bg=COLOR_BG,
        ).pack(pady=10)

        btn_frame = tk.Frame(lobby, bg=COLOR_BG)
        btn_frame.pack(pady=30)

        def start(game_type: str) -> None:
            import time as _time

            lobby.destroy()
            timer_state["active"] = True
            timer_state["start"] = _time.time()
            timer_var.set("Time: 00:00")
            update_timer()
            # Full-screen host: child games use place() relative to this frame
            # (same coordinate space as the overlay). A centered 0-size frame
            # would collapse Wordle and put Sentence chrome in the middle.
            host = tk.Frame(overlay, bg=COLOR_BG)
            host.place(relx=0, rely=0, relwidth=1, relheight=1)
            try:
                if game_type == "shuffle":
                    sentence.launch(host, game_data, on_close_game)
                elif game_type == "wordle":
                    wordle.launch(host, game_data, on_close_game)
                elif game_type == "crossword":
                    crossword.launch(
                        host, game_data, on_close_game, timer_var=timer_var
                    )
                elif game_type == "vocab":
                    vocab.launch(host, game_data, on_close_game)
            except Exception:
                log.exception("game launch failed: %s", game_type)
                tk.Label(
                    overlay,
                    text="游戏启动失败，请重试",
                    font=("Microsoft YaHei", 16),
                    fg="#E74C3C",
                    bg=COLOR_BG,
                ).place(relx=0.5, rely=0.5, anchor="center")

        games = [
            ("Sentence Master", "#3498DB", "shuffle"),
            ("Binglish Wordle", "#2ECC71", "wordle"),
            ("Mini Crossword", "#9B59B6", "crossword"),
            ("Test Your Vocabulary", "#E67E22", "vocab"),
        ]
        for label, color, key in games:
            tk.Button(
                btn_frame,
                text=label,
                bg=color,
                fg="white",
                command=lambda k=key: start(k),
                **_BTN_STYLE,
            ).pack(side="left", padx=10)

        tk.Button(
            lobby,
            text=" 返回桌面 ",
            font=("Microsoft YaHei", 13, "bold"),
            fg="white",
            bg="#34495E",
            relief="flat",
            padx=40,
            pady=10,
            cursor="hand2",
            command=on_close_game,
        ).pack(pady=30)

    def load_catalog() -> None:
        data = gd.fetch_game_catalog()
        overlay.after(0, lambda: finish(data))

    def finish(data: dict) -> None:
        nonlocal game_data
        game_data = data or {}
        if not game_data:
            on_close_game()
            return
        show_lobby()
        fade(0)
        overlay.focus_force()

    overlay.bind("<Escape>", on_close_game)
    threading.Thread(target=load_catalog, daemon=True).start()
