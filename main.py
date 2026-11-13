"""
AutoLockScreen — khóa màn hình khi không dùng chuột/bàn phím.
Windows only. Hỗ trợ khay hệ thống + khởi động cùng Windows.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import ctypes
from ctypes import wintypes
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import winreg
except ImportError:  # non-Windows
    winreg = None  # type: ignore

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None  # type: ignore
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = _app_dir()
CONFIG_PATH = APP_DIR / "config.json"
STARTUP_REG_NAME = "AutoLockScreen"
STARTUP_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

DEFAULT_CONFIG = {
    "idle_seconds": 60,
    "warning_seconds": 15,
    "enabled": False,
    "start_with_windows": False,
    "start_hidden": False,
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


# ---------- Launch / startup ----------

def launch_command(*, hidden: bool = False) -> str:
    """Lệnh dùng để đăng ký khởi động cùng Windows."""
    if getattr(sys, "frozen", False):
        base = f'"{Path(sys.executable).resolve()}"'
    else:
        py = Path(sys.executable).resolve()
        pythonw = py.with_name("pythonw.exe")
        runner = pythonw if pythonw.exists() else py
        script = Path(__file__).resolve()
        base = f'"{runner}" "{script}"'
    if hidden:
        return f"{base} --hidden"
    return base


def is_start_with_windows() -> bool:
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_PATH) as key:
            winreg.QueryValueEx(key, STARTUP_REG_NAME)
            return True
    except OSError:
        return False


def set_start_with_windows(enabled: bool, *, hidden: bool = False) -> None:
    if winreg is None:
        raise RuntimeError("Chỉ hỗ trợ Windows.")
    if enabled:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, STARTUP_REG_PATH, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(
                key, STARTUP_REG_NAME, 0, winreg.REG_SZ, launch_command(hidden=hidden)
            )
    else:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, STARTUP_REG_PATH, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, STARTUP_REG_NAME)
        except FileNotFoundError:
            pass


def make_tray_image():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((4, 4, 60, 60), radius=14, fill=(76, 139, 245, 255))
    draw.rectangle((18, 22, 46, 42), outline=(255, 255, 255, 255), width=3)
    draw.rectangle((28, 42, 36, 48), fill=(255, 255, 255, 255))
    return img


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

        tk.Button(
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
        ).pack(side="right")

        self._update_text()
        self._schedule_tick()
        win.deiconify()
        win.lift()
        win.focus_force()

    def _update_text(self) -> None:
        if not self.visible:
            return
        self.countdown_label.config(text=f"Khóa sau {self._remaining} giây")

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

    def __init__(self, *, start_hidden: bool = False) -> None:
        self.cfg = load_config()
        self._start_hidden = start_hidden
        self.root = tk.Tk()
        self.root.title("Auto Lock Screen")
        self.root.minsize(420, 520)
        self.root.configure(bg="#12141a")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_window)

        self.warning = WarningOverlay(self)
        self._poll_job: str | None = None
        self._enabled = bool(self.cfg.get("enabled", False))
        self._tray: pystray.Icon | None = None
        self._tray_thread: threading.Thread | None = None
        self._exiting = False

        self._build_style()
        self._build_ui()
        self._sync_ui_from_config()
        self._update_status_labels()
        if self._enabled:
            self._start_monitoring()

        if pystray is not None:
            self._setup_tray()
        elif start_hidden:
            messagebox.showwarning(
                "Thiếu thư viện",
                "Cần cài pystray + pillow để chạy ẩn trên khay.\n"
                "pip install pystray pillow",
                parent=self.root,
            )

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
        style.configure("Horizontal.TScale", background=card, troughcolor="#252a33")
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
            wraplength=400,
        ).pack(anchor="w", padx=24, pady=(0, 12))

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
            idle_row, from_=5, to=600, orient="horizontal", command=self._on_idle_scale
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
            warn_row, from_=3, to=120, orient="horizontal", command=self._on_warn_scale
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

        # Options card
        opt = ttk.Frame(outer, style="Card.TFrame", padding=16)
        opt.pack(fill="x", padx=24, pady=8)
        ttk.Label(opt, text="Tuỳ chọn", style="Card.TLabel").pack(anchor="w")

        self.start_win_var = tk.BooleanVar(
            value=bool(self.cfg.get("start_with_windows", False)) or is_start_with_windows()
        )
        self.start_hidden_var = tk.BooleanVar(
            value=bool(self.cfg.get("start_hidden", False))
        )

        ttk.Checkbutton(
            opt,
            text="Khởi động cùng Windows (mở cửa sổ ứng dụng)",
            variable=self.start_win_var,
            command=self._on_startup_option_changed,
        ).pack(anchor="w", pady=(8, 2))
        ttk.Checkbutton(
            opt,
            text="Khởi động ẩn trên khay hệ thống (như UniKey)",
            variable=self.start_hidden_var,
            command=self._on_startup_option_changed,
        ).pack(anchor="w", pady=(2, 2))

        ttk.Label(
            opt,
            text="Đóng cửa sổ (X) → ẩn vào khay. Chuột phải icon khay → Hiện cửa sổ / Thoát.",
            style="CardMuted.TLabel",
            wraplength=380,
        ).pack(anchor="w", pady=(8, 0))

        actions = ttk.Frame(outer)
        actions.pack(fill="x", padx=24, pady=(8, 0))
        ttk.Button(actions, text="Lưu cài đặt", command=self.save_settings).pack(
            side="left"
        )
        ttk.Button(actions, text="Ẩn vào khay", command=self.hide_to_tray).pack(
            side="left", padx=(10, 0)
        )
        ttk.Button(actions, text="Thử khóa ngay", command=self._test_lock).pack(
            side="right"
        )

        ttk.Label(
            outer,
            text="Bấm «Bật theo dõi» để chạy. Di chuyển chuột khi có cảnh báo để hủy khóa.",
            style="Muted.TLabel",
            wraplength=400,
        ).pack(anchor="w", padx=24, pady=(12, 0))

    # ----- tray -----

    def _setup_tray(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem("Hiện cửa sổ", self._tray_show_window, default=True),
            pystray.MenuItem(
                "Bật theo dõi",
                self._tray_toggle_monitoring,
                checked=lambda item: self._enabled,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Thoát", self._tray_exit),
        )
        self._tray = pystray.Icon(
            "AutoLockScreen",
            make_tray_image(),
            "Auto Lock Screen",
            menu,
        )
        self._tray_thread = threading.Thread(
            target=self._tray.run, name="tray", daemon=True
        )
        self._tray_thread.start()

    def _tray_show_window(self, icon=None, item=None) -> None:
        self.root.after(0, self.show_window)

    def _tray_toggle_monitoring(self, icon=None, item=None) -> None:
        self.root.after(0, self.toggle_monitoring)

    def _tray_exit(self, icon=None, item=None) -> None:
        self.root.after(0, self.quit_app)

    def show_window(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_to_tray(self) -> None:
        if self._tray is None:
            messagebox.showinfo(
                "Khay hệ thống",
                "Chưa có icon khay (cần pystray + pillow).\n"
                "Ứng dụng sẽ thu nhỏ thay thế.",
                parent=self.root,
            )
            self.root.iconify()
            return
        self.root.withdraw()

    # ----- settings helpers -----

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
        self.start_win_var.set(
            bool(self.cfg.get("start_with_windows", False)) or is_start_with_windows()
        )
        self.start_hidden_var.set(bool(self.cfg.get("start_hidden", False)))
        self._refresh_toggle_button()

    def _read_settings_from_ui(self) -> dict:
        self._on_idle_spin()
        self._on_warn_spin()
        return {
            "idle_seconds": self._clamp_idle(int(self.idle_var.get())),
            "warning_seconds": self._clamp_warn(int(self.warn_var.get())),
            "enabled": self._enabled,
            "start_with_windows": bool(self.start_win_var.get()),
            "start_hidden": bool(self.start_hidden_var.get()),
        }

    def _apply_startup_registration(self) -> None:
        start = bool(self.start_win_var.get())
        hidden = bool(self.start_hidden_var.get())
        # Nếu chỉ chọn "khởi động ẩn" mà chưa tích Windows → vẫn đăng ký ẩn
        if hidden and not start:
            self.start_win_var.set(True)
            start = True
        set_start_with_windows(start, hidden=hidden)

    def _on_startup_option_changed(self) -> None:
        try:
            self._apply_startup_registration()
            self.cfg = self._read_settings_from_ui()
            save_config(self.cfg)
        except OSError as exc:
            messagebox.showerror(
                "Lỗi khởi động Windows",
                f"Không ghi được registry:\n{exc}",
                parent=self.root,
            )
            self.start_win_var.set(is_start_with_windows())

    def save_settings(self) -> None:
        try:
            self._apply_startup_registration()
        except OSError as exc:
            messagebox.showerror(
                "Lỗi khởi động Windows",
                f"Không ghi được registry:\n{exc}",
                parent=self.root,
            )
            return
        self.cfg = self._read_settings_from_ui()
        save_config(self.cfg)
        messagebox.showinfo("Đã lưu", "Cài đặt đã được lưu.", parent=self.root)

    def _refresh_toggle_button(self) -> None:
        self.toggle_btn.configure(
            text="Tắt theo dõi" if self._enabled else "Bật theo dõi"
        )

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
        idle_limit = self._clamp_idle(
            int(self.idle_var.get() or self.cfg["idle_seconds"])
        )
        warn_secs = self._clamp_warn(
            int(self.warn_var.get() or self.cfg["warning_seconds"])
        )

        try:
            self.idle_now_label.configure(text=f"Idle hiện tại: {idle:.1f} giây")
        except tk.TclError:
            return

        if self.warning.visible:
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

    def _on_close_window(self) -> None:
        # UniKey-style: X = ẩn vào khay, không thoát
        self.cfg = self._read_settings_from_ui()
        save_config(self.cfg)
        self.hide_to_tray()

    def quit_app(self) -> None:
        if self._exiting:
            return
        self._exiting = True
        self.cfg = self._read_settings_from_ui()
        save_config(self.cfg)
        if self._poll_job is not None:
            try:
                self.root.after_cancel(self._poll_job)
            except tk.TclError:
                pass
        if self.warning.visible:
            self.warning.close()
        if self._tray is not None:
            try:
                self._tray.stop()
            except Exception:
                pass
            self._tray = None
        self.root.destroy()

    def run(self) -> None:
        self.root.update_idletasks()
        need_w = max(480, self.root.winfo_reqwidth())
        need_h = max(620, self.root.winfo_reqheight() + 20)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(
            f"{need_w}x{need_h}+{(sw - need_w) // 2}+{(sh - need_h) // 2}"
        )
        if self._start_hidden:
            self.root.withdraw()
        self.root.mainloop()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Auto Lock Screen")
    p.add_argument(
        "--hidden",
        action="store_true",
        help="Chạy ẩn trên khay hệ thống (không hiện cửa sổ lúc mở).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if sys.platform != "win32":
        print("Ứng dụng chỉ hỗ trợ Windows.", file=sys.stderr)
        return 1
    args = parse_args(argv)
    AutoLockApp(start_hidden=bool(args.hidden)).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
