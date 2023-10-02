import os
import sys
import json
import subprocess
from loguru import logger
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QSlider,
    QLabel,
    QHBoxLayout,
    QWidget,
    QStackedLayout, QStackedWidget, QSizePolicy, QSpacerItem,
)
from PyQt5.QtCore import (
    QTimer,
    Qt,
    QPoint,
    QSize, QPropertyAnimation, QEasingCurve,
)
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QPixmap, QIcon, QPainter
from MusicVisualizer import AudioVisualizer

PATH = os.path.split(__file__)[0]


def MusicPlayerCache(key: str, value: dict = None, rw: bool = True) -> dict or bool:
    """
    音乐播放器的播放缓存
    :param key: 音乐名称
    :param value: 数据
    :param rw: 读或者写，默认读（True）
    :return: None
    """
    logger.info("音乐播放器进行缓存")
    result = None
    __path__ = os.path.join(PATH, "cache")

    # 查看cache文件夹和MusicPlayerCache.json是否存在
    if os.path.isdir(__path__) is False:
        os.mkdir(__path__)
    __path__ = os.path.join(PATH, "cache/MusicPlayerCache.json")
    if os.path.isfile(__path__) is False:
        with open(__path__, "w+", encoding="utf-8") as wfp:
            wfp.write("{}")
    # end

    with open(__path__, mode="r", encoding="utf-8") as rfp:
        result = json.loads(rfp.read())

    if rw is True:
        if key in result.keys():
            logger.info(f"读取文件{key}缓存")
            return result[key]
        else:
            return None

    with open(__path__, mode="w+", encoding="utf-8") as wfp:
        result[key] = value
        logger.info(f"写入数据{key}")
        wfp.write(json.dumps(result, indent=4, ensure_ascii=False))
    logger.info(f"写入{key}成功")

    return True


def get_music_cover(music_file) -> str or None:
    cache_dir = "./cache"
    os.makedirs(cache_dir, exist_ok=True)  # 创建缓存目录

    output_file = os.path.join(cache_dir, os.path.basename(music_file).replace(".", "_") + "_cover.jpg")  # 生成保存路径
    if os.path.isfile(output_file) is True:
        return output_file

    try:
        cmd = [
            '.\\FFmpeg\\ffmpeg.exe',
            '-i', f"{music_file}",
            '-an', '-vcodec', 'copy',
            f"{output_file}"
        ]  # ffmpeg命令
        result = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        output, _ = result.communicate()  # 等待子进程结束并获取输出

        if result.returncode == 0 and os.path.exists(output_file):
            return output_file
        else:
            return None
    except Exception as e:
        logger.error(f"获取封面错误: {e}")
        return None


def get_audio_duration(audio_file_path: str) -> int:
    """
    使用subprocess运行ffprobe命令获取音频文件的总长度
    :param audio_file_path: 文件路径
    :return: int
    """
    result = 100
    logger.info(f"获取{audio_file_path}的总时长")
    try:
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

        # 将结果转换为浮点数，然后取整
        result = int(float(result.split('\n')[0].strip()))
        logger.info(f"获取到长度：{result}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error("Error running ffprobe:", e)
        return 100


class CustomProgressBar(QSlider):
    """自定义音乐进度条"""
    def __init__(self):
        super().__init__(Qt.Horizontal)
        logger.info("初始化音乐进度条")
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

    def update_progress(self, event) -> None:
        """
        更新当前进度条位置
        :param event: Event
        :return: None
        """
        position = event.pos().x()
        progress = int((position / self.width()) * self.maximum())
        self.setValue(progress)
        event.accept()


class SvgButton(QPushButton):
    """自定义按钮"""
    def __init__(self, svg_file, text="", parent=None) -> None:
        super().__init__(text, parent)
        self.setIcon(self.loadSvgIcon(svg_file))
        icon_size = QSize(32, 32)  # 设置图标大小
        self.setIconSize(icon_size)
        self.setFixedSize(icon_size)  # 设置按钮大小，确保是正方形
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;  /* 背景透明 */
                border: none;
                color: white;
                padding: 5px 10px;
                border-radius: 16px;  /* 设置按钮的圆角 */
            }
        """)
        self.hovered = False

    @staticmethod
    def loadSvgIcon(svg_file) -> QIcon:
        renderer = QSvgRenderer(svg_file)
        pixmap = QPixmap(32, 32)  # 图标大小
        pixmap.fill(Qt.transparent)  # 填充透明背景

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return QIcon(pixmap)

    def enterEvent(self, event):
        self.hovered = True
        self.update()

    def leaveEvent(self, event):
        self.hovered = False
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.hovered:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            pixmap = self.icon().pixmap(self.size())
            new_width = int(pixmap.width() * 1.2)
            new_height = int(pixmap.height() * 1.2)
            pixmap = pixmap.scaled(QSize(new_width, new_height), Qt.KeepAspectRatio)
            x = int((self.width() - pixmap.width()) / 2)
            y = int((self.height() - pixmap.height()) / 2)
            painter.drawPixmap(x, y, pixmap)
            self.setFixedSize(new_width, new_height)


class MusicPlayer(QMainWindow):
    """音乐播放器"""
    def __init__(self, musicFile: str):
        """
        :param musicFile: 音乐文件路径
        """
        logger.info("初始化音乐播放器")
        super().__init__(parent=None)
        self.musicFile = musicFile  # 音乐文件路径
        self.audioDuration = get_audio_duration(self.musicFile)
        self.musicCover = get_music_cover(self.musicFile)
        self.dragging = False  # 记录是否正在拖动
        self.drag_start_position = QPoint()

        self.setWindowTitle("Music Player")
        self.setGeometry(100, 100, 960, 640)

        # 隐藏窗口标题栏和边框
        self.setWindowFlags(Qt.CustomizeWindowHint)

        self.playing = False
        self.music_process = None
        # 记录当前播放位置
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updatePlayingTime)
        self.playingTime = 0

        centralWidget = QWidget()
        centralWidget.setStyleSheet("background-color:rgba(0, 0, 0, 0);")
        MainLayout = QVBoxLayout()
        MainLayout.setAlignment(Qt.AlignCenter)

        # 顶部
        BottomMenuLayout = QHBoxLayout()

        # 创建自定义最小化按钮
        minimize_button = QPushButton()
        minimize_button.setFixedSize(20, 20)
        minimize_button.setStyleSheet("border-radius: 10px; background-color: green; color: white;")
        minimize_button.clicked.connect(self.showMinimized)

        # 创建自定义最大化按钮
        maximize_button = QPushButton()
        maximize_button.setFixedSize(20, 20)
        maximize_button.setStyleSheet("border-radius: 10px; background-color: blue; color: white;")
        maximize_button.clicked.connect(self.toggleMaximized)

        # 创建自定义关闭按钮
        closeButton = QPushButton()
        closeButton.setFixedSize(20, 20)
        closeButton.setStyleSheet("border-radius: 10px; background-color: red; color: white;")
        closeButton.clicked.connect(self.close)

        # 将最小化、最大化和关闭按钮添加到按钮布局
        BottomMenuLayout.addWidget(minimize_button, alignment=Qt.AlignTop | Qt.AlignRight)
        BottomMenuLayout.addWidget(maximize_button)
        BottomMenuLayout.addWidget(closeButton)

        MainLayout.addLayout(BottomMenuLayout, stretch=1)

        FunctionLayout = QVBoxLayout()

        ShowLayout = QVBoxLayout()
        stacked_widget = QStackedWidget()
        self.visualizer = AudioVisualizer(self.musicFile)
        # ShowLayout.addWidget(self.visualizer)
        ShowLayout.addWidget(self.visualizer)
        MainLayout.addLayout(ShowLayout, stretch=10)
        MainLayout.setSpacing(1)

        ProgressLayout = QHBoxLayout()
        self.progressSlider = CustomProgressBar()
        self.progressSlider.setOrientation(1)  # 设置垂直滑块
        self.progressSlider.setMinimum(0)
        self.progressSlider.setMaximum(self.audioDuration)  # 将最大值设置为100，表示100%
        self.progressSlider.setValue(0)  # 初始值为0
        ProgressLayout.addWidget(self.progressSlider)
        self.playbackLabel = QLabel("0:00")
        ProgressLayout.addWidget(self.playbackLabel)
        FunctionLayout.addLayout(ProgressLayout)
        FunctionLayout.setSpacing(0)
        ProgressLayout.setSpacing(0)

        self.initProgressSlider()
        self.progressSlider.valueChanged.connect(self.updateProgressPlayingTime)

        FunctionTransverseLayout = QHBoxLayout()
        if self.musicCover:
            self.MusicBgImg = QLabel()
            self.MusicBgImg.setPixmap(
                QPixmap(
                    self.musicCover
                ).scaled(
                    QSize(64, 64),
                    Qt.AspectRatioMode.KeepAspectRatio
                )
            )
            # 设置MusicBgImg的大小
            self.MusicBgImg.setFixedSize(64, 64)

            self.MusicBgImg.setStyleSheet("border: none; background-color: transparent;")
            FunctionTransverseLayout.addWidget(self.MusicBgImg, alignment=Qt.AlignLeft)

        FunctionTransverseLayout.addItem(QSpacerItem(2, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.MusicNameShow = QLabel(os.path.split(self.musicFile)[-1].split(".", 1)[0])
        self.MusicNameShow.setStyleSheet("font-size: 10px;")
        FunctionTransverseLayout.addWidget(self.MusicNameShow, alignment=Qt.AlignLeft)

        FunctionTransverseLayout.addItem(QSpacerItem(2, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.PreviousSongButton = SvgButton(".\\img\\PreviousSongButton.svg")
        self.PreviousSongButton.setEnabled(True)
        self.PreviousSongButton.setFixedSize(32, 32)
        FunctionTransverseLayout.addWidget(self.PreviousSongButton)

        FunctionTransverseLayout.addItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.playOrPauseButton = SvgButton(".\\img\\pause.svg")
        self.playOrPauseButton.setFixedSize(32, 32)
        self.playOrPauseButton.clicked.connect(self.togglePlayPause)
        self.playOrPauseButton.setEnabled(True)
        FunctionTransverseLayout.addWidget(self.playOrPauseButton)

        FunctionTransverseLayout.addItem(QSpacerItem(2, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.NextSongButton = SvgButton(".\\img\\NextSongButton.svg")
        self.NextSongButton.setFixedSize(32, 32)
        self.NextSongButton.setEnabled(True)
        FunctionTransverseLayout.addWidget(self.NextSongButton)

        FunctionTransverseLayout.addItem(QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        FunctionLayout.addLayout(FunctionTransverseLayout)
        MainLayout.addLayout(FunctionLayout, stretch=1)

        centralWidget.setLayout(MainLayout)
        self.setCentralWidget(centralWidget)
        logger.info("初始化音乐播放器成功")

    def toggleMaximized(self) -> None:
        """
        检查窗口是否处于最大化状态，并相应地切换最大化和还原窗口的状态。
        :return: None
        """
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def togglePlayPause(self) -> None:
        """
        用于play/pause按钮的判断事件
        :return: None
        """
        if self.playing is False:
            if self.music_process is None or self.music_process.poll() is not None:
                self.playing = True
                self.visualizer.update_visualization(self.playingTime)
                self.playMusic()
                self.timer.start(1000)
                self.playOrPauseButton.setIcon(
                    self.playOrPauseButton.loadSvgIcon(".\\img\\play.svg")
                )
        else:
            self.playing = False
            if self.music_process and self.music_process.poll() is None:
                self.stopMusic()
                MusicPlayerCache(
                    os.path.split(self.musicFile)[-1],
                    {"playingTime": self.playingTime + 1},
                    rw=False
                )
            self.playOrPauseButton.setIcon(
                self.playOrPauseButton.loadSvgIcon(".\\img\\pause.svg")
            )
            self.visualizer.stop_visualization()
        self.playOrPauseButton.setIconSize(QSize(32, 32))
        self.playOrPauseButton.setFixedSize(QSize(32, 32))  # 设置按钮大小，确保是正方形

    def playMusic(self) -> None:
        """
        播放音乐
        :return: None
        """
        logger.info("开始播放")
        cache = MusicPlayerCache(
            os.path.split(self.musicFile)[-1]
        )
        if cache:
            self.playingTime = cache['playingTime']
            self.visualizer.update_visualization(
                self.playingTime
            )

        cmd = [
            ".\\FFmpeg\\ffplay.exe",
            "-i", self.musicFile,
            "-nodisp", "-autoexit", "-exitonkeydown",
            "-ss", str(self.playingTime),
        ]
        self.music_process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info("播放成功")

    def stopMusic(self) -> None:
        """
        停止播放
        :return: None
        """
        if self.music_process is not None and self.timer is not None:
            self.music_process.terminate()
            self.music_process.wait()
            self.timer.stop()
            logger.info("停止播放")
        else:
            return None

    def updatePlayingTime(self) -> None:
        """
        更新当前音频的位置
        :return: None
        """
        if self.playingTime == 0:
            logger.info("开始更新播放位置")
        try:
            if self.playingTime < self.audioDuration:
                self.playingTime += 1
                self.playbackLabel.setText(self.formatSeconds(self.playingTime))
                self.progressSlider.setValue(self.playingTime)
            else:
                self.stopMusic()
                self.playing = False
                self.progressSlider.setValue(0)
                self.playOrPauseButton.setText("Play")
        except Exception as e:
            logger.error(f"更新失败：{e}")

    def formatSeconds(self, seconds) -> str:
        """
        将秒数转换分钟
        :param seconds: 秒数
        :return: str
        """
        minutes, seconds = divmod(seconds, 60)
        DuratonMinutes, DuratonSeconds = divmod(self.audioDuration, 60)
        return f"{minutes}:{seconds:02}/{DuratonMinutes}:{DuratonSeconds}"

    def initProgressSlider(self) -> None:
        cache = MusicPlayerCache(
            os.path.split(self.musicFile)[-1]
        )
        if cache:
            self.progressSlider.setValue(cache['playingTime'])
            self.playbackLabel.setText(
                self.formatSeconds(cache['playingTime'])
            )

    def updateProgressPlayingTime(self) -> None:
        """
        更新进度条的播放时间值
        :return: None
        """
        if self.music_process and self.music_process.poll() is None:
            new_time = self.progressSlider.value()
            if new_time != self.playingTime:
                self.stopMusic()
                self.timer.stop()
                self.playingTime = new_time
                MusicPlayerCache(
                    os.path.split(self.musicFile)[-1],
                    {"playingTime": self.playingTime},
                    rw=False
                )
                self.playbackLabel.setText(
                    self.formatSeconds(
                        self.progressSlider.value()
                    )
                )
                self.playMusic()
                self.timer.start(1000)
                logger.info(f"更新音乐进度条值：{self.playingTime}")
                self.visualizer.update_visualization(self.playingTime)
        else:
            self.playingTime = self.progressSlider.value()
            MusicPlayerCache(
                os.path.split(self.musicFile)[-1],
                {"playingTime": self.playingTime},
                rw=False
            )
            self.playbackLabel.setText(
                self.formatSeconds(
                    self.progressSlider.value()
                )
            )
            logger.info(f"更新音乐进度条值：{self.playingTime}")

    def closeEvent(self, event) -> None:
        self.stopMusic()
        if self.playingTime != 0:
            MusicPlayerCache(
                os.path.split(self.musicFile)[-1],
                {"playingTime": self.playingTime},
                rw=False
            )

    # 重写鼠标按下事件，以实现窗口的拖动
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_start_position:
            self.move(event.globalPos() - self.drag_start_position)
            event.accept()
    # end


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MusicPlayer("..\\EK-U - I Took A Pill In Lbiza (Remix).flac")#"D:\\Python_MX\\PyFusionInnovator\\temp.wav")
    player.show()
    sys.exit(app.exec_())
