from __future__ import annotations

import json
import secrets
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from PySide6.QtCore import QObject, Signal


def local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


PAGE_TEMPLATE = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Điều khiển từ xa</title>
<style>
  body {{ margin: 0; background: #082f49; color: white; font-family: "Segoe UI", sans-serif;
         display: flex; flex-direction: column; align-items: center; padding: 24px 16px;
         min-height: 100vh; box-sizing: border-box; }}
  h1 {{ font-size: 18px; text-align: center; color: #bae6fd; margin-bottom: 4px; }}
  #status {{ font-size: 14px; color: #dbeafe; margin-bottom: 24px; text-align: center; min-height: 20px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; width: 100%; max-width: 360px; }}
  button {{ font-size: 20px; font-weight: 700; padding: 22px 10px; border: 0; border-radius: 12px;
           background: #e6edf7; color: #082f49; }}
  button:active {{ background: #bcd4f0; }}
  #start {{ grid-column: span 2; background: #075985; color: white; }}
  #stop {{ grid-column: span 2; background: #fee2e2; color: #991b1b; }}
  .msg {{ margin-top: 18px; font-size: 13px; color: #93c5fd; min-height: 16px; text-align: center; }}
</style>
</head>
<body>
<h1>ĐIỀU KHIỂN TỪ XA</h1>
<div id="status">Đang kết nối…</div>
<div class="grid">
  <button id="prev">◀ Trước</button>
  <button id="next">Tiếp ▶</button>
  <button id="start">BẮT ĐẦU</button>
  <button id="stop">KẾT THÚC</button>
</div>
<div class="msg" id="msg"></div>
<script>
const token = {token!r};
async function send(action) {{
  const msg = document.getElementById('msg');
  try {{
    const res = await fetch(`/action/${{action}}?token=${{token}}`, {{ method: 'POST' }});
    if (!res.ok) throw new Error('mã truy cập không hợp lệ');
    msg.textContent = '';
  }} catch (err) {{
    msg.textContent = 'Lỗi: ' + err.message;
  }}
  refreshStatus();
}}
async function refreshStatus() {{
  try {{
    const res = await fetch(`/status?token=${{token}}`);
    const data = await res.json();
    document.getElementById('status').textContent = data.status;
  }} catch (err) {{
    document.getElementById('status').textContent = 'Mất kết nối tới máy điều khiển';
  }}
}}
document.getElementById('prev').onclick = () => send('previous');
document.getElementById('next').onclick = () => send('next');
document.getElementById('start').onclick = () => send('start');
document.getElementById('stop').onclick = () => send('stop');
refreshStatus();
setInterval(refreshStatus, 2000);
</script>
</body>
</html>
"""


class RemoteControl(QObject):
    """Máy chủ HTTP nội bộ (LAN) cho phép điều khiển chương trình từ điện thoại."""

    next_requested = Signal()
    previous_requested = Signal()
    start_requested = Signal()
    stop_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.token = secrets.token_urlsafe(6)
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self._status_text = "Sẵn sàng"

    def set_status(self, text: str) -> None:
        self._status_text = text

    def url(self) -> str:
        if self.server is None:
            return ""
        port = self.server.server_address[1]
        return f"http://{local_ip()}:{port}/?token={self.token}"

    def start(self, port: int = 8765) -> None:
        if self.server is not None:
            return
        control = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):  # noqa: A002
                pass

            def _token_ok(self, query: dict) -> bool:
                return query.get("token", [""])[0] == control.token

            def do_GET(self):  # noqa: N802
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)
                if parsed.path == "/":
                    body = PAGE_TEMPLATE.format(token=control.token).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                elif parsed.path == "/status":
                    if not self._token_ok(query):
                        self.send_response(403)
                        self.end_headers()
                        return
                    body = json.dumps({"status": control._status_text}).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_response(404)
                    self.end_headers()

            def do_POST(self):  # noqa: N802
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)
                if not self._token_ok(query):
                    self.send_response(403)
                    self.end_headers()
                    return
                actions = {
                    "/action/next": control.next_requested,
                    "/action/previous": control.previous_requested,
                    "/action/start": control.start_requested,
                    "/action/stop": control.stop_requested,
                }
                signal = actions.get(parsed.path)
                if signal is None:
                    self.send_response(404)
                    self.end_headers()
                    return
                signal.emit()
                self.send_response(204)
                self.end_headers()

        try:
            self.server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
        except OSError:
            self.server = ThreadingHTTPServer(("0.0.0.0", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        self.thread = None
