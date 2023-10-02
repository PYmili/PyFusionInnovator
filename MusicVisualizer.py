import sys
import numpy as np
from pydub import AudioSegment
from loguru import logger
from PyQt5.QtWidgets import (
    QApplication, QMainWindow,
    QWidget,
    QVBoxLayout,
)
from PyQt5.QtCore import QTimer
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

# AudioSegment.converter = "D:\\Programs\\ffmpeg\\bin\\ffmpeg.exe"
# AudioSegment.ffmpeg = "D:\\Programs\\ffmpeg\\bin\\ffmpeg.exe"
# AudioSegment.ffprobe = "D:\\Programs\\ffmpeg\\bin\\ffprobe.exe"


class AudioVisualizer(QMainWindow):
    """用于显示音频，音乐可视化"""
    def __init__(self, wavFile: str):
        """
        :param wavFile: wav文件的路径
        """
        super().__init__()
        logger.info(f"开始初始化可视化类")
        self.wavFile = wavFile
        self.sound = AudioSegment.from_file(
            file=self.wavFile
        )
        self.playing = False
        self.start_time = 0  # 新增变量来存储开始时间
        self.fill_area = None

        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)

        self.layout = QVBoxLayout(self.centralWidget)

        # 创建 Matplotlib 图形用于绘制音频数据
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        self.LeftVocalTract = self.sound.split_to_mono()[0]
        self.FileSamplingRate = self.LeftVocalTract.frame_rate
        self.NumberOfSamples = len(self.LeftVocalTract.get_array_of_samples())
        self.windowSize = int(0.02 * self.FileSamplingRate)
        self.splitWindow = self.windowSize // 8
        # self.FrequencyAxis = np.linspace(20, 20 * 1000, self.splitWindow)
        self.FrequencyAxis = np.linspace(
            -self.FileSamplingRate / 2,
            self.FileSamplingRate / 2,
            self.splitWindow
        )
        self.timeAxis = np.linspace(0, 1, self.windowSize)
        self.color_grade = ['blue', 'yellow', 'red']
        self.LineObject = None
        self.frames = 0

        # 定时更新图像任务
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        logger.info(f"可视化类初始化完成")

    def update_visualization(self, value) -> None:
        """
        更新可视化要读取文件位置
        :param value: 文件的秒数
        :return: None
        """
        self.start_time = value
        if self.playing:
            self.stop_visualization()
        self.start_visualization()
        logger.info("成功更新可视化数据")

    def start_visualization(self) -> None:
        """
        启动可视化
        :return: None
        """
        logger.info(f"启动可视化")
        self.playing = True
        self.figure.clear()
        self.ax1 = self.figure.add_subplot(111)
        self.ax1.set_ylim(0, 2)
        self.ax1.set_axis_off()

        # 设置坐标和大小以填充整个self.figure
        self.ax1.set_position([0, 0, 1, 1])

        # 创建波浪线
        self.LineObject, = self.ax1.plot(self.FrequencyAxis, np.zeros(self.splitWindow), lw=1)
        self.LineObject.set_antialiased(True)

        # 启动定时任务
        self.timer.start(19)

        # 初始化填充区域
        if self.fill_area is not None:
            self.fill_area.remove()
        self.fill_area = self.ax1.fill_between(
            self.FrequencyAxis,
            0,
            np.zeros(self.splitWindow),
            color='blue',
            alpha=0
        )
        logger.info(f"可视化启动成功")

    def stop_visualization(self) -> None:
        """
        停止可视化
        :return: None
        """
        self.playing = False
        if self.timer.isActive():
            self.timer.stop()
        logger.info("成功停止可视化")

    def update(self) -> None:
        """
        定时更新可视化任务
        :return:
        """
        start_frame = int(self.start_time * self.FileSamplingRate)
        end_frame = start_frame + self.windowSize

        # 在窗口开始之前和窗口结束之后添加零值样本
        if start_frame > 0:
            start_frame -= int(self.windowSize)
        if end_frame < len(self.LeftVocalTract.get_array_of_samples()):
            end_frame += int(self.windowSize)

        # 截取样本
        slice = self.LeftVocalTract.get_sample_slice(start_frame, end_frame)
        y = np.array(slice.get_array_of_samples()) / 30000
        # 检查窗口大小是否有效
        if len(y) < self.windowSize:
            return
        yft = np.abs(np.fft.fft(y)) / (self.splitWindow)
        grade = int(max(yft[:self.splitWindow]) - min(yft[:self.splitWindow]))

        # 更新波浪线和填充区域
        self.LineObject.set_ydata(yft[:self.splitWindow])
        self.fill_area.remove()  # 移除之前的填充区域

        if 0 <= grade < len(self.color_grade):
            self.LineObject.set_color(self.color_grade[grade])
            self.fill_area = self.ax1.fill_between(
                self.FrequencyAxis,
                0,
                yft[:self.splitWindow],
                color=self.color_grade[grade],
                alpha=0.5
            )
        else:
            self.fill_area = self.ax1.fill_between(
                self.FrequencyAxis,
                0,
                yft[:self.splitWindow],
                color="blue",
                alpha=0.5
            )
        self.LineObject.set_ydata(yft[:self.splitWindow])
        self.canvas.draw()
        self.start_time += self.windowSize / self.FileSamplingRate

    def format_to_wav(self) -> str:
        """将音频文件转换为.wav格式并返回转换后的文件路径"""
        wavFile = self.wavFile.replace(".mp3", ".wav")  # 将.mp3扩展名替换为.wav
        sound = AudioSegment.from_file(file=self.wavFile)

        if not sound.sample_width == 2:
            sound = sound.set_sample_width(2)

        if not sound.frame_rate == 44100:
            sound = sound.set_frame_rate(44100)

        sound.export(wavFile, format="wav")  # 导出为.wav文件

        return wavFile


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AudioVisualizer()
    ex.start_visualization()
    ex.show()
    sys.exit(app.exec_())
