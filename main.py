from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from main_window import APP_STYLE, MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PPT Event Controller")
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
