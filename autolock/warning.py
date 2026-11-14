"""Cửa sổ cảnh báo trước khi Lock / Sleep / Shutdown."""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from .idle import ACTION_LABELS, ACTION_LOCK, get_idle_seconds, perform_action

if TYPE_CHECKING:
    from .app import AutoLockApp


class WarningOverlay:
    def __init__(self, app: "AutoLockApp") -> None:
        self.app = app
        self.win: tk.Toplevel | None = None
        self._remaining = 0
        self._tick_job: str | None = None
        self._action = ACTION_LOCK

    @property
    def visible(self) -> bool:
        return self.win is not None and self.win.winfo_exists()

    def show(self, seconds: int, action: str = ACTION_LOCK) -> None:
        if self.visible:
            return
        self._action = action if action in ACTION_LABELS else ACTION_LOCK
        self._remaining = max(1, int(seconds))
        win = tk.Toplevel(self.app.root)
        self.win = win
        win.title("Sắp thực hiện")
        win.attributes("-topmost", True)
        win.resizable(False, False)
        win.configure(bg="#1a1d23")
        win.protocol("WM_DELETE_WINDOW", self.cancel)

        w, h = 400, 200
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        frame = tk.Frame(win, bg="#1a1d23", padx=24, pady=20)
        frame.pack(fill="both", expand=True)

        label = ACTION_LABELS.get(self._action, "Khóa màn hình")
        tk.Label(
            frame,
            text="Không phát hiện hoạt động",
            font=("Segoe UI", 13, "bold"),
            fg="#f0f2f5",
            bg="#1a1d23",
        ).pack(anchor="w")

        self.countdown_label = tk.Label(
            frame,
            text="",
            font=("Segoe UI", 22, "bold"),
            fg="#ff6b6b",
            bg="#1a1d23",
        )
        self.countdown_label.pack(anchor="w", pady=(6, 2))

        tk.Label(
            frame,
            text=f"Sẽ: {label}. Di chuyển chuột/phím để hủy.",
            font=("Segoe UI", 9),
            fg="#9aa3b2",
            bg="#1a1d23",
        ).pack(anchor="w")

        btn_row = tk.Frame(frame, bg="#1a1d23")
        btn_row.pack(anchor="e", pady=(14, 0))
        tk.Button(
            btn_row,
            text="Hủy",
            font=("Segoe UI", 9),
            bg="#2d3340",
            fg="#f0f2f5",
            activebackground="#3d4555",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=5,
            cursor="hand2",
            command=self.cancel,
        ).pack(side="right")

        self._update_text()
        self._schedule_tick()
        win.deiconify()
        win.lift()
        win.focus_force()

    def _update_text(self) -> None:
        if not self.visible:
            return
        label = ACTION_LABELS.get(self._action, "Thực hiện")
        self.countdown_label.config(text=f"{label} sau {self._remaining}s")

    def _schedule_tick(self) -> None:
        if self.win is None:
            return
        self._tick_job = self.win.after(1000, self._on_tick)

    def _on_tick(self) -> None:
        if not self.visible:
            return
        if get_idle_seconds() < 0.8:
            self.cancel()
            return
        self._remaining -= 1
        if self._remaining <= 0:
            action = self._action
            self.close()
            perform_action(action)
            self.app.on_action_done(action)
            return
        self._update_text()
        self._schedule_tick()

    def cancel(self) -> None:
        self.close()
        self.app.on_warning_cancelled()

    def close(self) -> None:
        if self.win is None:
            return
        if self._tick_job is not None:
            try:
                self.win.after_cancel(self._tick_job)
            except tk.TclError:
                pass
            self._tick_job = None
        try:
            self.win.destroy()
        except tk.TclError:
            pass
        self.win = None
