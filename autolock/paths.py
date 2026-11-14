"""Đường dẫn cố định cho dữ liệu & resource của app."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "AutoLockScreen"
AUTHOR = "datdev2000"
GITHUB_URL = "https://github.com/datdev2000/Auto-Lock-Screen"


def data_dir() -> Path:
    """Thư mục dữ liệu cố định: C:\\ProgramData\\AutoLockScreen\\"""
    root = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
    path = root / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_path() -> Path:
    return data_dir() / "config.json"


def resource_dir() -> Path:
    """Asset đóng gói (PyInstaller _MEIPASS) hoặc thư mục project."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def icon_ico() -> Path:
    return resource_dir() / "assets" / "lock.ico"


def icon_png() -> Path:
    return resource_dir() / "assets" / "lock.png"


def install_dir() -> Path:
    """Thư mục chứa .exe (hoặc script) — không dùng để lưu config."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent
