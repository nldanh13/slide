from __future__ import annotations

from pathlib import Path


def _default_player_factory():
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

    return QMediaPlayer(), QAudioOutput()


class AudioController:
    """Phát nhạc nền lặp lại (chờ khai mạc / giải lao thảo luận / kết thúc) qua
    QtMultimedia. Máy không có codec/thư viện âm thanh cần thiết thì bỏ qua âm
    thầm — lỗi âm thanh không được phép làm gián đoạn buổi trình chiếu."""

    def __init__(self, player_factory=_default_player_factory) -> None:
        self._player_factory = player_factory
        self.player = None
        self.audio_output = None
        self._current_path = ""
        self._volume = 0.7

    def play_loop(self, path: str) -> None:
        if not path or not Path(path).is_file():
            self.stop()
            return
        if path == self._current_path and self.player is not None:
            return
        self.stop()
        try:
            from PySide6.QtCore import QUrl

            player, audio_output = self._player_factory()
            player.setAudioOutput(audio_output)
            try:
                audio_output.setVolume(self._volume)
            except Exception:
                pass
            player.setSource(QUrl.fromLocalFile(str(Path(path).resolve())))
            player.setLoops(-1)  # QMediaPlayer.Loops.Infinite
            player.play()
            self.player = player
            self.audio_output = audio_output
            self._current_path = path
        except Exception:
            self.player = None
            self.audio_output = None
            self._current_path = ""

    def stop(self) -> None:
        if self.player is not None:
            try:
                self.player.stop()
            except Exception:
                pass
        self.player = None
        self.audio_output = None
        self._current_path = ""

    def is_playing(self) -> bool:
        return self.player is not None

    def set_volume(self, volume: float) -> None:
        """volume: 0.0 – 1.0. Áp dụng ngay nếu đang phát; luôn được nhớ lại để
        dùng cho lần play_loop() kế tiếp."""
        self._volume = max(0.0, min(1.0, volume))
        if self.audio_output is not None:
            try:
                self.audio_output.setVolume(self._volume)
            except Exception:
                pass
