"""Đọc / tắt / khôi phục Sleep Windows qua powercfg."""

from __future__ import annotations

import re
import subprocess
from typing import Any


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _query_minutes(scheme_guid: str, subgroup: str, setting: str) -> dict[str, int | None]:
    """Trả về {ac, dc} phút từ powercfg /q."""
    r = _run(["powercfg", "/q", scheme_guid, subgroup, setting])
    text = r.stdout or ""
    ac = dc = None
    # Current AC/DC Power Setting Index: 0x0000012c  (seconds)
    for m in re.finditer(
        r"Current (AC|DC) Power Setting Index:\s*0x([0-9a-fA-F]+)", text
    ):
        kind, hexv = m.group(1), m.group(2)
        seconds = int(hexv, 16)
        minutes = seconds // 60
        if kind == "AC":
            ac = minutes
        else:
            dc = minutes
    return {"ac": ac, "dc": dc}


def get_active_scheme() -> str | None:
    r = _run(["powercfg", "/getactivescheme"])
    # Power Scheme GUID: xxxxxxxx-...  (Balanced)
    m = re.search(
        r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
        r.stdout or "",
    )
    return m.group(1) if m else None


def read_sleep_timeouts() -> dict[str, Any]:
    """
    Đọc timeout Sleep hiện tại (phút). 0 = Never.
    subgroup SUB_SLEEP, STANDBYIDLE
    """
    scheme = get_active_scheme()
    if not scheme:
        return {"scheme": None, "ac": None, "dc": None}
    vals = _query_minutes(scheme, "SUB_SLEEP", "STANDBYIDLE")
    return {"scheme": scheme, **vals}


def set_sleep_never() -> None:
    """Tắt Sleep khi cắm điện và dùng pin (Never)."""
    _run(["powercfg", "/change", "standby-timeout-ac", "0"])
    _run(["powercfg", "/change", "standby-timeout-dc", "0"])


def set_sleep_minutes(ac_minutes: int | None, dc_minutes: int | None) -> None:
    """Khôi phục Sleep (phút). None = bỏ qua."""
    if ac_minutes is not None:
        _run(["powercfg", "/change", "standby-timeout-ac", str(max(0, int(ac_minutes)))])
    if dc_minutes is not None:
        _run(["powercfg", "/change", "standby-timeout-dc", str(max(0, int(dc_minutes)))])


def format_timeout(minutes: int | None) -> str:
    if minutes is None:
        return "?"
    if minutes <= 0:
        return "Never"
    return f"{minutes} phút"
