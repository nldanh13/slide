# PPT Event Controller

[![Tests](https://github.com/nldanh13/slide/actions/workflows/tests.yml/badge.svg)](https://github.com/nldanh13/slide/actions/workflows/tests.yml)

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
7. Mở menu **Quản lý chương trình ▾** → **Lưu chương trình**, rồi bấm **BẮT ĐẦU**.

Có thể mở `sample_program.json` để xem cấu trúc dữ liệu mẫu.

Các thao tác Mở/Lưu chương trình, Khôi phục sao lưu, Mẫu chương trình và Xuất lịch
trình (PDF) đều nằm gọn trong menu **Quản lý chương trình ▾** ở thanh dưới cùng — các
nút còn lại (Xem thử màn hình, Điều khiển từ xa, Cài đặt, Trước/Bắt đầu/Tiếp/Kết thúc)
là nhóm điều khiển trực tiếp khi trình chiếu, để tránh bấm nhầm lúc đang chạy chương
trình thật.

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

**Giảm nháy màn hình khi chuyển bài:** trước khi đóng PowerPoint của báo cáo viên hiện
tại, ứng dụng hiện sẵn màn hình nền (background) với nội dung của phần kế tiếp lên
trước, rồi mới đóng PowerPoint — nhờ vậy lúc PowerPoint đóng, phía dưới đã là màn hình
của ứng dụng thay vì màn hình desktop trần trụi. Tương tự, khi mở PowerPoint mới, màn
hình nền vẫn giữ nguyên cho tới khi PowerPoint thật sự đã chạy mới ẩn đi. Đây là hạn chế
tự nhiên khi chuyển đổi giữa 2 ứng dụng toàn màn hình khác nhau trên Windows nên không
thể mượt 100% như chuyển slide trong cùng một PowerPoint, nhưng khoảng lộ desktop được
rút ngắn tối đa.

## Phím tắt

- `F5`: bắt đầu chương trình.
- `Ctrl + →`: chuyển sang phần kế tiếp.
- `Ctrl + ←`: quay lại phần trước.
- `Esc`: kết thúc toàn bộ trình chiếu khi cửa sổ điều khiển đang được chọn.

Trong PowerPoint vẫn dùng các phím chuyển slide thông thường như `Space`, `→`, `←`.
Các phím điều khiển chương trình cần được bấm khi cửa sổ điều khiển đang có focus;
khi PowerPoint đang chiếu, hãy kết thúc bài bằng `Esc` để app tự chuyển tiếp.

## Điều khiển từ xa bằng điện thoại

Nếu bạn không ngồi ngay cạnh máy tính chạy chương trình (ví dụ báo cáo viên
đứng ở bục dùng đúng máy đó), bạn có thể điều khiển từ xa bằng điện thoại:

1. Đảm bảo điện thoại và máy tính đang **cùng một mạng Wi-Fi**.
2. Trong cửa sổ điều khiển, bấm **Điều khiển từ xa…**.
3. Dùng camera điện thoại quét mã QR hiện ra (hoặc gõ tay đường dẫn hiển thị bên dưới)
   để mở trang điều khiển bằng trình duyệt điện thoại.
4. Trang này có 4 nút: **Trước**, **Tiếp**, **BẮT ĐẦU**, **KẾT THÚC** — tương ứng với
   các nút trên máy tính, và luôn hiển thị phần đang chiếu hiện tại.

Đường dẫn có kèm theo một mã truy cập ngẫu nhiên để hạn chế người khác trong cùng
mạng Wi-Fi bấm nhầm; mỗi lần mở lại ứng dụng sẽ sinh mã mới. Tính năng này chỉ nên
dùng trong mạng nội bộ/tin cậy của sự kiện.

## Màn hình ảo (test khi không có máy chiếu)

Nếu chưa có máy chiếu/màn hình thứ 2 để test, tick vào ô **"Màn hình ảo (chỉ bật khi
test, không có máy chiếu)"** ở khung thông tin chương trình. Khi đó màn hình sân khấu
sẽ hiện ra dưới dạng một cửa sổ nhỏ (960×540) thay vì chiếm toàn màn hình, giúp bạn
vừa thao tác ở cửa sổ điều khiển vừa xem thử kết quả trên cùng một màn hình laptop.

Khi trình chiếu thật (có máy chiếu/màn hình thứ 2), hãy **bỏ tick** ô này để màn hình
sân khấu hiển thị toàn màn hình như bình thường — mặc định ô này luôn tắt mỗi khi mở
ứng dụng.

## Cài đặt (⚙ Cài đặt…)

Bấm nút **Cài đặt…** ở thanh dưới cùng để mở cửa sổ cấu hình gồm 3 tab:

- **Ngôn ngữ** — chọn Tiếng Việt/English cho giao diện điều khiển. Áp dụng ngay lập
  tức cho hầu hết nhãn; nội dung màn hình sân khấu (tên chương trình, tên báo cáo
  viên...) vẫn hiển thị đúng như bạn nhập, không phụ thuộc ngôn ngữ giao diện.
- **Cấu hình máy** — đổi cổng máy chủ điều khiển từ xa (mặc định 8765, đổi là khởi
  động lại máy chủ ngay), chọn màn hình sân khấu mặc định, và mục **Kiểm tra hệ
  thống** hiển thị số màn hình phát hiện được, thư viện điều khiển PowerPoint đã sẵn
  sàng chưa, địa chỉ IP mạng nội bộ (để nối điều khiển từ xa) và phiên bản Python —
  hữu ích khi cần chẩn đoán sự cố trước giờ diễn ra sự kiện.
- **Hỗ trợ** — bảng phím tắt nhanh, nút mở file README này, và thông tin phiên bản
  ứng dụng.

Các lựa chọn được lưu vào file `app_settings.json` cạnh ứng dụng và tự áp dụng lại ở
lần mở sau.

## Tự động lưu & khôi phục

Ứng dụng tự động lưu bản nháp chương trình mỗi 30 giây (và ngay trước khi bấm **BẮT
ĐẦU**) vào file `autosave.json` cạnh ứng dụng. Nếu app hoặc máy tính gặp sự cố giữa
sự kiện và bạn phải mở lại ứng dụng, lần mở tiếp theo sẽ hỏi khôi phục lại bản nháp
đó. Sau khi **Lưu chương trình** hoặc **Mở chương trình** thành công, bản tự động lưu
cũ sẽ được xóa vì đã có file chính thức thay thế; đóng ứng dụng bình thường cũng tự
xóa file này.

## Đồng hồ đếm giờ trên sân khấu

Khi báo cáo viên đang trình bày PowerPoint hoặc trong phần thảo luận, một đồng hồ đếm
ngược nhỏ (luôn nổi trên cùng) sẽ hiện ở góc màn hình sân khấu theo đúng thời lượng dự
kiến đã khai báo cho từng báo cáo viên (hoặc thời lượng thảo luận chung). Đồng hồ
chuyển sang màu đỏ và hiện dấu `-` khi đã quá giờ. Có thể tắt bằng cách bỏ tick ô
**"Hiện đồng hồ đếm giờ trên sân khấu"**.

## Kéo-thả sắp xếp báo cáo viên

Ngoài 2 nút **▲ Lên / ▼ Xuống**, bạn có thể kéo-thả trực tiếp một dòng trong bảng báo
cáo viên để đổi thứ tự trình bày — thứ tự (cột STT) sẽ tự cập nhật ngay.

## Sao lưu tự động khi lưu

Mỗi lần bấm **Lưu chương trình** thành công, ứng dụng tự giữ thêm một bản sao lưu có
đánh dấu ngày giờ trong thư mục `backups/` cạnh ứng dụng (giữ tối đa 30 bản gần nhất
cho mỗi file). Nếu chỉnh sửa nhầm hoặc lưu đè mất dữ liệu cũ, bấm **Khôi phục sao
lưu…** để xem danh sách và tải lại phiên bản trước đó.

## Xuất lịch trình ra file PDF

Bấm **Xuất lịch trình (PDF)…** để xuất danh sách báo cáo viên (tên, đơn vị, chuyên đề,
thời lượng) và thời gian thảo luận thành 1 file PDF gọn gàng — tiện in phát cho ban tổ
chức, MC hoặc bảo vệ mà không cần mở ứng dụng để xem lịch.

## Mẫu chương trình dựng sẵn

Bấm **Mẫu chương trình…** để:

- **Lưu chương trình hiện tại làm mẫu mới** (đặt tên tùy ý, ví dụ "Hội nghị khoa học
  thường quy") — lưu toàn bộ thông tin hiện có (tên chương trình, background/logo,
  thời lượng thảo luận, danh sách báo cáo viên...) làm mẫu dùng lại cho sự kiện sau.
- **Tải mẫu đã chọn** để nạp nhanh một mẫu có sẵn vào chương trình đang chỉnh sửa,
  thay vì nhập lại từ đầu — hữu ích cho các sự kiện định kỳ có cấu trúc giống nhau.
- **Xóa mẫu đã chọn** khi không còn cần dùng nữa.

Các mẫu được lưu dưới dạng file JSON trong thư mục `templates/` cạnh ứng dụng.

## Dùng slide riêng (từ 1 file PowerPoint tổng) hoặc ảnh riêng cho từng phần

Ngoài ảnh **Background** dùng chung mặc định, bấm **Cấu hình slide/ảnh riêng cho
từng phần…** để tùy chỉnh riêng cho **Thảo luận**, **Post-test**, **Kết thúc** (và cả
**Nền/Mở đầu** mặc định) theo 1 trong 2 cách:

1. **Dùng slide có sẵn** — chọn 1 file PowerPoint "chương trình tổng" (có thể là file
   thiết kế sẵn nhiều slide cho toàn bộ giao diện chương trình), rồi nhập số thứ tự
   slide tương ứng cho từng phần. Ứng dụng tự mở PowerPoint (ẩn) để xuất slide đó ra
   ảnh nền (cần cài Microsoft PowerPoint) — ảnh xuất ra được lưu cache trong thư mục
   `slide_cache/` để không phải xuất lại nếu file gốc không đổi.
2. **Dùng ảnh riêng** — nếu không có/không muốn dùng slide, chọn thẳng 1 file ảnh cho
   phần đó.

Nếu một phần không được cấu hình gì cả, ứng dụng tự rơi về dùng ảnh **Background**
mặc định — không bắt buộc phải cấu hình đầy đủ cả 4 phần.

## Nhập nhiều file PowerPoint cùng lúc

Thay vì bấm **+ Thêm báo cáo viên** từng người, bấm **Nhập nhiều file PowerPoint…** để
chọn cả loạt file `.pptx` một lần. Ứng dụng đoán theo tên file:

- File chứa từ khóa như "khai mạc", "chương trình", "MC", "background", "mở đầu"...
  được xếp vào nhóm **Giao diện – Mở đầu**.
- File chứa từ khóa như "kết thúc", "bế mạc", "closing"... được xếp vào nhóm
  **Giao diện – Kết thúc**.
- Các file còn lại được xếp vào nhóm **Báo cáo viên** (tên báo cáo viên tạm đoán từ
  tên file, bạn có thể sửa lại).

Bảng xem trước cho phép bạn đổi lại phân loại từng dòng (hoặc chọn **Bỏ qua**) trước
khi bấm **Nhập**. Sau khi nhập, các báo cáo viên xuất hiện trong bảng chính như bình
thường (vào **Sửa** để bổ sung đơn vị/chuyên đề/ảnh/thời lượng); file khai mạc/kết thúc
được điền vào 2 ô **File khai mạc** / **File kết thúc** ở khung thông tin chương trình.

Khi đã khai báo file khai mạc/kết thúc, chương trình sẽ **mở file đó bằng PowerPoint**
(giống hệt cách chiếu bài của báo cáo viên) thay cho màn hình nền tĩnh mặc định ở phần
mở đầu/kết thúc. Để trống (bấm **Xóa**) nếu muốn quay lại dùng màn hình nền mặc định.

## Đóng gói thành file .exe (không cần cài Python)

Nếu muốn đưa ứng dụng cho người khác dùng mà không cần cài Python/thư viện, chạy file
`build_exe.bat` **trên máy Windows** (không build được từ máy khác vì cần đúng
`pywin32` của Windows):

```powershell
build_exe.bat
```

Script sẽ cài `pyinstaller`, cài các thư viện trong `requirements.txt`, rồi đóng gói
thành `dist\PPT_Event_Controller.exe`. Copy file `.exe` đó vào cùng thư mục với
`README.md` và `sample_program.json` để phân phối — `app_settings.json` và
`autosave.json` sẽ tự tạo cạnh file `.exe` khi chạy, y hệt như khi chạy bằng
`python main.py`.

## Kiểm tra an toàn trước khi trình chiếu

Khi bấm **BẮT ĐẦU**, ứng dụng kiểm tra và báo lỗi rõ ràng nếu: chưa nhập tên chương
trình, chưa có báo cáo viên, thiếu tên/chuyên đề, chưa chọn (hoặc không tìm thấy) file
PowerPoint, hoặc không tìm thấy ảnh nền/logo/ảnh báo cáo viên đã khai báo.

Ứng dụng cũng hỏi xác nhận trước các thao tác có thể ảnh hưởng đến chương trình đang
chạy: bắt đầu lại từ đầu khi đang trình chiếu, kết thúc trình chiếu, đóng ứng dụng khi
đang chạy, hoặc mở một chương trình khác khi dữ liệu hiện tại chưa lưu.

**Chống bấm nhầm làm văng bài báo cáo viên:** nếu báo cáo viên đang trình bày dở
(PowerPoint đang chạy) mà người điều khiển bấm **Phần tiếp ▶**, **◀ Phần trước**, hoặc
**KẾT THÚC** — dù bấm nhầm hay cố ý — ứng dụng sẽ luôn hỏi xác nhận trước khi đóng bài
đang chiếu, tránh làm gián đoạn báo cáo viên giữa chừng chỉ vì một cú bấm nhầm. Việc
báo cáo viên tự bấm `Esc` để kết thúc bài của chính mình thì không bị hỏi lại (đó là
thao tác chủ động của họ).

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

## Chạy test / CI

Bộ test (`test_*.py`) không phụ thuộc Windows/PowerPoint nên chạy được trên mọi hệ điều
hành:

```bash
pip install -r requirements.txt
python -m unittest discover -p "test_*.py" -v
```

GitHub Actions (`.github/workflows/tests.yml`) tự động chạy toàn bộ test này mỗi khi có
commit hoặc pull request mới, để lỗi không lọt vào `main` mà không ai biết.
