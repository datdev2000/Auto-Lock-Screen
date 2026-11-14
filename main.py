"""
Auto Lock Screen — entry point.
"""

from __future__ import annotations

import argparse
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Auto Lock Screen")
    p.add_argument(
        "--hidden",
        action="store_true",
        help="Chạy ẩn trên khay hệ thống.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if sys.platform != "win32":
        print("Ứng dụng chỉ hỗ trợ Windows.", file=sys.stderr)
        return 1

    from autolock.instance import (
        acquire_single_instance,
        focus_existing_via_title,
        release_single_instance,
    )

    if not acquire_single_instance():
        # Đã có instance → đưa cửa sổ cũ lên, không tạo thêm icon khay
        focus_existing_via_title("Auto Lock Screen")
        return 0

    try:
        from autolock.app import AutoLockApp

        args = parse_args(argv)
        AutoLockApp(start_hidden=bool(args.hidden)).run()
    finally:
        release_single_instance()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
