from __future__ import annotations

from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrinter

from core import Program, ProgramFileError
from i18n import tr


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_schedule_html(program: Program) -> str:
    rows = []
    for index, report in enumerate(program.reports, start=1):
        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td>{_escape(report.name)}</td>"
            f"<td>{_escape(report.department)}</td>"
            f"<td>{_escape(report.topic)}</td>"
            f"<td align='center'>{report.duration_minutes}</td>"
            "</tr>"
        )
    rows_html = "".join(rows) if rows else (
        f"<tr><td colspan='5' align='center'>{tr('Chưa có báo cáo viên')}</td></tr>"
    )
    organizer_html = f"<p>{_escape(program.organizer)}</p>" if program.organizer else ""
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; font-size: 12pt;">
      <h2 style="text-align:center;">{_escape(program.event_name)}</h2>
      {organizer_html}
      <table border="1" cellspacing="0" cellpadding="8" width="100%"
             style="border-collapse: collapse;">
        <tr style="background:#e8eef7; font-weight:bold;">
          <td>{tr('STT')}</td>
          <td>{tr('Báo cáo viên')}</td>
          <td>{tr('Đơn vị')}</td>
          <td>{tr('Chuyên đề')}</td>
          <td>{tr('Phút')}</td>
        </tr>
        {rows_html}
      </table>
      <p>{tr('Thảo luận')} ({tr('Thảo luận (phút)')}): {program.discussion_minutes}</p>
    </body>
    </html>
    """


def export_schedule_pdf(program: Program, path: str) -> None:
    document = QTextDocument()
    document.setHtml(build_schedule_html(program))
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(path)
    try:
        document.print_(printer)
    except Exception as exc:  # lỗi ghi file PDF (đang mở ở nơi khác, không có quyền...)
        raise ProgramFileError(f"Không thể tạo file PDF: {exc}") from exc


def build_duration_report_html(program: Program, actual_seconds: dict[int, float]) -> str:
    """`actual_seconds` là dict {id(report): tổng số giây đã trình bày thực tế},
    do MainWindow theo dõi trong lúc chạy chương trình (xem _begin/_end_ppt_timing)."""
    rows = []
    for index, report in enumerate(program.reports, start=1):
        actual_minutes = actual_seconds.get(id(report), 0.0) / 60
        planned = report.duration_minutes
        diff = actual_minutes - planned
        sign = "+" if diff >= 0 else ""
        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td>{_escape(report.name)}</td>"
            f"<td align='center'>{planned}</td>"
            f"<td align='center'>{actual_minutes:.1f}</td>"
            f"<td align='center'>{sign}{diff:.1f}</td>"
            "</tr>"
        )
    rows_html = "".join(rows) if rows else (
        f"<tr><td colspan='5' align='center'>{tr('Chưa có báo cáo viên')}</td></tr>"
    )
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; font-size: 12pt;">
      <h2 style="text-align:center;">{_escape(program.event_name)}</h2>
      <h3 style="text-align:center;">{tr('Báo cáo thời lượng trình bày thực tế')}</h3>
      <table border="1" cellspacing="0" cellpadding="8" width="100%"
             style="border-collapse: collapse;">
        <tr style="background:#e8eef7; font-weight:bold;">
          <td>{tr('STT')}</td>
          <td>{tr('Báo cáo viên')}</td>
          <td>{tr('Dự kiến (phút)')}</td>
          <td>{tr('Thực tế (phút)')}</td>
          <td>{tr('Chênh lệch (phút)')}</td>
        </tr>
        {rows_html}
      </table>
    </body>
    </html>
    """


def export_duration_report_pdf(program: Program, actual_seconds: dict[int, float], path: str) -> None:
    document = QTextDocument()
    document.setHtml(build_duration_report_html(program, actual_seconds))
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(path)
    try:
        document.print_(printer)
    except Exception as exc:
        raise ProgramFileError(f"Không thể tạo file PDF: {exc}") from exc
