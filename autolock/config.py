"""Đọc/ghi cấu hình trong ProgramData."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .paths import config_path, data_dir

DEFAULT_CONFIG = {
    "idle_seconds": 60,
    "warning_seconds": 15,
    "enabled": False,
    "start_with_windows": False,
    "start_hidden": False,
    "action": "lock",  # lock | sleep | shutdown
    "disable_windows_sleep": False,
    # Lưu giá trị Sleep cũ (phút) để khôi phục khi bỏ tắt
    "saved_sleep_ac": None,
    "saved_sleep_dc": None,
}


def load_config() -> dict:
    path = config_path()
    # Migrate từ config cũ cạnh .exe (nếu còn)
    _maybe_migrate_legacy(path)
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            cfg = dict(DEFAULT_CONFIG)
            cfg.update(data)
            return cfg
        except (json.JSONDecodeError, OSError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def clear_app_data() -> Path:
    """Xóa toàn bộ thư mục dữ liệu app. Trả về path đã xóa."""
    root = data_dir()
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)
    return root


def _maybe_migrate_legacy(new_path: Path) -> None:
    if new_path.exists():
        return
    try:
        from .paths import install_dir

        legacy = install_dir() / "config.json"
        if legacy.exists():
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(legacy, new_path)
    except OSError:
        pass
