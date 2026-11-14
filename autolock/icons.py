"""Icon ổ khóa dùng chung cho cửa sổ, khay và .exe."""

from __future__ import annotations

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore

from .paths import icon_png


def make_lock_image(size: int = 64):
    """Ổ khóa đóng — cùng thiết kế cho cửa sổ + khay."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size
    pad = max(1, s // 32)
    d.rounded_rectangle(
        (pad, pad, s - 1 - pad, s - 1 - pad),
        radius=max(4, s // 5),
        fill=(76, 139, 245, 255),
    )
    # Thân khóa
    bx0, by0 = int(s * 0.28), int(s * 0.48)
    bx1, by1 = int(s * 0.72), int(s * 0.80)
    d.rounded_rectangle(
        (bx0, by0, bx1, by1),
        radius=max(2, s // 16),
        fill=(255, 255, 255, 255),
    )
    # Lỗ khóa
    cx, cy = s // 2, int(s * 0.58)
    r = max(2, s // 18)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(76, 139, 245, 255))
    d.rectangle(
        (cx - max(1, r // 2), cy, cx + max(1, r // 2), cy + int(s * 0.12)),
        fill=(76, 139, 245, 255),
    )
    # Móc khóa đóng (cung nửa trên, hai chân cắm vào thân)
    sw = max(2, s // 12)
    ax0, ay0 = int(s * 0.34), int(s * 0.22)
    ax1, ay1 = int(s * 0.66), int(s * 0.58)
    d.arc((ax0, ay0, ax1, ay1), start=200, end=340, fill=(255, 255, 255, 255), width=sw)
    # Hai chân móc nối xuống thân
    d.line(
        [(int(s * 0.36), int(s * 0.40)), (int(s * 0.36), int(s * 0.50))],
        fill=(255, 255, 255, 255),
        width=sw,
    )
    d.line(
        [(int(s * 0.64), int(s * 0.40)), (int(s * 0.64), int(s * 0.50))],
        fill=(255, 255, 255, 255),
        width=sw,
    )
    return img


def load_lock_image(size: int = 64):
    if Image is None:
        return None
    # Luôn ưu tiên vẽ lại để cửa sổ/khay giống nhau (không lệch file cũ)
    return make_lock_image(size)
