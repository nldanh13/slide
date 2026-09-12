# PPT Event Controller

Ứng dụng Windows điều khiển chương trình gồm background, giới thiệu từng báo cáo viên,
file PowerPoint tương ứng, màn hình chuyển tiếp, thảo luận, Post-test và kết thúc.

## Yêu cầu

- Windows 10/11.
- Python 3.10 trở lên.
- Microsoft PowerPoint bản desktop đã được cài đặt.
- Nên dùng hai màn hình: laptop điều khiển và máy chiếu trình chiếu.

## Chạy nhanh

1. Giải nén toàn bộ thư mục.
3. Lần đầu ứng dụng tự tạo `.venv` và cài thư viện, nên cần Internet và có thể mất vài phút.
4. Nhập tên chương trình, chọn background/logo.
5. Chọn **Thêm báo cáo viên**, nhập thông tin và gắn file PowerPoint.
6. Chọn đúng màn hình sân khấu, sau đó bấm **Xem thử màn hình**.
7. Bấm **Lưu chương trình** rồi **BẮT ĐẦU**.

Có thể mở `sample_program.json` để xem cấu trúc dữ liệu mẫu.

## Flow tự động

Ứng dụng tạo thứ tự:

1. Background mở đầu.
2. Giới thiệu báo cáo viên 1.
3. PowerPoint 1.
4. Background cảm ơn/chuyển tiếp.
5. Lặp lại cho các báo cáo viên tiếp theo.
6. Thảo luận.
7. Post-test với mã QR.
8. Cảm ơn và kết thúc.

Khi kết thúc PowerPoint bằng `Esc`, ứng dụng tự đóng bài đó và chuyển sang background.

## Phím tắt

- `F5`: bắt đầu chương trình.
- `Ctrl + →`: chuyển sang phần kế tiếp.
- `Ctrl + ←`: quay lại phần trước.
- `Esc`: kết thúc toàn bộ trình chiếu khi cửa sổ điều khiển đang được chọn.

Trong PowerPoint vẫn dùng các phím chuyển slide thông thường như `Space`, `→`, `←`.
Các phím điều khiển chương trình cần được bấm khi cửa sổ điều khiển đang có focus;
khi PowerPoint đang chiếu, hãy kết thúc bài bằng `Esc` để app tự chuyển tiếp.

## Lưu ý màn hình PowerPoint

PowerPoint dùng màn hình trình chiếu đã chọn trong chính PowerPoint. Trước chương trình,
hãy mở PowerPoint một lần, vào **Slide Show → Monitor** và chọn máy chiếu. Ứng dụng tự
chọn màn hình cho background, nhưng không thay đổi cài đặt Monitor riêng của PowerPoint.

## Chạy bằng lệnh

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
