from __future__ import annotations

from pathlib import Path


class PowerPointError(RuntimeError):
    pass


class PowerPointController:
    """Điều khiển Microsoft PowerPoint qua COM trên Windows."""

    def __init__(self) -> None:
        self.app = None
        self.presentation = None
        self.slideshow = None

    def start(self, file_path: str) -> None:
        path = Path(file_path).resolve()
        if not path.is_file():
            raise PowerPointError(f"Không tìm thấy file: {path}")
        if path.suffix.lower() not in {".ppt", ".pptx", ".pptm", ".pps", ".ppsx"}:
            raise PowerPointError("File đã chọn không phải định dạng PowerPoint.")

        try:
            import pythoncom
            import win32com.client

            pythoncom.CoInitialize()
            if self.app is None:
                self.app = win32com.client.DispatchEx("PowerPoint.Application")
                self.app.Visible = True
            self.presentation = self.app.Presentations.Open(
                str(path), ReadOnly=True, Untitled=False, WithWindow=True
            )
            self.presentation.SlideShowSettings.ShowPresenterView = False
            self.slideshow = self.presentation.SlideShowSettings.Run()
        except Exception as exc:
            self.close_presentation()
            raise PowerPointError(
                "Không thể mở trình chiếu. Hãy kiểm tra Microsoft PowerPoint "
                "đã được cài và file không bị khóa."
            ) from exc

    def is_running(self) -> bool:
        if self.app is None:
            return False
        try:
            return self.app.SlideShowWindows.Count > 0
        except Exception:
            return False

    def next_slide(self) -> None:
        try:
            self.slideshow.View.Next()
        except Exception:
            pass

    def previous_slide(self) -> None:
        try:
            self.slideshow.View.Previous()
        except Exception:
            pass

    def close_presentation(self) -> None:
        try:
            if self.slideshow is not None:
                self.slideshow.View.Exit()
        except Exception:
            pass
        try:
            if self.presentation is not None:
                self.presentation.Close()
        except Exception:
            pass
        self.slideshow = None
        self.presentation = None

    def shutdown(self) -> None:
        self.close_presentation()
        try:
            if self.app is not None:
                self.app.Quit()
        except Exception:
            pass
        self.app = None

