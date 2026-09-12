import json
import time
import unittest
import urllib.error
import urllib.request

from PySide6.QtWidgets import QApplication

from remote import RemoteControl


class RemoteControlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.remote = RemoteControl()
        self.remote.start(port=0)
        self.addCleanup(self.remote.stop)
        self.port = self.remote.server.server_address[1]

    def _wait_until(self, predicate, timeout=2.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return True
            time.sleep(0.01)
        return False

    def test_status_rejects_wrong_token(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(f"http://127.0.0.1:{self.port}/status?token=sai", timeout=3)
        self.assertEqual(ctx.exception.code, 403)

    def test_action_rejects_wrong_token(self):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/action/next?token=sai", method="POST"
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=3)
        self.assertEqual(ctx.exception.code, 403)

    def test_status_reports_current_text(self):
        self.remote.set_status("Đang chiếu phần 2")
        with urllib.request.urlopen(
            f"http://127.0.0.1:{self.port}/status?token={self.remote.token}", timeout=3
        ) as resp:
            body = json.loads(resp.read())
        self.assertEqual(body["status"], "Đang chiếu phần 2")

    def test_next_action_emits_signal_on_main_thread(self):
        received = []
        self.remote.next_requested.connect(lambda: received.append(True))
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/action/next?token={self.remote.token}", method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            self.assertEqual(resp.status, 204)
        self.assertTrue(self._wait_until(lambda: received), "signal was not delivered in time")

    def test_unknown_action_returns_404(self):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/action/khong_ton_tai?token={self.remote.token}",
            method="POST",
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req, timeout=3)
        self.assertEqual(ctx.exception.code, 404)

    def test_url_contains_token(self):
        self.assertIn(f"token={self.remote.token}", self.remote.url())


if __name__ == "__main__":
    unittest.main()
