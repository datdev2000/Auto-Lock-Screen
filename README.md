# Auto Lock Screen

Ứng dụng tự khóa màn hình Windows khi bạn không dùng chuột hoặc bàn phím trong một thời gian.

---

## Cách tải và mở

1. Tải file **`AutoLockScreen.exe`** (thường nằm trong thư mục `dist` của bản phát hành, hoặc nhận từ người gửi).
2. Double-click file để mở.
3. Nếu Windows hỏi *“Windows protected your PC”* → bấm **More info** → **Run anyway** (vì app chưa được Microsoft ký số).

Không cần cài Python, không cần mở CMD.

---

## Dùng lần đầu (3 bước)

1. Mở app → chỉnh thời gian nếu muốn (xem bên dưới).
2. Bấm **Bật theo dõi**.
3. Trạng thái hiện **Đang theo dõi** là đã chạy.

Khi không đụng chuột/phím đủ lâu → hiện thông báo đếm ngược → hết giờ thì khóa màn hình.

**Muốn hủy khóa:** di chuyển chuột, nhấn phím, hoặc bấm **Hủy khóa** trên thông báo.

---

## Các ô chỉnh thời gian

| Mục | Ý nghĩa | Ví dụ |
|-----|---------|--------|
| **Thời gian chờ (không hoạt động)** | Bao lâu không dùng máy thì hiện cảnh báo | `60` = 1 phút |
| **Thời gian chờ thông báo** | Sau khi hiện cảnh báo, bao lâu nữa thì khóa | `15` = 15 giây |

Dùng thanh kéo hoặc ô số bên phải. Bấm **Lưu cài đặt** để ghi nhớ.

---

## Chạy nền (như UniKey) — không cần để cửa sổ

- Bấm **Ẩn vào khay**, hoặc bấm nút **X** trên cửa sổ → app vẫn chạy, chỉ còn **icon nhỏ ở khay hệ thống** (góc phải dưới gần đồng hồ).
- **Chuột phải** vào icon đó:
  - **Hiện cửa sổ** — mở lại màn hình cài đặt
  - **Bật theo dõi** — bật/tắt theo dõi
  - **Thoát** — tắt hẳn ứng dụng

> Lưu ý: tắt bằng **Thoát** trên khay mới dừng hẳn. Đóng cửa sổ bằng X chỉ là **ẩn**, vẫn đang chạy.

---

## Tự mở khi bật máy

Trong phần **Tuỳ chọn**:

| Tuỳ chọn | Khi nào dùng |
|----------|----------------|
| **Khởi động cùng Windows (mở cửa sổ ứng dụng)** | Mỗi lần đăng nhập Windows, app tự mở (có cửa sổ) |
| **Khởi động ẩn trên khay hệ thống** | Mỗi lần đăng nhập, app chạy ẩn (chỉ có icon khay, giống UniKey) |

Tích chọn → app tự lưu. Muốn tắt: bỏ tích rồi **Lưu cài đặt**.

---

## Các nút thường dùng

| Nút | Việc nó làm |
|-----|-------------|
| **Bật theo dõi** / **Tắt theo dõi** | Bật hoặc dừng theo dõi không hoạt động |
| **Lưu cài đặt** | Lưu thời gian + tuỳ chọn khởi động |
| **Ẩn vào khay** | Ẩn cửa sổ, chạy nền |
| **Thử khóa ngay** | Khóa màn hình ngay để kiểm tra |

---

## Câu hỏi thường gặp

**App có cần Internet không?**  
Không.

**Đóng cửa sổ là tắt app rồi phải không?**  
Không. Đóng cửa sổ chỉ ẩn vào khay. Muốn tắt hẳn: chuột phải icon khay → **Thoát**.

**Sao không khóa?**  
Kiểm tra đã bấm **Bật theo dõi** chưa, và app còn chạy (còn icon khay hoặc cửa sổ).

**Để đâu cho tiện?**  
Copy `AutoLockScreen.exe` vào thư mục bất kỳ (ví dụ Desktop), rồi tạo shortcut nếu muốn.

**File cài đặt lưu ở đâu?**  
File `config.json` nằm cùng thư mục với `AutoLockScreen.exe` — không cần mở/sửa nếu bạn chỉnh trong app.

---

## Tóm tắt nhanh

1. Chạy `AutoLockScreen.exe`  
2. Bấm **Bật theo dõi**  
3. (Tuỳ chọn) Tích **Khởi động cùng Windows** hoặc **Khởi động ẩn**  
4. Bấm **X** hoặc **Ẩn vào khay** để dùng nền  
5. Muốn tắt hẳn → chuột phải icon khay → **Thoát**
