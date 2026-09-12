from __future__ import annotations

LANGUAGES = {"vi": "Tiếng Việt", "en": "English"}

_current = "vi"

# Bản dịch tiếng Anh, khóa bằng chính chuỗi tiếng Việt gốc dùng trong code.
# Thiếu khóa nào thì tr() trả về nguyên văn tiếng Việt (không lỗi, không thiếu chữ).
_TRANSLATIONS: dict[str, str] = {
    "Điều khiển chương trình PowerPoint": "PowerPoint Program Controller",
    "ĐIỀU KHIỂN CHƯƠNG TRÌNH": "PROGRAM CONTROL",
    "Tên chương trình": "Program name",
    "Đơn vị tổ chức": "Organizer",
    "Background": "Background",
    "Chọn ảnh…": "Choose image…",
    "Logo": "Logo",
    "Chọn logo…": "Choose logo…",
    "Màn hình sân khấu": "Stage screen",
    "Thảo luận (phút)": "Discussion (minutes)",
    "Link Post-test": "Post-test link",
    "Màn hình ảo (chỉ bật khi test, không có máy chiếu)": "Virtual screen (test mode, no projector)",
    "Khi bật: màn hình sân khấu hiện dưới dạng cửa sổ nhỏ để xem thử,\n"
    "không chiếm toàn màn hình — dùng khi không có máy chiếu/màn hình thứ 2 để test.\n"
    "Khi trình chiếu thật, hãy tắt mục này.": (
        "When enabled: the stage screen shows as a small window for preview,\n"
        "instead of filling the screen — use this when there's no projector/second "
        "screen to test with.\nTurn it off for the real event."
    ),
    "+ Thêm báo cáo viên": "+ Add speaker",
    "Sửa": "Edit",
    "Xóa": "Delete",
    "Xóa báo cáo viên đang chọn?": "Delete the selected speaker?",
    "▲ Lên": "▲ Up",
    "▼ Xuống": "▼ Down",
    "STT": "No.",
    "Báo cáo viên": "Speaker",
    "Chuyên đề": "Topic",
    "File PowerPoint": "PowerPoint file",
    "Phút": "Minutes",
    "Mở chương trình": "Open program",
    "Lưu chương trình": "Save program",
    "Xem thử màn hình": "Preview screen",
    "Điều khiển từ xa…": "Remote control…",
    "◀ Phần trước": "◀ Previous",
    "BẮT ĐẦU": "START",
    "Phần tiếp ▶": "Next ▶",
    "KẾT THÚC": "END",
    "Cài đặt…": "Settings…",
    "Màn hình sân khấu (ẢO – chỉ dùng để test)": "Stage screen (VIRTUAL – test only)",
    "Màn hình trình chiếu": "Stage screen",
    "Hiện đồng hồ đếm giờ trên sân khấu": "Show countdown timer on stage screen",
    "Khôi phục dữ liệu": "Recover data",
    "Phát hiện dữ liệu tự động lưu từ lần chạy trước (có thể do ứng dụng bị đóng "
    "đột ngột). Khôi phục lại chương trình đó?": (
        "Found auto-saved data from a previous run (the app may have closed "
        "unexpectedly). Restore that program?"
    ),
    "Đã khôi phục dữ liệu tự động lưu.": "Auto-saved data restored.",
    "Sẵn sàng": "Ready",
    "Chưa chọn": "Not selected",
    "📡 Điều khiển từ xa: cổng {port}": "📡 Remote control: port {port}",
    "📡 Điều khiển từ xa: chưa bật": "📡 Remote control: not started",
    "Mở chương trình khác": "Open another program",
    "Dữ liệu báo cáo viên hiện tại chưa được lưu sẽ bị thay thế. Tiếp tục?": (
        "Unsaved speaker data will be replaced. Continue?"
    ),
    "Không thể lưu": "Cannot save",
    "Không thể mở": "Cannot open",
    "Đã lưu: {path}": "Saved: {path}",
    "Đã mở: {path}": "Opened: {path}",
    "Bắt đầu lại": "Restart",
    "Chương trình đang chạy. Bắt đầu lại từ đầu?": "The program is running. Restart from the beginning?",
    "Chưa thể trình chiếu": "Cannot start yet",
    "Mở đầu": "Opening",
    "Giới thiệu báo cáo viên": "Speaker introduction",
    "Chuyển tiếp": "Transition",
    "Thảo luận": "Discussion",
    "Post-test": "Post-test",
    "Kết thúc": "Closing",
    "Phần {index}/{total} – {label}": "Part {index}/{total} – {label}",
    "Lỗi PowerPoint": "PowerPoint error",
    "Kết thúc trình chiếu": "End the show",
    "Bạn có chắc muốn kết thúc trình chiếu hiện tại?": "Are you sure you want to end the current show?",
    "Đã kết thúc trình chiếu": "Show ended",
    "Đóng ứng dụng": "Close application",
    "Chương trình đang trình chiếu. Đóng ứng dụng sẽ dừng toàn bộ. Tiếp tục?": (
        "The show is currently running. Closing the app will stop everything. Continue?"
    ),
    "Thông tin báo cáo viên": "Speaker information",
    "Họ tên, học hàm/học vị*": "Full name, title*",
    "Đơn vị": "Department",
    "Tên chuyên đề*": "Topic title*",
    "Ảnh báo cáo viên": "Speaker photo",
    "File PowerPoint*": "PowerPoint file*",
    "Thời lượng dự kiến (phút)": "Expected duration (minutes)",
    "Lưu": "Save",
    "Hủy": "Cancel",
    "Chọn…": "Choose…",
    "Chọn file": "Choose file",
    "Thiếu thông tin": "Missing information",
    "Vui lòng nhập họ tên, chuyên đề và chọn file PowerPoint.": (
        "Please enter the name, topic and select a PowerPoint file."
    ),
    "Điều khiển từ xa": "Remote control",
    "Dùng điện thoại kết nối cùng Wi-Fi với máy tính này, quét mã QR "
    "hoặc mở đường dẫn bên dưới bằng trình duyệt để điều khiển chương trình.": (
        "Use a phone on the same Wi-Fi as this computer, scan the QR code "
        "or open the link below in a browser to control the program."
    ),
    "Lưu ý: liên kết chỉ dùng được khi điện thoại và máy tính cùng mạng Wi-Fi. "
    "Khởi động lại ứng dụng sẽ tạo mã truy cập mới.": (
        "Note: the link only works while the phone and computer share the same "
        "Wi-Fi network. Restarting the app generates a new access code."
    ),
    "Không tạo được mã QR": "Could not generate QR code",
    "Đóng": "Close",
    # Trang điều khiển từ xa (remote.py)
    "ĐIỀU KHIỂN TỪ XA": "REMOTE CONTROL",
    "Đang kết nối…": "Connecting…",
    "◀ Trước": "◀ Previous",
    "Tiếp ▶": "Next ▶",
    "Mất kết nối tới máy điều khiển": "Lost connection to the control computer",
    # Cài đặt
    "Cài đặt": "Settings",
    "Ngôn ngữ": "Language",
    "Cấu hình máy": "Machine setup",
    "Hỗ trợ": "Support",
    "Ngôn ngữ giao diện": "Interface language",
    "Chọn ngôn ngữ hiển thị cho cửa sổ điều khiển. Màn hình sân khấu vẫn hiển thị "
    "đúng theo nội dung chương trình (tên chương trình, tên báo cáo viên...) mà bạn nhập, "
    "không phụ thuộc vào ngôn ngữ giao diện.": (
        "Choose the display language for the control window. The stage screen "
        "still shows the program content (event name, speaker names...) exactly "
        "as you entered it, regardless of the interface language."
    ),
    "Áp dụng ngay lập tức. Nhãn có sẵn trên màn hình có thể cần mở lại cửa sổ để cập nhật hết.": (
        "Applies immediately. Some already-open labels may need the window "
        "reopened to fully refresh."
    ),
    "Cổng máy chủ điều khiển từ xa": "Remote control server port",
    "Đổi cổng sẽ khởi động lại máy chủ điều khiển từ xa ngay lập tức "
    "(mọi mã QR/đường dẫn cũ sẽ không dùng được nữa).": (
        "Changing the port immediately restarts the remote-control server "
        "(any previous QR code/link will stop working)."
    ),
    "Màn hình sân khấu mặc định": "Default stage screen",
    "Tự động (ưu tiên màn hình phụ)": "Automatic (prefer secondary screen)",
    "Kiểm tra hệ thống": "System check",
    "Kiểm tra lại": "Recheck",
    "Số màn hình phát hiện": "Detected screens",
    "Điều khiển PowerPoint (COM)": "PowerPoint control (COM)",
    "Có sẵn": "Available",
    "Không khả dụng (chỉ chạy được trên Windows có PowerPoint)": (
        "Not available (only works on Windows with PowerPoint installed)"
    ),
    "Địa chỉ IP mạng nội bộ": "Local network IP",
    "Phiên bản Python": "Python version",
    "Phím tắt": "Keyboard shortcuts",
    "F5: bắt đầu chương trình.": "F5: start the program.",
    "Ctrl + →: chuyển sang phần kế tiếp.": "Ctrl + →: go to the next part.",
    "Ctrl + ←: quay lại phần trước.": "Ctrl + ←: go back to the previous part.",
    "Esc: kết thúc toàn bộ trình chiếu khi cửa sổ điều khiển đang được chọn.": (
        "Esc: end the whole show while the control window is focused."
    ),
    "Mở hướng dẫn sử dụng (README)": "Open user guide (README)",
    "Không thể mở file hướng dẫn": "Could not open the guide file",
    "Phiên bản ứng dụng": "Application version",
    "Đóng cửa sổ này": "Close this window",
}


def set_language(code: str) -> None:
    global _current
    if code in LANGUAGES:
        _current = code


def get_language() -> str:
    return _current


def tr(text: str) -> str:
    if _current == "vi":
        return text
    return _TRANSLATIONS.get(text, text)
