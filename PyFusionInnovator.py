import os
import sys
import atexit
import datetime
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFrame
)
from PyQt5.QtCore import QSize
from loguru import logger

PATH = os.path.split(__file__)[0]


class LeftMenuButton(QPushButton):
    """自定义左侧菜单按钮"""
    def __init__(self, text):
        super().__init__(text)
        self.setCheckable(True)  # 设置按钮可被选中
        self.setStyleSheet(
            """
            QPushButton {
                border: none;
                text-align: center;
                padding: 10px;
                font-size: 14px;
                font-weight: normal;  /* 控制字体粗细，可以改为 bold 或其他值 */
                font-family: Arial;   /* 控制字体类型，可以根据需要更改 */
            }

            QPushButton:checked {
                background-color: lightblue;
                border-Left: 5px solid blue;  /* 左侧竖杠效果 */
                font-weight: bold;
                font-size: 16px;
                color: blue;
            }

            QPushButton:hover {
                background-color: lightgray;
            }
            """
        )

    def toggleChecked(self) -> None:
        """在按钮被点击时，切换选中状态"""
        self.setChecked(not self.isChecked())
        if self.isChecked():
            self.setFixedSize(QSize(120, 36))  # 设置放大后的大小
        else:
            self.setFixedSize(QSize(100, 30))  # 恢复正常大小


class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        logger.info("初始化主窗口")
        super().__init__()
        self.setWindowTitle("Main Window")
        self.setGeometry(100, 100, 800, 600)

        # 创建玻璃模糊效果
        # self.setStyleSheet("background: rgba(255, 255, 255, 100);")
        # self.setWindowOpacity(0.90)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(main_layout)

        left_menu = QVBoxLayout()

        musicLeftButton = LeftMenuButton("音乐")
        videoLeftButton = LeftMenuButton("视频")
        imageLeftButton = LeftMenuButton("图片")

        left_menu.addWidget(musicLeftButton)
        left_menu.addWidget(videoLeftButton)
        left_menu.addWidget(imageLeftButton)

        right_layout = QVBoxLayout()

        self.display_area = QFrame()
        self.display_area.setStyleSheet("background-color: lightgray;")

        function_area = QFrame()
        function_area.setStyleSheet("background-color: lightblue;")

        right_layout.addWidget(self.display_area)
        right_layout.setSpacing(0)
        right_layout.addWidget(function_area)
        right_layout.setStretch(right_layout.indexOf(self.display_area), 10)
        right_layout.setStretch(right_layout.indexOf(function_area), 1)

        main_layout.addLayout(left_menu, 1)
        main_layout.addLayout(right_layout, 9)

        # 连接按钮的点击事件
        musicLeftButton.clicked.connect(lambda: self.setLastSelectedButton(musicLeftButton))
        videoLeftButton.clicked.connect(lambda: self.setLastSelectedButton(videoLeftButton))
        imageLeftButton.clicked.connect(lambda: self.setLastSelectedButton(imageLeftButton))

        # 记录最后一个选中的按钮
        self.last_selected_button = None
        logger.info("成功初始化主窗口")

    def setLastSelectedButton(self, button) -> None:
        """
        设置左侧按钮的样式及切换窗口
        :param button: LeftMenuButton(QPushButton)
        :return: None
        """
        if self.last_selected_button is not None:
            self.last_selected_button.setChecked(False)  # 清除上一个按钮的选中状态
            self.last_selected_button.setFixedSize(QSize(100, 40))  # 恢复上一个按钮的大小

        button.setChecked(True)  # 设置当前按钮为选中状态
        button.setFixedSize(QSize(120, 40))  # 设置当前选中按钮的大小
        self.last_selected_button = button  # 更新最后一个选中的按钮

        # 根据按钮选择来显示界面内容
        if button.text() == "音乐":
            self.display_area.setStyleSheet("background-color: lightgray;")
        elif button.text() == "视频":
            self.display_area.setStyleSheet("background-color: lightblue;")
        elif button.text() == "图片":
            self.display_area.setStyleSheet("background-color: lightgreen;")


def on_exit() -> None:
    logger.info("程序结束")


if __name__ == "__main__":
    # 使用当前时间戳来生成不同的日志文件名
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{os.path.join(PATH, 'log')}/latest_{current_time}.log"
    logger.add(log_file, rotation="10mb")

    app = QApplication(sys.argv)
    logger.info("启动程序")
    window = MainWindow()
    window.show()
    atexit.register(on_exit)
    sys.exit(app.exec_())
