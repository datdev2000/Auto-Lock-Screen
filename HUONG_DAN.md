# Auto Lock Screen — Hướng dẫn sử dụng

Ứng dụng theo dõi chuột và bàn phím. Nếu không có hoạt động trong một khoảng thời gian, sẽ hiện thông báo rồi khóa màn hình Windows.

---

## Chạy nhanh (khuyến nghị)

1. Mở thư mục `dist`
2. Double-click **`AutoLockScreen.exe`**
3. Không cần cài Python, không hiện cửa sổ CMD

Có thể tạo shortcut (chuột phải → Send to → Desktop) để mở từ Desktop.

---

## Cách dùng

1. Mở ứng dụng
2. Chỉnh hai tham số:
   - **Thời gian chờ (không hoạt động):** sau bao nhiêu giây không dùng chuột/phím thì hiện thông báo
   - **Thời gian chờ thông báo:** đếm ngược trên thông báo trước khi khóa
3. Bấm **Bật theo dõi**
4. Trạng thái chuyển thành **Đang theo dõi**

### Khi đang cảnh báo

- Di chuyển chuột, nhấn phím, hoặc bấm **Hủy khóa** → hủy, không khóa
- Hết đếm ngược → màn hình bị khóa

### Các nút khác

| Nút | Công dụng |
|-----|-----------|
| **Bật / Tắt theo dõi** | Bật hoặc dừng theo dõi idle |
| **Lưu cài đặt** | Ghi tham số vào `config.json` |
| **Thử khóa ngay** | Khóa màn hình ngay để kiểm tra |

Cài đặt được lưu cạnh file chạy (`config.json`). Lần mở sau sẽ nhớ lại.

---

## Chạy bằng Python (tuỳ chọn)

Nếu chưa đóng gói `.exe`:

```bat
python main.py
```

hoặc double-click `run.bat` (ưu tiên `.exe` nếu đã build; nếu không thì dùng `pythonw` — không hiện CMD).

Yêu cầu: Python 3 trên Windows, đã có `tkinter` (thường có sẵn).

---

## Đóng gói lại thành .exe

Khi sửa code và muốn tạo lại file chạy:

1. Cài dependency (một lần):

```bat
python -m pip install -r requirements.txt
```

2. Chạy:

```bat
build.bat
```

3. File mới nằm tại: `dist\AutoLockScreen.exe`

Tham số build: một file (`--onefile`), không hiện console (`--windowed`).

---

## Cấu trúc thư mục

```
AutoLockScreen/
├── main.py              # Mã nguồn
├── config.json          # Cài đặt (tự tạo/cập nhật khi chạy)
├── requirements.txt     # PyInstaller (để build)
├── build.bat            # Script đóng gói .exe
├── run.bat              # Chạy app (exe hoặc pythonw)
├── HUONG_DAN.md         # File này
└── dist/
    └── AutoLockScreen.exe
```

---

## Lưu ý

- Chỉ hỗ trợ **Windows** (dùng API `GetLastInputInfo` + `LockWorkStation`)
- Giữ app đang chạy (có thể thu nhỏ cửa sổ) thì mới theo dõi được
- Muốn chạy cùng Windows: đặt shortcut `AutoLockScreen.exe` vào thư mục Startup  
  (`Win + R` → `shell:startup`)
