"""UI chính Auto Lock Screen — layout gọn."""

from __future__ import annotations

import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox

try:
    import pystray
except ImportError:
    pystray = None  # type: ignore

try:
    from PIL import ImageTk
except ImportError:
    ImageTk = None  # type: ignore

from .config import clear_app_data, load_config, save_config
from .icons import load_lock_image, make_lock_image
from .idle import (
    ACTION_LABELS,
    ACTION_LOCK,
    ACTION_SHUTDOWN,
    ACTION_SLEEP,
    ACTIONS,
    get_idle_seconds,
    is_workstation_locked,
    perform_action,
)
from .paths import AUTHOR, GITHUB_URL, data_dir
from .power import (
    format_timeout,
    read_sleep_timeouts,
    set_sleep_minutes,
    set_sleep_never,
)
from .startup import set_start_with_windows
from .warning import WarningOverlay


class AutoLockApp:
    POLL_MS = 500

    def __init__(self, *, start_hidden: bool = False) -> None:
        self.cfg = load_config()
        self._start_hidden = start_hidden
        self.root = tk.Tk()
        self.root.title("Auto Lock Screen")
        self.root.minsize(440, 480)
        self.root.configure(bg="#12141a")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close_window)
        self._apply_window_icon()

        self.warning = WarningOverlay(self)
        self._poll_job: str | None = None
        self._enabled = bool(self.cfg.get("enabled", False))
        self._tray = None
        self._tray_thread: threading.Thread | None = None
        self._exiting = False
        self._updating_startup_ui = False
        self._was_locked = False

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

    def _apply_window_icon(self) -> None:
        """Cùng ảnh ổ khóa với khay — chỉ dùng iconphoto (tránh iconbitmap lệch)."""
        if ImageTk is None:
            return
        try:
            img32 = load_lock_image(32) or make_lock_image(32)
            img64 = load_lock_image(64) or make_lock_image(64)
            self._tk_icon_32 = ImageTk.PhotoImage(img32)
            self._tk_icon_64 = ImageTk.PhotoImage(img64)
            self.root.iconphoto(True, self._tk_icon_64, self._tk_icon_32)
        except Exception:
            pass

    def _build_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        bg, card, fg, muted, accent = "#12141a", "#1a1d23", "#e8eaed", "#9aa3b2", "#4c8bf5"
        btn_bg, btn_hover = "#2d3340", "#3d4555"
        style.configure(".", background=bg, foreground=fg, font=("Segoe UI", 9))
        style.configure("TFrame", background=bg)
        style.configure("Card.TFrame", background=card)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("Card.TLabel", background=card, foreground=fg)
        style.configure("Muted.TLabel", background=bg, foreground=muted)
        style.configure("CardMuted.TLabel", background=card, foreground=muted)
        style.configure("Title.TLabel", background=bg, foreground=fg, font=("Segoe UI", 15, "bold"))
        style.configure("Status.TLabel", background=card, foreground=accent, font=("Segoe UI", 10, "bold"))
        style.configure("Link.TLabel", background=bg, foreground=accent, font=("Segoe UI", 8, "underline"))
        style.configure(
            "TButton",
            font=("Segoe UI", 9),
            padding=(10, 5),
            background=btn_bg,
            foreground=fg,
            bordercolor="#3d4555",
            lightcolor=btn_bg,
            darkcolor=btn_bg,
            focuscolor=btn_bg,
        )
        style.map(
            "TButton",
            background=[("active", btn_hover), ("pressed", "#252a33"), ("disabled", "#252a33")],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff"), ("disabled", "#888888")],
        )
        style.configure(
            "Accent.TButton",
            background=accent,
            foreground="#ffffff",
            font=("Segoe UI", 9, "bold"),
            padding=(12, 6),
            bordercolor=accent,
            lightcolor=accent,
            darkcolor=accent,
            focuscolor=accent,
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#3a74d8"), ("pressed", "#2f63bc"), ("disabled", "#3a4050")],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff"), ("disabled", "#888888")],
        )
        style.configure(
            "Danger.TButton",
            background="#5a2a2a",
            foreground="#ffb4b4",
            font=("Segoe UI", 9),
            padding=(10, 5),
            bordercolor="#7a3a3a",
            lightcolor="#5a2a2a",
            darkcolor="#5a2a2a",
            focuscolor="#5a2a2a",
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#7a3a3a"), ("pressed", "#4a2020")],
            foreground=[("active", "#ffffff"), ("pressed", "#ffffff")],
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
        style.configure("TRadiobutton", background=card, foreground=fg)
        style.map("TRadiobutton", background=[("active", card)])

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=(16, 12, 16, 10))
        outer.pack(fill="both", expand=True)

        # Footer full ngang, dính đáy
        footer = ttk.Frame(outer)
        footer.pack(side="bottom", fill="x", pady=(8, 0))

        actions = ttk.Frame(footer)
        actions.pack(fill="x")
        ttk.Button(actions, text="Lưu", command=self.save_settings).pack(side="left")
        ttk.Button(
            actions, text="Gỡ cài đặt", style="Danger.TButton", command=self.uninstall_app
        ).pack(side="right")

        about = ttk.Frame(footer)
        about.pack(fill="x", pady=(10, 0))
        author = ttk.Label(
            about,
            text=f"Author: {AUTHOR}  ·  GitHub",
            style="Link.TLabel",
            cursor="hand2",
        )
        author.pack()
        author.bind("<Button-1>", lambda e: webbrowser.open(GITHUB_URL))
        self._footer = footer

        # Cuộn bằng chuột (ẩn thanh) — nội dung full ngang theo cửa sổ
        scroll_wrap = ttk.Frame(outer)
        scroll_wrap.pack(fill="both", expand=True)

        self._scroll_canvas = tk.Canvas(
            scroll_wrap, bg="#12141a", highlightthickness=0, bd=0
        )
        self._scroll_canvas.pack(fill="both", expand=True)

        body = ttk.Frame(self._scroll_canvas)
        self._body_window = self._scroll_canvas.create_window(
            (0, 0), window=body, anchor="nw"
        )

        def _on_body_configure(_event=None) -> None:
            self._scroll_canvas.configure(scrollregion=self._scroll_canvas.bbox("all"))

        def _on_canvas_configure(event) -> None:
            # Full ngang: body = đúng bề rộng canvas
            w = max(1, int(event.width))
            self._scroll_canvas.itemconfigure(self._body_window, width=w)
            self._scroll_canvas.coords(self._body_window, 0, 0)
            wrap = max(280, w - 40)
            try:
                self._subtitle_label.configure(wraplength=wrap)
                self._sleep_hint_label.configure(wraplength=wrap)
                self.sleep_status_label.configure(wraplength=wrap)
                self._data_path_label.configure(wraplength=wrap)
            except Exception:
                pass

        def _on_mousewheel(event) -> None:
            bbox = self._scroll_canvas.bbox("all")
            if not bbox:
                return
            content_h = bbox[3] - bbox[1]
            if content_h <= self._scroll_canvas.winfo_height():
                return
            self._scroll_canvas.yview_scroll(int(-event.delta / 120), "units")

        def _bind_wheel(_event=None) -> None:
            self._scroll_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_wheel(_event=None) -> None:
            self._scroll_canvas.unbind_all("<MouseWheel>")

        body.bind("<Configure>", _on_body_configure)
        self._scroll_canvas.bind("<Configure>", _on_canvas_configure)
        self._scroll_canvas.bind("<Enter>", _bind_wheel)
        self._scroll_canvas.bind("<Leave>", _unbind_wheel)
        body.bind("<Enter>", _bind_wheel)
        body.bind("<Leave>", _unbind_wheel)
        self._unbind_wheel = _unbind_wheel

        ttk.Label(body, text="Auto Lock Screen", style="Title.TLabel").pack(anchor="w")
        self._subtitle_label = ttk.Label(
            body,
            text="Theo dõi chuột & bàn phím — cảnh báo rồi khóa khi không hoạt động.",
            style="Muted.TLabel",
            wraplength=480,
        )
        self._subtitle_label.pack(anchor="w", pady=(2, 8))

        status = ttk.Frame(body, style="Card.TFrame", padding=12)
        status.pack(fill="x", pady=(0, 6))
        head = ttk.Frame(status, style="Card.TFrame")
        head.pack(fill="x")
        left = ttk.Frame(head, style="Card.TFrame")
        left.pack(side="left", fill="x", expand=True)
        ttk.Label(left, text="Trạng thái", style="Card.TLabel").pack(anchor="w")
        self.status_label = ttk.Label(left, text="Đã tắt", style="Status.TLabel")
        self.status_label.pack(anchor="w")
        self.toggle_btn = ttk.Button(
            head, text="Bật theo dõi", style="Accent.TButton", command=self.toggle_monitoring
        )
        self.toggle_btn.pack(side="right")
        self.idle_now_label = ttk.Label(status, text="Idle: —", style="CardMuted.TLabel")
        self.idle_now_label.pack(anchor="w", pady=(4, 0))
        self.countdown_hint = ttk.Label(status, text="", style="CardMuted.TLabel")
        self.countdown_hint.pack(anchor="w")

        # Timers — mỗi mục một dòng; scale cao bằng spinbox
        timers = ttk.Frame(body, style="Card.TFrame", padding=12)
        timers.pack(fill="x", pady=(0, 6))
        self.idle_var = tk.IntVar(value=int(self.cfg["idle_seconds"]))
        self.warn_var = tk.IntVar(value=int(self.cfg["warning_seconds"]))

        ttk.Label(timers, text="Chờ không hoạt động (giây)", style="Card.TLabel").pack(
            anchor="w"
        )
        self.idle_scale, self.idle_spin = self._make_scale_spin_row(
            timers,
            self.idle_var,
            from_=5,
            to_scale=600,
            to_spin=3600,
            on_scale=self._on_idle_scale,
            on_spin=self._on_idle_spin,
        )

        ttk.Label(timers, text="Chờ thông báo (giây)", style="Card.TLabel").pack(
            anchor="w", pady=(10, 0)
        )
        self.warn_scale, self.warn_spin = self._make_scale_spin_row(
            timers,
            self.warn_var,
            from_=1,
            to_scale=120,
            to_spin=600,
            on_scale=self._on_warn_scale,
            on_spin=self._on_warn_spin,
        )

        # Hành động khi hết giờ
        act = ttk.Frame(body, style="Card.TFrame", padding=12)
        act.pack(fill="x", pady=(0, 6))
        ttk.Label(act, text="Khi hết giờ sẽ", style="Card.TLabel").pack(anchor="w")
        self.action_var = tk.StringVar(
            value=str(self.cfg.get("action", ACTION_LOCK))
        )
        for key in ACTIONS:
            ttk.Radiobutton(
                act,
                text=ACTION_LABELS[key],
                value=key,
                variable=self.action_var,
                command=self._on_action_changed,
            ).pack(anchor="w", pady=(4, 0))
        self._sleep_hint_label = ttk.Label(
            act,
            text="Nếu Windows Sleep sớm hơn app thì Windows ngủ trước. "
            "Nên tắt Sleep Windows hoặc đặt timeout app ngắn hơn.",
            style="CardMuted.TLabel",
            wraplength=480,
        )
        self._sleep_hint_label.pack(anchor="w", pady=(6, 0))

        sleep_row = ttk.Frame(act, style="Card.TFrame")
        sleep_row.pack(fill="x", pady=(8, 0))
        self.disable_sleep_var = tk.BooleanVar(
            value=bool(self.cfg.get("disable_windows_sleep", False))
        )
        ttk.Checkbutton(
            sleep_row,
            text="Tắt Sleep tự động của Windows (Never)",
            variable=self.disable_sleep_var,
            command=self._on_disable_sleep_changed,
        ).pack(side="left", anchor="w")
        ttk.Button(
            sleep_row,
            text="Áp dụng ngay",
            command=self._apply_disable_sleep_clicked,
        ).pack(side="left", padx=(12, 0))
        self.sleep_status_label = ttk.Label(
            act, text="", style="CardMuted.TLabel", wraplength=480
        )
        self.sleep_status_label.pack(anchor="w", pady=(4, 0))
        self._refresh_sleep_status()

        opt = ttk.Frame(body, style="Card.TFrame", padding=12)
        opt.pack(fill="x", pady=(0, 6))
        ttk.Label(opt, text="Tuỳ chọn", style="Card.TLabel").pack(anchor="w")
        self.start_win_var = tk.BooleanVar(
            value=bool(self.cfg.get("start_with_windows", False))
        )
        self.start_hidden_var = tk.BooleanVar(
            value=bool(self.cfg.get("start_hidden", False))
        )
        ttk.Checkbutton(
            opt,
            text="Khởi động cùng Windows (mở cửa sổ)",
            variable=self.start_win_var,
            command=self._on_startup_changed,
        ).pack(anchor="w", pady=(6, 0))
        ttk.Checkbutton(
            opt,
            text="Khởi động ẩn trên khay",
            variable=self.start_hidden_var,
            command=self._on_startup_changed,
        ).pack(anchor="w", pady=(2, 0))
        self._data_path_label = ttk.Label(
            opt,
            text=f"Dữ liệu: {data_dir()}  ·  X → ẩn khay",
            style="CardMuted.TLabel",
            wraplength=480,
        )
        self._data_path_label.pack(anchor="w", pady=(6, 0))

    def _make_scale_spin_row(
        self,
        parent,
        var: tk.IntVar,
        *,
        from_: int,
        to_scale: int,
        to_spin: int,
        on_scale,
        on_spin,
    ):
        """Một dòng: thanh kéo + ô số căn giữa cùng hàng."""
        row = tk.Frame(parent, bg="#1a1d23")
        row.pack(fill="x", pady=(6, 0))
        row.columnconfigure(0, weight=1)

        scale = tk.Scale(
            row,
            from_=from_,
            to=to_scale,
            orient="horizontal",
            showvalue=0,
            resolution=1,
            width=14,
            sliderlength=16,
            bd=0,
            highlightthickness=0,
            relief="flat",
            bg="#1a1d23",
            fg="#e8eaed",
            troughcolor="#252a33",
            activebackground="#4c8bf5",
            command=on_scale,
        )
        scale.set(var.get())
        scale.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        spin = tk.Spinbox(
            row,
            from_=from_,
            to=to_spin,
            width=6,
            textvariable=var,
            command=on_spin,
            font=("Segoe UI", 10),
            bg="#252a33",
            fg="#e8eaed",
            buttonbackground="#2d3340",
            relief="flat",
            insertbackground="#e8eaed",
            justify="center",
        )
        spin.grid(row=0, column=1, sticky="e")
        spin.bind("<FocusOut>", lambda e: on_spin())
        spin.bind("<Return>", lambda e: on_spin())
        return scale, spin

    # ----- tray -----

    def _setup_tray(self) -> None:
        if self._tray is not None:
            return  # không tạo trùng icon
        menu = pystray.Menu(
            pystray.MenuItem("Hiện cửa sổ", self._tray_show_window),
            pystray.MenuItem(
                "Bật theo dõi",
                self._tray_toggle_monitoring,
                checked=lambda item: self._enabled,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Thoát", self._tray_exit),
        )
        # Cùng ảnh với cửa sổ
        tray_img = load_lock_image(64) or make_lock_image(64)
        self._tray = pystray.Icon("AutoLockScreen", tray_img, "Auto Lock Screen", menu)
        self._tray_thread = threading.Thread(target=self._tray.run, name="tray", daemon=True)
        self._tray_thread.start()

    def _tray_show_window(self, icon=None, item=None) -> None:
        self.root.after(0, self.show_window)

    def _tray_toggle_monitoring(self, icon=None, item=None) -> None:
        self.root.after(0, self.toggle_monitoring)

    def _tray_exit(self, icon=None, item=None) -> None:
        self.root.after(0, self.quit_app)

    def show_window(self) -> None:
        try:
            state = self.root.state()
        except tk.TclError:
            return
        if state == "withdrawn":
            self.root.deiconify()
        elif state == "iconic":
            self.root.deiconify()
        self.root.lift()

    def hide_to_tray(self) -> None:
        if self._tray is None:
            self.root.iconify()
            return
        self.root.withdraw()

    # ----- settings -----

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
        action = str(self.cfg.get("action", ACTION_LOCK))
        if action not in ACTIONS:
            action = ACTION_LOCK
        self.action_var.set(action)
        self.disable_sleep_var.set(bool(self.cfg.get("disable_windows_sleep", False)))
        self.start_win_var.set(bool(self.cfg.get("start_with_windows", False)))
        self.start_hidden_var.set(bool(self.cfg.get("start_hidden", False)))
        self._refresh_toggle_button()
        self._refresh_sleep_status()

    def _read_settings_from_ui(self) -> dict:
        self._on_idle_spin()
        self._on_warn_spin()
        action = str(self.action_var.get() or ACTION_LOCK)
        if action not in ACTIONS:
            action = ACTION_LOCK
        return {
            "idle_seconds": self._clamp_idle(int(self.idle_var.get())),
            "warning_seconds": self._clamp_warn(int(self.warn_var.get())),
            "enabled": self._enabled,
            "start_with_windows": bool(self.start_win_var.get()),
            "start_hidden": bool(self.start_hidden_var.get()),
            "action": action,
            "disable_windows_sleep": bool(self.disable_sleep_var.get()),
            "saved_sleep_ac": self.cfg.get("saved_sleep_ac"),
            "saved_sleep_dc": self.cfg.get("saved_sleep_dc"),
        }

    def _on_action_changed(self) -> None:
        self.cfg = self._read_settings_from_ui()
        save_config(self.cfg)

    def _refresh_sleep_status(self) -> None:
        try:
            cur = read_sleep_timeouts()
            text = (
                f"Sleep Windows hiện tại — AC: {format_timeout(cur.get('ac'))}, "
                f"Pin: {format_timeout(cur.get('dc'))}"
            )
            if self.disable_sleep_var.get():
                text += "  ·  Đã chọn tắt Sleep (Never)"
            self.sleep_status_label.configure(text=text)
        except Exception:
            self.sleep_status_label.configure(text="Không đọc được Sleep Windows.")

    def _apply_disable_windows_sleep(self, enabled: bool) -> bool:
        """
        enabled=True: lưu timeout cũ (nếu chưa có) rồi set Never.
        enabled=False: khôi phục timeout đã lưu.
        """
        try:
            if enabled:
                cur = read_sleep_timeouts()
                # Chỉ lưu lần đầu khi chưa có bản sao
                if self.cfg.get("saved_sleep_ac") is None and self.cfg.get("saved_sleep_dc") is None:
                    self.cfg["saved_sleep_ac"] = cur.get("ac")
                    self.cfg["saved_sleep_dc"] = cur.get("dc")
                set_sleep_never()
            else:
                ac = self.cfg.get("saved_sleep_ac")
                dc = self.cfg.get("saved_sleep_dc")
                if ac is not None or dc is not None:
                    set_sleep_minutes(
                        int(ac) if ac is not None else None,
                        int(dc) if dc is not None else None,
                    )
                self.cfg["saved_sleep_ac"] = None
                self.cfg["saved_sleep_dc"] = None
            self.cfg["disable_windows_sleep"] = enabled
            save_config(self.cfg)
            self._refresh_sleep_status()
            return True
        except Exception as exc:
            messagebox.showerror(
                "Sleep Windows",
                f"Không đổi được Sleep:\n{exc}",
                parent=self.root,
            )
            return False

    def _on_disable_sleep_changed(self) -> None:
        want = bool(self.disable_sleep_var.get())
        if not self._apply_disable_windows_sleep(want):
            self.disable_sleep_var.set(not want)

    def _apply_disable_sleep_clicked(self) -> None:
        want = bool(self.disable_sleep_var.get())
        if self._apply_disable_windows_sleep(want):
            state = "đã tắt Sleep (Never)" if want else "đã khôi phục Sleep cũ"
            messagebox.showinfo("Sleep Windows", f"OK — {state}.", parent=self.root)

    def _apply_startup_registration(self) -> None:
        """Hai checkbox độc lập; chỉ cần một cái bật là đăng ký khởi động."""
        start_win = bool(self.start_win_var.get())
        start_hidden = bool(self.start_hidden_var.get())
        enabled = start_win or start_hidden
        # Ẩn ưu tiên nếu đang bật; không ép checkbox kia
        set_start_with_windows(enabled, hidden=start_hidden)

    def _on_startup_changed(self) -> None:
        if self._updating_startup_ui:
            return
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
        messagebox.showinfo("Đã lưu", f"Đã lưu vào:\n{data_dir()}", parent=self.root)

    def uninstall_app(self) -> None:
        if not messagebox.askyesno(
            "Gỡ cài đặt",
            "Xóa toàn bộ dữ liệu app (config, …),\n"
            "hủy khởi động cùng Windows, rồi thoát?\n\n"
            f"Thư mục: {data_dir()}\n\n"
            "File .exe bạn tự xóa sau nếu muốn.",
            parent=self.root,
        ):
            return
        try:
            set_start_with_windows(False)
        except OSError:
            pass
        # Khôi phục Sleep Windows nếu app từng tắt
        try:
            if self.cfg.get("disable_windows_sleep") or self.disable_sleep_var.get():
                ac = self.cfg.get("saved_sleep_ac")
                dc = self.cfg.get("saved_sleep_dc")
                if ac is not None or dc is not None:
                    set_sleep_minutes(
                        int(ac) if ac is not None else None,
                        int(dc) if dc is not None else None,
                    )
        except Exception:
            pass
        cleared = clear_app_data()
        messagebox.showinfo(
            "Đã gỡ",
            f"Đã xóa dữ liệu:\n{cleared}\n\nỨng dụng sẽ thoát.",
            parent=self.root,
        )
        # Thoát không ghi lại config
        self._exiting = True
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

    def _refresh_toggle_button(self) -> None:
        self.toggle_btn.configure(text="Tắt theo dõi" if self._enabled else "Bật theo dõi")

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

        # Máy đã khóa → tạm dừng đếm, đóng cảnh báo (tránh lặp Lock/Sleep khi đang lock)
        try:
            locked = is_workstation_locked()
        except Exception:
            locked = False

        if locked:
            self._was_locked = True
            if self.warning.visible:
                self.warning.close()
            try:
                self.status_label.configure(text="Máy đang khóa — tạm dừng")
                self.idle_now_label.configure(text="Idle: —")
                self.countdown_hint.configure(text="Mở khóa xong sẽ đếm lại từ đầu")
            except tk.TclError:
                return
            self._schedule_poll()
            return

        # Vừa mở khóa → reset trạng thái, đếm lại từ idle hiện tại
        if self._was_locked:
            self._was_locked = False
            if self.warning.visible:
                self.warning.close()

        idle = get_idle_seconds()
        idle_limit = self._clamp_idle(int(self.idle_var.get() or self.cfg["idle_seconds"]))
        warn_secs = self._clamp_warn(int(self.warn_var.get() or self.cfg["warning_seconds"]))
        action = str(self.action_var.get() or self.cfg.get("action") or ACTION_LOCK)
        try:
            self.idle_now_label.configure(text=f"Idle: {idle:.1f}s")
        except tk.TclError:
            return

        if not self.warning.visible:
            remaining = max(0, idle_limit - idle)
            if idle >= idle_limit:
                self.warning.show(warn_secs, action=action)
                self.status_label.configure(text="Đang cảnh báo…")
            elif remaining > 0:
                self.countdown_hint.configure(text=f"Còn ~{remaining:.0f}s tới cảnh báo")
                self.status_label.configure(text="Đang theo dõi")
            else:
                self.countdown_hint.configure(text="")
        self._schedule_poll()

    def _update_status_labels(self) -> None:
        if self._enabled:
            self.status_label.configure(text="Đang theo dõi")
            self.countdown_hint.configure(text="")
        else:
            self.status_label.configure(text="Đã tắt")
            self.idle_now_label.configure(text="Idle: —")
            self.countdown_hint.configure(text="")

    def on_warning_cancelled(self) -> None:
        if self._enabled:
            self.status_label.configure(text="Đang theo dõi")
            self.countdown_hint.configure(text="Đã hủy — chờ idle lại")

    def on_action_done(self, action: str) -> None:
        if self._enabled:
            label = ACTION_LABELS.get(action, action)
            self.status_label.configure(text=f"Đã: {label}")
            self.countdown_hint.configure(text="")

    def _test_lock(self) -> None:
        action = str(self.action_var.get() or ACTION_LOCK)
        label = ACTION_LABELS.get(action, action)
        if messagebox.askyesno("Thử ngay", f"Thực hiện «{label}» ngay?", parent=self.root):
            perform_action(action)

    def _on_close_window(self) -> None:
        self.cfg = self._read_settings_from_ui()
        save_config(self.cfg)
        self.hide_to_tray()

    def quit_app(self) -> None:
        if self._exiting:
            return
        self._exiting = True
        try:
            self._unbind_wheel()
        except Exception:
            pass
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
        w, h = 520, 640
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.root.minsize(420, 480)
        # Ép layout canvas sau khi có kích thước thật (tránh body hẹp / trống)
        self.root.update_idletasks()
        try:
            cw = max(1, self._scroll_canvas.winfo_width())
            self._scroll_canvas.itemconfigure(self._body_window, width=cw)
            self._scroll_canvas.coords(self._body_window, 0, 0)
            self._scroll_canvas.yview_moveto(0)
            self._scroll_canvas.configure(scrollregion=self._scroll_canvas.bbox("all"))
        except tk.TclError:
            pass
        if self._start_hidden:
            self.root.withdraw()
        self.root.mainloop()
