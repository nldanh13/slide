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
