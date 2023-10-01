import os
import subprocess
from PyQt5.QtCore import QThread, pyqtSignal


class Player(QThread):
    play_signal = pyqtSignal()
    pause_signal = pyqtSignal()

    def __init__(self, audio_file):
        super().__init__()
        self.audio_file = audio_file
        self.playing = False

    def run(self):
        while True:
            if self.playing:
                self.play_music()
            self.msleep(100)

    def play_music(self):
        if not self.playing:
            return

        if not self.music_process or self.music_process.poll() is not None:
            cmd = [
                ".\\FFmpeg\\ffplay.exe",
                "-i", self.audio_file,
                "-nodisp", "-autoexit", "-exitonkeydown"
            ]
            self.music_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def pause_music(self):
        if self.playing:
            self.pause_signal.emit()
            self.playing = False

    def resume_music(self):
        if not self.playing:
            self.play_signal.emit()
            self.playing = True

    def stop_music(self):
        if self.playing:
            self.playing = False
            if self.music_process and self.music_process.poll() is None:
                try:
                    os.kill(self.music_process.pid, 2)  # Send a Ctrl+C signal to terminate ffplay
                except OSError:
                    pass

    def toggle_play_pause(self):
        if self.playing:
            self.pause_music()
        else:
            self.resume_music()
