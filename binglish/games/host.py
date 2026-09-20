"""Game lobby host — opens overlay and routes to individual games."""

from __future__ import annotations

import logging
import threading
import tkinter as tk

from binglish.core.constants import COLOR_BG, COLOR_GOLD, COLOR_MUTED
from binglish.core.state import state
from binglish.games import crossword, sentence, vocab, wordle
from binglish.services import game_data as gd
from binglish.ui import theme

log = logging.getLogger(__name__)

_BTN_STYLE = {
    "font": theme.ui_font(14, "bold"),
    "relief": "flat",
    "borderwidth": 0,
    "highlightthickness": 0,
    "cursor": "hand2",
    "padx": 28,
    "pady": 16,
}


def open_games_overlay() -> None:
    """Must be called on the Tk main thread."""
    if state.root is None:
        return
    if not state.try_acquire_overlay():
        return

    overlay = theme.make_overlay(state.root, "Binglish Games", color=COLOR_BG, fade=True)

    game_data: dict = {}
    loading = tk.Label(
        overlay,
        text="正在加载游戏数据...",
        font=theme.ui_font(16),
        fg=COLOR_MUTED,
        bg=COLOR_BG,
    )
    loading.place(relx=0.5, rely=0.5, anchor="center")

    timer_var = tk.StringVar(value="Time: 00:00")
    # start: wall-clock base; penalty: extra seconds (hints etc.) owned by host.
    timer_state = {"active": False, "start": 0.0, "penalty": 0}

    timer_lbl = tk.Label(
        overlay,
        textvariable=timer_var,
        font=("Helvetica", 20, "bold"),
        fg=COLOR_MUTED,
        bg=COLOR_BG,
    )
    # Hidden in lobby; raised above the game host frame when a match starts.
    timer_visible = {"on": False}

    def _format_elapsed(total_seconds: int) -> str:
        return f"Time: {total_seconds // 60:02d}:{total_seconds % 60:02d}"

    def _elapsed_seconds() -> int:
        import time as _time

        base = _time.time() - float(timer_state.get("start") or _time.time())
        penalty = float(timer_state.get("penalty") or 0)
        return int(base + penalty)

    def add_timer_penalty(seconds: float) -> None:
        """Cumulative time penalty applied by games (e.g. crossword hints)."""
        if not timer_state.get("active"):
            return
        timer_state["penalty"] = float(timer_state.get("penalty") or 0) + float(seconds)
        timer_var.set(_format_elapsed(_elapsed_seconds()))

    def stop_timer() -> None:
        """Freeze the displayed time when a match ends (overlay stays open)."""
        timer_state["active"] = False

    def show_timer() -> None:
        timer_visible["on"] = True
        timer_state["penalty"] = 0
        timer_var.set("Time: 00:00")
        timer_lbl.place(relx=0.02, rely=0.02, anchor="nw")
        timer_lbl.lift()

    def hide_timer() -> None:
        timer_visible["on"] = False
        try:
            timer_lbl.place_forget()
        except tk.TclError:
            pass

    def update_timer() -> None:
        if not timer_state["active"] or not state.is_overlay_showing:
            return
        # Host owns the clock: elapsed + penalty. Games must not write timer_var.
        timer_var.set(_format_elapsed(_elapsed_seconds()))
        if timer_visible["on"]:
            try:
                timer_lbl.lift()
            except tk.TclError:
                pass
        overlay.after(1000, update_timer)

    def on_close_game(_event=None) -> None:
        timer_state["active"] = False
        state.release_overlay()
        try:
            overlay.destroy()
        except tk.TclError:
            pass

    def fade(a=0.0) -> None:
        if theme.IS_MAC:
            try:
                overlay.attributes("-alpha", 1.0)
            except tk.TclError:
                pass
            return
        if a < 0.95:
            a += 0.05
            overlay.attributes("-alpha", a)
            overlay.after(20, fade, a)

    def show_lobby() -> None:
        loading.destroy()
        hide_timer()
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
            font=theme.ui_font(16),
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
            timer_state["penalty"] = 0
            show_timer()
            update_timer()
            # Full-screen host: child games use place() relative to this frame
            # (same coordinate space as the overlay). A centered 0-size frame
            # would collapse Wordle and put Sentence chrome in the middle.
            host = tk.Frame(overlay, bg=COLOR_BG)
            host.place(relx=0, rely=0, relwidth=1, relheight=1)
            try:
                if game_type == "shuffle":
                    sentence.launch(
                        host, game_data, on_close_game, on_game_end=stop_timer
                    )
                elif game_type == "wordle":
                    wordle.launch(
                        host, game_data, on_close_game, on_game_end=stop_timer
                    )
                elif game_type == "crossword":
                    crossword.launch(
                        host,
                        game_data,
                        on_close_game,
                        timer_var=timer_var,
                        add_timer_penalty=add_timer_penalty,
                        on_game_end=stop_timer,
                    )
                elif game_type == "vocab":
                    vocab.launch(
                        host, game_data, on_close_game, on_game_end=stop_timer
                    )
                # Host frame is full-screen and would cover the timer.
                timer_lbl.lift()
                theme.focus_widget(host, delay_ms=50)
            except Exception:
                log.exception("game launch failed: %s", game_type)
                tk.Label(
                    overlay,
                    text="游戏启动失败，请重试",
                    font=theme.ui_font(16),
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
            try:
                theme.make_button(
                    btn_frame,
                    text=label,
                    bg=color,
                    fg="white",
                    command=lambda k=key: start(k),
                    **_BTN_STYLE,
                ).pack(side="left", padx=10)
            except Exception:
                log.exception("lobby button failed: %s", label)
                # Last-resort: plain colored tk.Button so the entry stays visible
                tk.Button(
                    btn_frame,
                    text=label,
                    bg=color,
                    fg="white",
                    relief="flat",
                    padx=20,
                    pady=12,
                    command=lambda k=key: start(k),
                ).pack(side="left", padx=10)

        try:
            theme.make_button(
                lobby,
                text=" 返回桌面 ",
                font=theme.ui_font(13, "bold"),
                fg="white",
                bg="#34495E",
                relief="flat",
                borderwidth=0,
                highlightthickness=0,
                padx=40,
                pady=12,
                cursor="hand2",
                command=on_close_game,
            ).pack(pady=30)
        except Exception:
            log.exception("lobby back button failed")
            tk.Button(
                lobby,
                text=" 返回桌面 ",
                bg="#34495E",
                fg="white",
                command=on_close_game,
            ).pack(pady=30)
        try:
            lobby.update_idletasks()
        except tk.TclError:
            pass

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
        theme.focus_widget(overlay, delay_ms=50)

    overlay.bind("<Escape>", on_close_game)
    threading.Thread(target=load_catalog, daemon=True).start()
