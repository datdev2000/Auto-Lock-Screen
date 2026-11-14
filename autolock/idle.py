"""Theo dõi idle, phát hiện màn hình khóa, và thực hiện Lock / Sleep / Shutdown."""

from __future__ import annotations

import ctypes
import subprocess
from ctypes import wintypes

ACTION_LOCK = "lock"
ACTION_SLEEP = "sleep"
ACTION_SHUTDOWN = "shutdown"
ACTIONS = (ACTION_LOCK, ACTION_SLEEP, ACTION_SHUTDOWN)

ACTION_LABELS = {
    ACTION_LOCK: "Khóa màn hình",
    ACTION_SLEEP: "Sleep (ngủ)",
    ACTION_SHUTDOWN: "Tắt máy",
}


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


def is_workstation_locked() -> bool:
    """
    True khi Windows đang ở màn hình khóa (Win+L).
    Khi khóa, GetLastInputInfo vẫn tăng — app phải tạm dừng đếm.
    """
    DESKTOP_SWITCHDESKTOP = 0x0100
    hdesk = user32.OpenDesktopW("Default", 0, False, DESKTOP_SWITCHDESKTOP)
    if not hdesk:
        return True
    try:
        # SwitchDesktop thất bại khi session đang bị lock
        return not bool(user32.SwitchDesktop(hdesk))
    finally:
        user32.CloseDesktop(hdesk)


def lock_workstation() -> None:
    user32.LockWorkStation()


def sleep_workstation() -> None:
    # SetSuspendState(Hibernate=False, ForceCritical=True, DisableWakeEvent=False)
    ctypes.windll.powrprof.SetSuspendState(False, True, False)


def shutdown_workstation() -> None:
    # shutdown.exe không cần đặc quyền phức tạp như ExitWindowsEx
    subprocess.Popen(
        ["shutdown", "/s", "/t", "0"],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def perform_action(action: str) -> None:
    action = (action or ACTION_LOCK).lower()
    if action == ACTION_SLEEP:
        sleep_workstation()
    elif action == ACTION_SHUTDOWN:
        shutdown_workstation()
    else:
        lock_workstation()
