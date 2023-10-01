import sys
import subprocess
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QSlider,
    QLabel,
    QHBoxLayout,
    QWidget
)
from PyQt5.QtCore import (
    QTimer,
    Qt
)
from PyQt5.QtGui import (
    QPainter,
    QBrush,
    QPen,
    QPalette
)


from MusicVisualizer import AudioVisualizer

def get_audio_duration(audio_file_path):
    try:
        # 使用subprocess运行ffprobe命令获取音频文件的总长度
        cmd = [
            r".\FFmpeg\ffprobe.exe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_file_path
        ]
        result = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        return int(float(result.strip()))  # 将结果转换为浮点数，然后取整
    except subprocess.CalledProcessError as e:
        print("Error running ffprobe:", e)
        return 100


class CustomProgressBar(QSlider):
    def __init__(self):
        super().__init__(Qt.Horizontal)
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 2px;  /* 设置进度条轨道的高度 */
                background: rgba(241, 241, 241, 0.5);
            }
            QSlider::sub-page:horizontal {
                background: rgba(0, 0, 255, 0.5);  /* 半透明的已过进度颜色 (蓝色) */
            }
            QSlider::handle:horizontal {
                background: #2196F3; /* 设置滑块的背景颜色 */
                border: 1px solid #ccc;
                width: 0px;  /* 设置滑块的宽度 */
                height: 0px;
                margin: -5px 0;  /* 调整滑块的位置使其居中 */
            }
        """)

        self.dragging = False  # 用于标记是否正在拖动

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.update_progress(event)

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.update_progress(event)

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self.dragging = False
            self.update_progress(event)

    def update_progress(self, event):
        position = event.pos().x()
        progress = int((position / self.width()) * self.maximum())
        self.setValue(progress)
        event.accept()


class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.music_file = "D:\\Python_MX\\PyFusionInnovator\\temp.wav"  # 音乐文件路径
        self.audioDuration = get_audio_duration(self.music_file)

        self.setWindowTitle("Music Player")
        self.setGeometry(100, 100, 960, 540)

        self.playing = False
        self.music_process = None
        # 记录当前播放位置
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_counter)
        self.playingTime = 0

        MainLayout = QVBoxLayout()

        FunctionLayout = QVBoxLayout()

        ShowLayout = QVBoxLayout()
        self.visualizer = AudioVisualizer(self.music_file)
        ShowLayout.addWidget(self.visualizer)
        MainLayout.addLayout(ShowLayout, stretch=10)
        MainLayout.setSpacing(0)

        ProgressLayout = QHBoxLayout()
        self.progress_slider = CustomProgressBar()
        self.progress_slider.setOrientation(1)  # 设置垂直滑块
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(self.audioDuration)  # 将最大值设置为100，表示100%
        self.progress_slider.setValue(0)  # 初始值为0
        ProgressLayout.addWidget(self.progress_slider)
        self.playback_label = QLabel("0:00")
        ProgressLayout.addWidget(self.playback_label)
        FunctionLayout.addLayout(ProgressLayout)
        FunctionLayout.setSpacing(0)
        ProgressLayout.setSpacing(0)

        self.progress_slider.valueChanged.connect(self.update_playing_time)

        self.play_button = QPushButton("Play/Pause")
        self.play_button.clicked.connect(self.toggle_play_pause)
        self.play_button.setEnabled(True)
        self.play_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                border: none;
                color: white;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        FunctionLayout.addWidget(self.play_button)

        MainLayout.addLayout(FunctionLayout, stretch=1)

        central_widget = QWidget()
        central_widget.setLayout(MainLayout)
        self.setCentralWidget(central_widget)

    def toggle_play_pause(self):
        if self.playing is False:
            if self.music_process is None or self.music_process.poll() is not None:
                self.playing = True
                self.visualizer.update_visualization(self.playingTime)
                self.play_music()
                self.timer.start(1000)
                self.play_button.setText("Pause")
        else:
            self.playing = False
            if self.music_process and self.music_process.poll() is None:
                self.stop_music()
                self.play_button.setText("Play")
            self.visualizer.stop_visualization()

    def play_music(self):
        cmd = [
            ".\\FFmpeg\\ffplay.exe",
            "-i", self.music_file,
            "-nodisp", "-autoexit", "-exitonkeydown",
            "-ss", str(self.playingTime),
        ]
        self.music_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    def stop_music(self):
        self.music_process.terminate()
        self.music_process.wait()
        self.timer.stop()

    def update_counter(self):
        if self.playingTime < self.audioDuration:
            self.playingTime += 1
            self.playback_label.setText(self.format_time(self.playingTime))
            self.progress_slider.setValue(self.playingTime)
        else:
            self.stop_music()
            self.playing = False
            self.progress_slider.setValue(0)
            self.play_button.setText("Play")

    def format_time(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes}:{seconds:02}"

    def update_playing_time(self):
        if self.music_process and self.music_process.poll() is None:
            new_time = self.progress_slider.value()
            if new_time != self.playingTime:
                self.stop_music()
                self.timer.stop()
                self.playingTime = new_time
                self.playback_label.setText(
                    self.format_time(
                        self.progress_slider.value()
                    )
                )
                self.play_music()
                self.timer.start(1000)
                self.visualizer.update_visualization(self.playingTime)
        else:
            self.playingTime = self.progress_slider.value()
            self.playback_label.setText(
                self.format_time(
                    self.progress_slider.value()
                )
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec_())
