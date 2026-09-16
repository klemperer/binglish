"""Mini Crossword — NYT-Mini-style navigation + bilingual learning aids."""

from __future__ import annotations

import logging
import random
import re
import threading
import time
import tkinter as tk
from typing import Optional

from binglish.core.constants import COLOR_BG, COLOR_GOLD, COLOR_MUTED
from binglish.games import crossword_logic as cl
from binglish.games.share import (
    copy_text,
    crossword_grid_rows,
    crossword_share_text,
)
from binglish.games.sounds import play_game_sound
from binglish.services import game_data as gd

log = logging.getLogger(__name__)

CELL_NORMAL = "#ECF0F1"
CELL_WORD = "#D6EAF8"
CELL_CURRENT = "#85C1E9"
CLUE_NORMAL_FG = "white"
CLUE_ACTIVE_FG = COLOR_GOLD
DIRECTION_FONT = ("Microsoft YaHei", 12, "bold")


def _spacing_fix(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"([a-zA-Z0-9'\"]+)([一-龥])", r"\1 \2", text)
    text = re.sub(r"([一-龥])([a-zA-Z0-9'\"]+)", r"\1 \2", text)
    return text


def launch(
    parent: tk.Misc,
    game_data: dict,
    on_exit,
    timer_var: tk.StringVar | None = None,
) -> None:
    container = tk.Frame(parent, bg=COLOR_BG)
    container.place(relx=0.5, rely=0.50, anchor="center")

    result_msg = tk.Label(
        parent, text="", font=("Microsoft YaHei", 24, "bold"), bg=COLOR_BG
    )
    result_msg.place(relx=0.5, rely=0.1, anchor="center")

    header = tk.Frame(container, bg=COLOR_BG)
    header.pack(fill="x", pady=(8, 4))
    tk.Label(
        header,
        text="Mini Crossword",
        font=("Helvetica", 28, "bold"),
        fg=COLOR_GOLD,
        bg=COLOR_BG,
    ).pack(side="left")
    direction_var = tk.StringVar(value="方向：横向 Across")
    direction_lbl = tk.Label(
        header,
        textvariable=direction_var,
        font=DIRECTION_FONT,
        fg="#3498DB",
        bg=COLOR_BG,
    )
    direction_lbl.pack(side="right", padx=8)

    tk.Label(
        container,
        text="在网格中填入正确的字母，使水平和垂直方向的单词都能吻合线索。",
        font=("Microsoft YaHei", 13),
        fg=COLOR_MUTED,
        bg=COLOR_BG,
    ).pack(pady=(0, 8))

    tk.Button(
        parent,
        text="退出游戏 (Esc)",
        font=("Microsoft YaHei", 11),
        command=on_exit,
        bg="#E74C3C",
        fg="white",
        relief="flat",
        padx=15,
        pady=4,
    ).place(relx=0.98, rely=0.02, anchor="ne")

    tip_f = tk.Frame(container, bg=COLOR_BG)
    tip_f.pack(side="bottom", pady=(6, 0))
    tk.Label(
        tip_f,
        text=(
            "💡 方向键在当前方向内移动（另一轴只切换方向）；"
            "Tab / Shift+Tab 切换未完成词；空格或回车切换横/纵；"
            "点击线索跳转并高亮该词。"
        ),
        font=("Microsoft YaHei", 10, "italic"),
        fg="#7F8C8D",
        bg=COLOR_BG,
        wraplength=900,
        justify="center",
    ).pack()

    holder: dict = {"data": None}

    def load() -> None:
        holder["data"] = gd.fetch_crossword()
        parent.after(0, build_ui)

    def build_ui() -> None:
        cw_data = holder["data"]
        if not cw_data:
            result_msg.config(text="无法获取字谜数据，请检查网络", fg="#E74C3C")
            return

        tk.Button(
            parent,
            text="💡 提示",
            font=("Microsoft YaHei", 11),
            command=lambda: give_hint(),
            bg="#9B59B6",
            fg="white",
            relief="flat",
            padx=15,
            pady=4,
        ).place(relx=0.85, rely=0.02, anchor="ne")

        main_f = tk.Frame(container, bg=COLOR_BG)
        main_f.pack(pady=4, fill="both", expand=True)
        left = tk.Frame(main_f, bg=COLOR_BG)
        left.pack(side="left", padx=8, fill="y")
        grid_f = tk.Frame(main_f, bg=COLOR_BG)
        grid_f.pack(side="left", padx=12)
        right = tk.Frame(main_f, bg=COLOR_BG)
        right.pack(side="left", padx=8, fill="y")

        hint_holder = tk.Frame(container, bg=COLOR_BG)
        hint_holder.pack(pady=(2, 6))
        penalty_lbl = tk.Label(
            hint_holder,
            text="",
            font=("Microsoft YaHei", 11, "bold"),
            fg="#E74C3C",
            bg=COLOR_BG,
        )
        penalty_lbl.pack()
        hint_display = tk.Message(
            hint_holder,
            text="",
            font=("Microsoft YaHei", 11),
            fg="#A9DFBF",
            bg=COLOR_BG,
            justify="left",
            width=760,
        )
        hint_display.pack()

        valid_cells: dict[cl.Coord, str] = {}
        num_across: dict[cl.Coord, int] = {}
        num_down: dict[cl.Coord, int] = {}
        all_words: list[dict] = []
        for direction in ("Across", "Down"):
            for raw in cw_data.get("clues", {}).get(direction, []) or []:
                w = dict(raw)
                w["dir"] = direction
                all_words.append(w)
                if direction == "Across":
                    num_across[(w["x"], w["y"])] = w["number"]
                else:
                    num_down[(w["x"], w["y"])] = w["number"]
                for i in range(w["length"]):
                    cx = w["x"] + (i if direction == "Across" else 0)
                    cy = w["y"] + (i if direction == "Down" else 0)
                    prev = valid_cells.get((cx, cy))
                    ch = w["answer"][i]
                    if prev is not None and prev != ch:
                        log.warning(
                            "crossword data conflict at %s: %s vs %s",
                            (cx, cy),
                            prev,
                            ch,
                        )
                    valid_cells[(cx, cy)] = ch

        entry_widgets: dict[cl.Coord, tk.Entry] = {}
        clue_widgets: dict[str, tk.Label] = {}
        game_active = True
        hint_count = 0
        hinted_cells: set[cl.Coord] = set()
        locked_cells: set[cl.Coord] = set()
        completed_word_ids: set[str] = set()
        display_queue: list[dict] = []
        display_timer = [None]
        active_direction = ["Across"]
        current_cell: list[Optional[cl.Coord]] = [None]
        current_word: list[Optional[dict]] = [None]

        xs = [x for x, _ in valid_cells] or [0]
        ys = [y for _, y in valid_cells] or [0]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        grid_w = max_x - min_x + 1
        grid_h = max_y - min_y + 1

        def get_char(coord: cl.Coord) -> str:
            e = entry_widgets.get(coord)
            return e.get() if e else ""

        def set_direction(direction: str) -> None:
            active_direction[0] = direction
            if direction == "Across":
                direction_var.set("方向：横向 Across")
                direction_lbl.config(fg="#3498DB")
            else:
                direction_var.set("方向：纵向 Down")
                direction_lbl.config(fg="#E74C3C")

        def word_cells(w: dict) -> list[cl.Coord]:
            return cl.word_cells(w)

        def refresh_clue_styles() -> None:
            active_id = (
                cl.word_id(current_word[0]) if current_word[0] else None
            )
            for wid, lbl in clue_widgets.items():
                if wid == active_id:
                    lbl.config(fg=CLUE_ACTIVE_FG, font=("Microsoft YaHei", 11, "bold"))
                else:
                    lbl.config(fg=CLUE_NORMAL_FG, font=("Microsoft YaHei", 11))

        def refresh_highlights() -> None:
            word = current_word[0]
            cells = set(word_cells(word)) if word else set()
            focus = current_cell[0]
            for coord, e in entry_widgets.items():
                if coord == focus:
                    bg = CELL_CURRENT
                elif coord in cells:
                    bg = CELL_WORD
                else:
                    bg = CELL_NORMAL
                try:
                    e.config(bg=bg)
                except tk.TclError:
                    pass
            refresh_clue_styles()

        def set_current_word(word: Optional[dict]) -> None:
            current_word[0] = word
            refresh_highlights()

        def focus_coord(coord: cl.Coord, direction: Optional[str] = None) -> None:
            if coord not in entry_widgets:
                return
            if direction:
                set_direction(direction)
            word = cl.word_at(all_words, coord, active_direction[0])
            if word is None:
                word = cl.word_at(all_words, coord, cl.other_direction(active_direction[0]))
            current_cell[0] = coord
            set_current_word(word)
            entry_widgets[coord].focus_set()

        def process_display_queue() -> None:
            if not display_queue:
                display_timer[0] = None
                return
            w = display_queue.pop(0)
            ans = w.get("answer", "")
            yb = _spacing_fix(w.get("yb", ""))
            mean = _spacing_fix(w.get("meaning", ""))
            exp = _spacing_fix(w.get("explanation", ""))
            hint_display.config(
                text=f"【单词】{ans}   【音标】{yb}\n【含义】{mean}\n【解析】{exp}"
            )
            if display_queue:
                display_timer[0] = parent.after(5000, process_display_queue)
            else:
                display_timer[0] = None

        def queue_display(w: dict) -> None:
            display_queue.append(w)
            if display_timer[0] is None:
                process_display_queue()

        def check_word_completion_at(cx: int, cy: int) -> None:
            newly = []
            for w in all_words:
                wid = cl.word_id(w)
                if wid in completed_word_ids:
                    continue
                cells = word_cells(w)
                if (cx, cy) not in cells:
                    continue
                current = "".join(get_char(c).strip().upper() for c in cells)
                if current == w["answer"]:
                    newly.append((w, cells))
                    completed_word_ids.add(wid)
            newly.sort(key=lambda item: 0 if item[0]["dir"] == "Across" else 1)
            for w, cells in newly:
                queue_display(w)
                for coord in cells:
                    if coord not in locked_cells:
                        locked_cells.add(coord)
                        e = entry_widgets[coord]
                        fg = "#9B59B6" if coord in hinted_cells else COLOR_BG
                        e.config(state="readonly", readonlybackground=CELL_NORMAL, fg=fg)

        def check_cw_win() -> None:
            nonlocal game_active
            if not game_active:
                return
            for (x, y), char in valid_cells.items():
                if get_char((x, y)).strip().upper() != char:
                    return
            game_active = False
            play_game_sound("submit")
            if hint_count == 0:
                rank_text = "Genius!"
            elif hint_count <= 2:
                rank_text = "Excellent!"
            else:
                rank_text = "Keep Trying!"
            result_msg.config(text=f"✨ {rank_text} ✨", fg="#2ECC71")
            for coord, e in entry_widgets.items():
                final_fg = "#8E44AD" if coord in hinted_cells else "#27AE60"
                e.config(
                    state="disabled",
                    disabledbackground="#D5F5E3",
                    disabledforeground=final_fg,
                )
            _show_crossword_share(rank_text)

        share_state = {"btn": None}

        def _current_time_label() -> str:
            if timer_var is not None:
                m = re.search(r"(\d+):(\d+)", timer_var.get() or "")
                if m:
                    return f"{m.group(1)}:{m.group(2)}"
            return "00:00"

        def _show_crossword_share(rank_text: str) -> None:
            if share_state["btn"] is not None:
                return

            def do_copy() -> None:
                grid = crossword_grid_rows(
                    valid_cells,
                    hinted_cells,
                    min_x=min_x,
                    max_x=max_x,
                    min_y=min_y,
                    max_y=max_y,
                )
                text = crossword_share_text(
                    time_label=_current_time_label(),
                    hints=hint_count,
                    rank_text=rank_text,
                    grid_rows=grid,
                )
                if copy_text(parent, text):
                    share_state["btn"].config(text="已复制，可粘贴分享 ✓")
                else:
                    share_state["btn"].config(text="复制失败")

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
            btn.place(relx=0.5, rely=0.18, anchor="center")
            share_state["btn"] = btn

        def give_hint() -> None:
            nonlocal hint_count
            if not game_active:
                return
            unsolved = [
                w for w in all_words if not cl.word_is_filled_correct(w, get_char)
            ]
            if not unsolved:
                return
            w = random.choice(unsolved)
            modified = []
            for coord, ans_ch in zip(word_cells(w), w["answer"]):
                e = entry_widgets[coord]
                if str(e.cget("state")) == "readonly":
                    e.config(state="normal")
                e.delete(0, tk.END)
                e.insert(0, ans_ch)
                e.config(fg="#9B59B6")
                hinted_cells.add(coord)
                modified.append(coord)
            play_game_sound("click")
            if timer_var is not None:
                try:
                    cur = timer_var.get()
                    m = re.search(r"(\d+):(\d+)", cur)
                    if m:
                        total = int(m.group(1)) * 60 + int(m.group(2)) + 30
                        timer_var.set(f"Time: {total // 60:02d}:{total % 60:02d}")
                except Exception:
                    pass
            hint_count += 1
            penalty_lbl.config(
                text=f"⏳ 触发提示，总时间增加30秒！(当前已提示: {hint_count}次)"
            )
            for cx, cy in modified:
                check_word_completion_at(cx, cy)
            check_cw_win()
            refresh_highlights()

        def toggle_clue_language(widget: tk.Label, cw: dict) -> None:
            en_text = f"{cw['number']}. {cw['clue']}"
            cn_text = f"{cw['number']}. {cw.get('clue_cn', '暂无翻译')}"
            if widget.cget("text") == en_text:
                widget.config(text=cn_text)
            else:
                widget.config(text=en_text)

        def on_clue_click(widget: tk.Label, cw: dict) -> None:
            # First click selects/jumps; double-purpose: language toggle only if already active
            wid = cl.word_id(cw)
            already = current_word[0] and cl.word_id(current_word[0]) == wid
            if already:
                toggle_clue_language(widget, cw)
                refresh_clue_styles()
                return
            set_direction(cw["dir"])
            target = cl.focus_target_for_word(cw, get_char)
            current_cell[0] = target
            set_current_word(cw)
            if target in entry_widgets:
                entry_widgets[target].focus_set()
            refresh_highlights()

        tk.Label(
            left, text="Across (横向)", font=("Helvetica", 15, "bold"),
            fg="#3498DB", bg=COLOR_BG,
        ).pack(anchor="w", pady=(0, 6))
        for c in cw_data["clues"].get("Across", []) or []:
            cw = dict(c)
            cw["dir"] = "Across"
            lbl = tk.Label(
                left, text=f"{c['number']}. {c['clue']}",
                font=("Microsoft YaHei", 11), fg=CLUE_NORMAL_FG, bg=COLOR_BG,
                wraplength=340, justify="left", cursor="hand2",
            )
            lbl.pack(anchor="w", pady=2)
            clue_widgets[cl.word_id(cw)] = lbl
            lbl.bind("<Button-1>", lambda e, cw=cw, w=lbl: on_clue_click(w, cw))

        tk.Label(
            right, text="Down (纵向)", font=("Helvetica", 15, "bold"),
            fg="#E74C3C", bg=COLOR_BG,
        ).pack(anchor="w", pady=(0, 6))
        for c in cw_data["clues"].get("Down", []) or []:
            cw = dict(c)
            cw["dir"] = "Down"
            lbl = tk.Label(
                right, text=f"{c['number']}. {c['clue']}",
                font=("Microsoft YaHei", 11), fg=CLUE_NORMAL_FG, bg=COLOR_BG,
                wraplength=340, justify="left", cursor="hand2",
            )
            lbl.pack(anchor="w", pady=2)
            clue_widgets[cl.word_id(cw)] = lbl
            lbl.bind("<Button-1>", lambda e, cw=cw, w=lbl: on_clue_click(w, cw))

        def move_in_current_direction(delta: int) -> None:
            """Move within current word with wrap. No-op if no current word."""
            word = current_word[0]
            coord = current_cell[0]
            if not word or coord is None:
                return
            nxt = cl.step_in_word(word_cells(word), coord, delta)
            if nxt and nxt in entry_widgets:
                current_cell[0] = nxt
                entry_widgets[nxt].focus_set()
                refresh_highlights()

        def toggle_direction() -> None:
            set_direction(cl.other_direction(active_direction[0]))
            if current_cell[0]:
                word = cl.word_at(all_words, current_cell[0], active_direction[0])
                set_current_word(word)
            refresh_highlights()

        def tab_to_word(step: int) -> None:
            nxt = cl.next_incomplete_word(all_words, current_word[0], get_char, step)
            if not nxt:
                return
            target = cl.focus_target_for_word(nxt, get_char)
            focus_coord(target, nxt["dir"])

        # Grid cells
        for y in range(grid_h):
            for x in range(grid_w):
                gx, gy = x + min_x, y + min_y
                cell_f = tk.Frame(grid_f, width=52, height=52, bg=COLOR_BG)
                cell_f.grid(row=y, column=x, padx=2, pady=2)
                cell_f.grid_propagate(False)
                if (gx, gy) in valid_cells:
                    e = tk.Entry(
                        cell_f,
                        font=("Helvetica", 16, "bold"),
                        justify="center",
                        fg=COLOR_BG,
                        bg=CELL_NORMAL,
                        relief="flat",
                    )
                    e.place(relx=0, rely=0, relwidth=1, relheight=1)
                    entry_widgets[(gx, gy)] = e

                    if (gx, gy) in num_across:
                        lbl_a = tk.Label(
                            cell_f, text=str(num_across[(gx, gy)]),
                            font=("Helvetica", 7, "bold"), fg="#3498DB",
                            bg=CELL_NORMAL, cursor="xterm",
                        )
                        lbl_a.place(x=2, y=0)
                        lbl_a.bind(
                            "<Button-1>",
                            lambda ev, t=e, c=(gx, gy): focus_coord(c, "Across"),
                        )
                    if (gx, gy) in num_down:
                        lbl_d = tk.Label(
                            cell_f, text=str(num_down[(gx, gy)]),
                            font=("Helvetica", 7, "bold"), fg="#E74C3C",
                            bg=CELL_NORMAL, cursor="xterm",
                        )
                        lbl_d.place(x=36, y=0)
                        lbl_d.bind(
                            "<Button-1>",
                            lambda ev, t=e, c=(gx, gy): focus_coord(c, "Down"),
                        )

                    def on_focus(event, cx=gx, cy=gy):
                        current_cell[0] = (cx, cy)
                        word = cl.word_at(all_words, (cx, cy), active_direction[0])
                        if word is None:
                            word = cl.word_at(
                                all_words, (cx, cy), cl.other_direction(active_direction[0])
                            )
                        set_current_word(word)
                        refresh_highlights()

                    def on_click(event, cx=gx, cy=gy):
                        if current_cell[0] == (cx, cy):
                            toggle_direction()
                        else:
                            # Prefer current direction's word if both exist
                            word = cl.word_at(all_words, (cx, cy), active_direction[0])
                            if word is None:
                                other = cl.other_direction(active_direction[0])
                                if cl.word_at(all_words, (cx, cy), other):
                                    set_direction(other)
                        refresh_highlights()

                    e.bind("<FocusIn>", on_focus)
                    e.bind("<Button-1>", on_click)

                    def on_key(event, cx=gx, cy=gy, widget=e):
                        if not game_active:
                            return "break"
                        key = event.keysym
                        coord = (cx, cy)

                        # Tab / Shift+Tab
                        if key == "Tab":
                            step = -1 if event.state & 0x0001 else 1
                            parent.after_idle(lambda: tab_to_word(step))
                            return "break"

                        # Space / Enter → toggle direction
                        if key in ("space", "Return", "KP_Enter"):
                            toggle_direction()
                            return "break"

                        # Arrows
                        if key in ("Left", "Right", "Up", "Down"):
                            horizontal = key in ("Left", "Right")
                            if horizontal:
                                if active_direction[0] == "Across":
                                    move_in_current_direction(-1 if key == "Left" else 1)
                                else:
                                    # Down mode: left/right only switch to Across, no move
                                    set_direction("Across")
                                    word = cl.word_at(all_words, coord, "Across")
                                    set_current_word(word)
                                    refresh_highlights()
                            else:
                                if active_direction[0] == "Down":
                                    move_in_current_direction(-1 if key == "Up" else 1)
                                else:
                                    set_direction("Down")
                                    word = cl.word_at(all_words, coord, "Down")
                                    set_current_word(word)
                                    refresh_highlights()
                            return "break"

                        if key == "BackSpace":
                            if str(widget.cget("state")) == "normal":
                                widget.delete(0, tk.END)
                            move_in_current_direction(-1)
                            return "break"

                        if str(widget.cget("state")) == "readonly":
                            move_in_current_direction(1)
                            return "break"

                        char = event.char
                        if char and char.isalpha():
                            widget.delete(0, tk.END)
                            widget.insert(0, char.upper())
                            widget.config(fg=COLOR_BG)
                            check_word_completion_at(cx, cy)
                            check_cw_win()
                            move_in_current_direction(1)
                            return "break"

                        return None

                    e.bind("<Key>", on_key)
                    # Prevent default Tk class bindings from inserting space/newline
                    e.bind("<KeyRelease>", lambda ev: "break")
                else:
                    tk.Label(cell_f, bg="#1A252F").place(
                        relx=0, rely=0, relwidth=1, relheight=1
                    )

        # Initial focus: first Across word's first unsolved cell
        if all_words:
            first_word = next(
                (w for w in cl.ordered_words(all_words) if w["dir"] == "Across"),
                all_words[0],
            )
            target = cl.focus_target_for_word(first_word, get_char)
            set_direction(first_word["dir"])
            current_cell[0] = target
            set_current_word(first_word)
            if target in entry_widgets:
                entry_widgets[target].focus_set()
            refresh_highlights()

    threading.Thread(target=load, daemon=True).start()
