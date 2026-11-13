"""
AutoLockScreen — khóa màn hình khi không dùng chuột/bàn phím.
Windows only. Không cần thư viện bên thứ ba.
"""

from __future__ import annotations

import json
import sys
import ctypes
from ctypes import wintypes
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

def _app_dir() -> Path:
    # Khi đóng gói .exe: lưu config cạnh file exe (có quyền ghi)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = _app_dir()
CONFIG_PATH = APP_DIR / "config.json"

DEFAULT_CONFIG = {
    "idle_seconds": 60,
    "warning_seconds": 15,
    "enabled": False,
}

# ---------- Windows idle + lock ----------

class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.UINT),
        ("dwTime", wintypes.DWORD),
    ]


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32


def get_idle_seconds() -> float:
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not user32.GetLastInputInfo(ctypes.byref(info)):
        return 0.0
    tick = kernel32.GetTickCount()
    idle_ms = (tick - info.dwTime) & 0xFFFFFFFF
    return idle_ms / 1000.0


def lock_workstation() -> None:
    user32.LockWorkStation()


# ---------- Config ----------

def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            cfg = dict(DEFAULT_CONFIG)
            cfg.update(data)
            return cfg
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ---------- Warning overlay ----------

class WarningOverlay:
    def __init__(self, app: "AutoLockApp") -> None:
        self.app = app
        self.win: tk.Toplevel | None = None
        self._remaining = 0
        self._tick_job: str | None = None

    @property
    def visible(self) -> bool:
        return self.win is not None and self.win.winfo_exists()

    def show(self, seconds: int) -> None:
        if self.visible:
            return
        self._remaining = max(1, int(seconds))
        win = tk.Toplevel(self.app.root)
        self.win = win
        win.title("Sắp khóa màn hình")
        win.attributes("-topmost", True)
        win.resizable(False, False)
        win.configure(bg="#1a1d23")
        win.protocol("WM_DELETE_WINDOW", self.cancel)

        # Center on primary screen
        w, h = 420, 220
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        frame = tk.Frame(win, bg="#1a1d23", padx=28, pady=24)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame,
            text="Không phát hiện hoạt động",
            font=("Segoe UI", 14, "bold"),
            fg="#f0f2f5",
            bg="#1a1d23",
        ).pack(anchor="w")

        self.countdown_label = tk.Label(
            frame,
            text="",
            font=("Segoe UI", 28, "bold"),
            fg="#ff6b6b",
            bg="#1a1d23",
        )
        self.countdown_label.pack(anchor="w", pady=(8, 4))

        tk.Label(
            frame,
            text="Di chuyển chuột hoặc nhấn phím để hủy.",
            font=("Segoe UI", 10),
            fg="#9aa3b2",
            bg="#1a1d23",
        ).pack(anchor="w")

        btn_row = tk.Frame(frame, bg="#1a1d23")
        btn_row.pack(anchor="e", pady=(20, 0))

        cancel_btn = tk.Button(
            btn_row,
            text="Hủy khóa",
            font=("Segoe UI", 10),
            bg="#2d3340",
            fg="#f0f2f5",
            activebackground="#3d4555",
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.cancel,
        )
        cancel_btn.pack(side="right")

        self._update_text()
        self._schedule_tick()
        win.focus_force()

    def _update_text(self) -> None:
        if not self.visible:
            return
        self.countdown_label.config(
            text=f"Khóa sau {self._remaining} giây"
        )

    def _schedule_tick(self) -> None:
        if self.win is None:
            return
        self._tick_job = self.win.after(1000, self._on_tick)

    def _on_tick(self) -> None:
        if not self.visible:
            return
        # Activity during warning → cancel
        if get_idle_seconds() < 0.8:
            self.cancel()
            return
        self._remaining -= 1
        if self._remaining <= 0:
            self.close()
            lock_workstation()
            self.app.on_locked()
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


# ---------- Main app ----------

class AutoLockApp:
    POLL_MS = 250

    def __init__(self) -> None:
        self.cfg = load_config()
        self.root = tk.Tk()
        self.root.title("Auto Lock Screen")
        self.root.minsize(420, 460)
        self.root.configure(bg="#12141a")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.warning = WarningOverlay(self)
        self._poll_job: str | None = None
        self._enabled = bool(self.cfg.get("enabled", False))

        self._build_style()
        self._build_ui()
        self._sync_ui_from_config()
        self._update_status_labels()
        if self._enabled:
            self._start_monitoring()

    def _build_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        bg = "#12141a"
        card = "#1a1d23"
        fg = "#e8eaed"
        muted = "#9aa3b2"
        accent = "#4c8bf5"
        style.configure(".", background=bg, foreground=fg, font=("Segoe UI", 10))
        style.configure("TFrame", background=bg)
        style.configure("Card.TFrame", background=card)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("Card.TLabel", background=card, foreground=fg)
        style.configure("Muted.TLabel", background=bg, foreground=muted)
        style.configure("CardMuted.TLabel", background=card, foreground=muted)
        style.configure("Title.TLabel", background=bg, foreground=fg, font=("Segoe UI", 18, "bold"))
        style.configure("Status.TLabel", background=card, foreground=accent, font=("Segoe UI", 11, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=(12, 6))
        style.configure(
            "Accent.TButton",
            background=accent,
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
            padding=(14, 8),
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#3a74d8"), ("disabled", "#3a4050")],
            foreground=[("disabled", "#888")],
        )
        style.configure(
            "TSpinbox",
            fieldbackground="#252a33",
            foreground=fg,
            background=card,
            arrowcolor=fg,
        )
        style.configure(
            "Horizontal.TScale",
            background=card,
            troughcolor="#252a33",
        )
        style.configure("TCheckbutton", background=card, foreground=fg)
        style.map("TCheckbutton", background=[("active", card)])

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=(0, 16, 0, 16))
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Auto Lock Screen", style="Title.TLabel").pack(
            anchor="w", padx=24, pady=(0, 4)
        )
        ttk.Label(
            outer,
            text="Theo dõi chuột & bàn phím — cảnh báo rồi khóa khi không hoạt động.",
            style="Muted.TLabel",
            wraplength=380,
        ).pack(anchor="w", padx=24, pady=(0, 12))

        # Status + Bật/Tắt ngay trên đầu — luôn nhìn thấy
        status_card = ttk.Frame(outer, style="Card.TFrame", padding=16)
        status_card.pack(fill="x", padx=24, pady=(0, 8))

        head = ttk.Frame(status_card, style="Card.TFrame")
        head.pack(fill="x")
        left = ttk.Frame(head, style="Card.TFrame")
        left.pack(side="left", fill="x", expand=True)
        ttk.Label(left, text="Trạng thái", style="Card.TLabel").pack(anchor="w")
        self.status_label = ttk.Label(left, text="Đã tắt", style="Status.TLabel")
        self.status_label.pack(anchor="w", pady=(4, 0))
        self.toggle_btn = ttk.Button(
            head,
            text="Bật theo dõi",
            style="Accent.TButton",
            command=self.toggle_monitoring,
        )
        self.toggle_btn.pack(side="right", padx=(12, 0))

        self.idle_now_label = ttk.Label(
            status_card, text="Idle hiện tại: —", style="CardMuted.TLabel"
        )
        self.idle_now_label.pack(anchor="w", pady=(8, 0))
        self.countdown_hint = ttk.Label(
            status_card, text="", style="CardMuted.TLabel"
        )
        self.countdown_hint.pack(anchor="w", pady=(2, 0))

        card = ttk.Frame(outer, style="Card.TFrame", padding=16)
        card.pack(fill="x", padx=24, pady=8)

        # Idle timeout
        ttk.Label(card, text="Thời gian chờ (không hoạt động)", style="Card.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            card,
            text="Sau khoảng này sẽ hiện thông báo sắp khóa.",
            style="CardMuted.TLabel",
        ).pack(anchor="w", pady=(0, 6))

        idle_row = ttk.Frame(card, style="Card.TFrame")
        idle_row.pack(fill="x", pady=(0, 4))
        self.idle_var = tk.IntVar(value=int(self.cfg["idle_seconds"]))
        self.idle_scale = ttk.Scale(
            idle_row,
            from_=5,
            to=600,
            orient="horizontal",
            command=self._on_idle_scale,
        )
        self.idle_scale.set(self.idle_var.get())
        self.idle_scale.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.idle_spin = ttk.Spinbox(
            idle_row,
            from_=5,
            to=3600,
            width=6,
            textvariable=self.idle_var,
            command=self._on_idle_spin,
        )
        self.idle_spin.pack(side="right")
        self.idle_spin.bind("<FocusOut>", lambda e: self._on_idle_spin())
        self.idle_spin.bind("<Return>", lambda e: self._on_idle_spin())
        ttk.Label(card, text="giây", style="CardMuted.TLabel").pack(anchor="e")

        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=12)

        # Warning timeout
        ttk.Label(card, text="Thời gian chờ thông báo", style="Card.TLabel").pack(
            anchor="w"
        )
        ttk.Label(
            card,
            text="Đếm ngược trên thông báo trước khi khóa màn hình.",
            style="CardMuted.TLabel",
        ).pack(anchor="w", pady=(0, 6))

        warn_row = ttk.Frame(card, style="Card.TFrame")
        warn_row.pack(fill="x", pady=(0, 4))
        self.warn_var = tk.IntVar(value=int(self.cfg["warning_seconds"]))
        self.warn_scale = ttk.Scale(
            warn_row,
            from_=3,
            to=120,
            orient="horizontal",
            command=self._on_warn_scale,
        )
        self.warn_scale.set(self.warn_var.get())
        self.warn_scale.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.warn_spin = ttk.Spinbox(
            warn_row,
            from_=1,
            to=600,
            width=6,
            textvariable=self.warn_var,
            command=self._on_warn_spin,
        )
        self.warn_spin.pack(side="right")
        self.warn_spin.bind("<FocusOut>", lambda e: self._on_warn_spin())
        self.warn_spin.bind("<Return>", lambda e: self._on_warn_spin())
        ttk.Label(card, text="giây", style="CardMuted.TLabel").pack(anchor="e")

        actions = ttk.Frame(outer)
        actions.pack(fill="x", padx=24, pady=(8, 0))
        ttk.Button(actions, text="Lưu cài đặt", command=self.save_settings).pack(
            side="left"
        )
        ttk.Button(actions, text="Thử khóa ngay", command=self._test_lock).pack(
            side="right"
        )

        ttk.Label(
            outer,
            text="Bấm «Bật theo dõi» để chạy. Di chuyển chuột khi có cảnh báo để hủy khóa.",
            style="Muted.TLabel",
            wraplength=380,
        ).pack(anchor="w", padx=24, pady=(12, 0))

    def _clamp_idle(self, value: int) -> int:
        return max(5, min(3600, int(value)))

    def _clamp_warn(self, value: int) -> int:
        return max(1, min(600, int(value)))

    def _on_idle_scale(self, raw: str) -> None:
        v = self._clamp_idle(int(float(raw)))
        if self.idle_var.get() != v:
            self.idle_var.set(v)

    def _on_idle_spin(self) -> None:
        try:
            v = self._clamp_idle(int(self.idle_var.get()))
        except (tk.TclError, ValueError):
            v = 60
        self.idle_var.set(v)
        self.idle_scale.set(min(600, v))

    def _on_warn_scale(self, raw: str) -> None:
        v = self._clamp_warn(int(float(raw)))
        if self.warn_var.get() != v:
            self.warn_var.set(v)

    def _on_warn_spin(self) -> None:
        try:
            v = self._clamp_warn(int(self.warn_var.get()))
        except (tk.TclError, ValueError):
            v = 15
        self.warn_var.set(v)
        self.warn_scale.set(min(120, v))

    def _sync_ui_from_config(self) -> None:
        idle = self._clamp_idle(int(self.cfg.get("idle_seconds", 60)))
        warn = self._clamp_warn(int(self.cfg.get("warning_seconds", 15)))
        self.idle_var.set(idle)
        self.warn_var.set(warn)
        self.idle_scale.set(min(600, idle))
        self.warn_scale.set(min(120, warn))
        self._refresh_toggle_button()

    def _read_settings_from_ui(self) -> dict:
        self._on_idle_spin()
        self._on_warn_spin()
        return {
            "idle_seconds": self._clamp_idle(int(self.idle_var.get())),
            "warning_seconds": self._clamp_warn(int(self.warn_var.get())),
            "enabled": self._enabled,
        }

    def save_settings(self) -> None:
        self.cfg = self._read_settings_from_ui()
        save_config(self.cfg)
        messagebox.showinfo("Đã lưu", "Cài đặt đã được lưu.", parent=self.root)

    def _refresh_toggle_button(self) -> None:
        if self._enabled:
            self.toggle_btn.configure(text="Tắt theo dõi")
        else:
            self.toggle_btn.configure(text="Bật theo dõi")

    def toggle_monitoring(self) -> None:
        if self._enabled:
            self._stop_monitoring()
        else:
            self.cfg = self._read_settings_from_ui()
            save_config(self.cfg)
            self._start_monitoring()

    def _start_monitoring(self) -> None:
        self._enabled = True
        self.cfg["enabled"] = True
        save_config(self.cfg)
        self._refresh_toggle_button()
        self._update_status_labels()
        self._schedule_poll()

    def _stop_monitoring(self) -> None:
        self._enabled = False
        self.cfg["enabled"] = False
        save_config(self.cfg)
        if self._poll_job is not None:
            try:
                self.root.after_cancel(self._poll_job)
            except tk.TclError:
                pass
            self._poll_job = None
        if self.warning.visible:
            self.warning.close()
        self._refresh_toggle_button()
        self._update_status_labels()

    def _schedule_poll(self) -> None:
        self._poll_job = self.root.after(self.POLL_MS, self._poll)

    def _poll(self) -> None:
        if not self._enabled:
            return
        idle = get_idle_seconds()
        idle_limit = self._clamp_idle(int(self.idle_var.get() or self.cfg["idle_seconds"]))
        warn_secs = self._clamp_warn(int(self.warn_var.get() or self.cfg["warning_seconds"]))

        self.idle_now_label.configure(text=f"Idle hiện tại: {idle:.1f} giây")

        if self.warning.visible:
            # WarningOverlay tự xử lý đếm ngược + hủy khi có activity
            remaining_to_warn = 0
        else:
            remaining_to_warn = max(0, idle_limit - idle)
            if idle >= idle_limit:
                self.warning.show(warn_secs)
                self.status_label.configure(text="Đang cảnh báo…")

        if not self.warning.visible:
            if remaining_to_warn > 0:
                self.countdown_hint.configure(
                    text=f"Còn ~{remaining_to_warn:.0f}s trước khi hiện thông báo"
                )
            else:
                self.countdown_hint.configure(text="")
            if self._enabled and not self.warning.visible:
                self.status_label.configure(text="Đang theo dõi")

        self._schedule_poll()

    def _update_status_labels(self) -> None:
        if self._enabled:
            self.status_label.configure(text="Đang theo dõi")
            self.countdown_hint.configure(text="")
        else:
            self.status_label.configure(text="Đã tắt")
            self.idle_now_label.configure(text="Idle hiện tại: —")
            self.countdown_hint.configure(text="")

    def on_warning_cancelled(self) -> None:
        if self._enabled:
            self.status_label.configure(text="Đang theo dõi")
            self.countdown_hint.configure(text="Đã hủy — chờ idle lại từ đầu")

    def on_locked(self) -> None:
        if self._enabled:
            self.status_label.configure(text="Đã khóa — tiếp tục theo dõi")

    def _test_lock(self) -> None:
        if messagebox.askyesno(
            "Thử khóa",
            "Khóa màn hình ngay bây giờ?",
            parent=self.root,
        ):
            lock_workstation()

    def _on_close(self) -> None:
        # Persist current UI values + enabled state
        self.cfg = self._read_settings_from_ui()
        save_config(self.cfg)
        if self._poll_job is not None:
            try:
                self.root.after_cancel(self._poll_job)
            except tk.TclError:
                pass
        if self.warning.visible:
            self.warning.close()
        self.root.destroy()

    def run(self) -> None:
        # Center main window
        self.root.update_idletasks()
        need_w = max(460, self.root.winfo_reqwidth())
        need_h = max(520, self.root.winfo_reqheight() + 20)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{need_w}x{need_h}+{(sw - need_w) // 2}+{(sh - need_h) // 2}")
        self.root.mainloop()


def main() -> int:
    if sys.platform != "win32":
        print("Ứng dụng chỉ hỗ trợ Windows.", file=sys.stderr)
        return 1
    AutoLockApp().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
