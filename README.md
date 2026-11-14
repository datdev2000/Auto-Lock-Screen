# Auto Lock Screen

Ứng dụng tự khóa màn hình Windows khi bạn không dùng chuột hoặc bàn phím trong một thời gian.

---

## Tải về

👉 **[Tải AutoLockScreen.exe](https://github.com/datdev2000/Auto-Lock-Screen/releases/latest/download/AutoLockScreen.exe)**

Hoặc vào trang phát hành: [Releases](https://github.com/datdev2000/Auto-Lock-Screen/releases/latest)

---

## Cách mở

1. Tải file bằng link ở trên.
2. Double-click **`AutoLockScreen.exe`** để mở.
3. Nếu Windows hỏi *“Windows protected your PC”* → bấm **More info** → **Run anyway** (app chưa được Microsoft ký số).

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
`C:\ProgramData\AutoLockScreen\config.json` — chỉnh trong app là đủ, không cần sửa tay.

**Gỡ cài đặt?**  
Trong app bấm **Gỡ cài đặt** để xóa dữ liệu + hủy khởi động cùng Windows, rồi tự xóa file `.exe` nếu muốn.

**Máy đang khóa (Win+L) thì app còn đếm không?**  
Không — app **tạm dừng**. Mở khóa xong mới đếm lại từ đầu (tránh khóa/sleep lặp khi đang khóa).

**Windows Sleep 5 phút, app timeout 10 phút thì sao?**  
Windows sẽ ngủ trước. App chỉ kịp chạy nếu thời gian chờ của app **ngắn hơn** Sleep của Windows. Khi máy đã ngủ, app cũng bị treo theo.

**Thấy nhiều icon khay?**  
Chỉ nên chạy **1** bản. Bản mới chặn instance trùng — thoát hết app cũ (chuột phải icon → Thoát) rồi mở lại.

---

## Tắt Sleep tự động của Windows

Để app (Lock / Sleep / Tắt máy) kịp chạy, nên **tắt Sleep Windows** hoặc đặt Sleep dài hơn timeout của app.

### Cách nhanh trong app

1. Mở Auto Lock Screen  
2. Tích **Tắt Sleep tự động của Windows (Never)**  
3. Bấm **Áp dụng ngay** (hoặc chỉ tích — cũng áp dụng)  
4. Dòng trạng thái hiện Sleep AC/Pin = **Never**

Bỏ tích → app **khôi phục** thời gian Sleep cũ (đã lưu).  
**Gỡ cài đặt** cũng khôi phục Sleep nếu từng tắt.

### Cách làm tay (Settings Windows)

1. Bấm **Start** → gõ **Power** → mở **Power & sleep settings**  
   (hoặc **Settings → System → Power & battery / Power & sleep**)  
2. Mục **Screen and sleep** / **Khi cắm điện, PC của tôi chuyển sang chế độ ngủ sau**  
3. Chọn **Never** (cả khi cắm điện và dùng pin nếu có)  
4. (Tuỳ chọn) Tắt luôn tắt màn hình nếu muốn: **Never**

**Windows 11 đường tắt:**  
`Win + I` → **System** → **Power & battery** → **Screen and sleep** → **Never**

---

## Tóm tắt nhanh

1. Chạy `AutoLockScreen.exe`  
2. Bấm **Bật theo dõi**  
3. (Tuỳ chọn) Tích **Khởi động cùng Windows** hoặc **Khởi động ẩn**  
4. Bấm **X** hoặc **Ẩn vào khay** để dùng nền  
5. Muốn tắt hẳn → chuột phải icon khay → **Thoát**
