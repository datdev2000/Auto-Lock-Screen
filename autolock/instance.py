"""Đảm bảo chỉ một instance app chạy (tránh nhiều icon khay)."""

from __future__ import annotations

import ctypes
import sys

MUTEX_NAME = "Local\\AutoLockScreen_SingleInstance"
ERROR_ALREADY_EXISTS = 183

_mutex_handle = None


def acquire_single_instance() -> bool:
    """
    True = được phép chạy (instance đầu).
    False = đã có instance khác → nên thoát.
    """
    global _mutex_handle
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        return True  # không chặn nếu tạo mutex lỗi
    _mutex_handle = handle
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        return False
    return True


def release_single_instance() -> None:
    global _mutex_handle
    if _mutex_handle:
        ctypes.windll.kernel32.CloseHandle(_mutex_handle)
        _mutex_handle = None


def focus_existing_via_title(title: str = "Auto Lock Screen") -> None:
    """Thử đưa cửa sổ instance đang chạy lên trước."""
    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW(None, title)
    if hwnd:
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
