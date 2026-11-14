"""Đăng ký / hủy khởi động cùng Windows (HKCU Run)."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import winreg
except ImportError:
    winreg = None  # type: ignore

STARTUP_REG_NAME = "AutoLockScreen"
STARTUP_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def launch_command(*, hidden: bool = False) -> str:
    if getattr(sys, "frozen", False):
        base = f'"{Path(sys.executable).resolve()}"'
    else:
        py = Path(sys.executable).resolve()
        pythonw = py.with_name("pythonw.exe")
        runner = pythonw if pythonw.exists() else py
        script = Path(__file__).resolve().parent.parent / "main.py"
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
