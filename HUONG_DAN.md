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
| **Lưu cài đặt** | Ghi tham số vào `config.json` + đăng ký khởi động |
| **Ẩn vào khay** | Ẩn cửa sổ, chạy nền như UniKey |
| **Thử khóa ngay** | Khóa màn hình ngay để kiểm tra |

### Tuỳ chọn

| Tuỳ chọn | Ý nghĩa |
|----------|---------|
| **Khởi động cùng Windows** | Mở app (có cửa sổ) khi đăng nhập Windows |
| **Khởi động ẩn trên khay** | Mở app ẩn icon khay khi đăng nhập (tự bật luôn khởi động cùng Windows) |

- Đóng cửa sổ bằng **X** → **ẩn vào khay**, không thoát
- Chuột phải icon khay → **Hiện cửa sổ** / **Bật theo dõi** / **Thoát**

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

## Tắt Sleep Windows (để app kịp chạy)

**Trong app:** tích **Tắt Sleep tự động của Windows (Never)** → **Áp dụng ngay**.  
Bỏ tích = khôi phục Sleep cũ.

**Làm tay:** `Win + I` → System → Power & battery → Screen and sleep → đặt Sleep = **Never**.

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
├── main.py                 # Entry point
├── autolock/               # Module theo chức năng
│   ├── app.py              # UI chính
│   ├── config.py           # Đọc/ghi cấu hình
│   ├── idle.py             # Idle + khóa màn hình
│   ├── startup.py          # Khởi động cùng Windows
│   ├── icons.py            # Icon ổ khóa
│   ├── warning.py          # Cảnh báo sắp khóa
│   └── paths.py            # Đường dẫn ProgramData / assets
├── assets/lock.ico         # Icon ứng dụng
├── requirements.txt
├── build.bat / run.bat
└── dist/AutoLockScreen.exe
```

Dữ liệu người dùng: `C:\ProgramData\AutoLockScreen\` (config, …)

---

## Lưu ý

- Chỉ hỗ trợ **Windows** (dùng API `GetLastInputInfo` + `LockWorkStation`)
- App cần đang chạy (cửa sổ hoặc icon khay) mới theo dõi được
- Khởi động cùng Windows dùng registry `HKCU\...\Run` (bật/tắt trong app)
- Khi chạy bằng Python cần: `pip install pystray pillow`
