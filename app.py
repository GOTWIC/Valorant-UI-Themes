from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QSlider, QVBoxLayout, QCheckBox, QLabel, QFileDialog, QStackedLayout
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QBrush, QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer
import sys
import numpy as np
from ctypes import windll
import ffmpeg


class VideoOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.enable_click_through()
        self.showFullScreen()
        self.process = None
        self.frame = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
    def enable_click_through(self):
        hwnd = self.winId().__int__()
        WS_EX_LAYERED = 0x00080000
        WS_EX_TRANSPARENT = 0x00000020
        current_style = windll.user32.GetWindowLongW(hwnd, -20)
        windll.user32.SetWindowLongW(hwnd, -20, current_style | WS_EX_LAYERED | WS_EX_TRANSPARENT)

    def play_video(self, path): 
        if self.process:
            self.process.kill()
        self.current_video_path = path
        self.process = (
            ffmpeg
            .input(path)
            .output('pipe:', format='rawvideo', pix_fmt='rgba')
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )
        self.timer.start(30)

    def stop_video(self):
        if self.process:
            self.process.kill()
            self.process = None
        self.timer.stop()
        self.frame = None
        self.update()

    def update_frame(self):
        if self.process:
            width, height = 1920, 1080
            frame_size = width * height * 4
            raw_frame = self.process.stdout.read(frame_size)

            if len(raw_frame) < frame_size:
                self.process.stdout.close()
                self.process.wait()
                self.play_video(self.current_video_path)
                return

            frame = np.frombuffer(raw_frame, np.uint8).reshape((height, width, 4)).copy()
            
            # TEMPORARY
            #frame = self.remove_middle_region(frame)
            
            self.frame = frame
            self.update()


    def paintEvent(self, event):
        if self.frame is not None:
            painter = QPainter(self)
            height, width, _ = self.frame.shape
            q_img = QImage(self.frame.data, width, height, width * 4, QImage.Format_RGBA8888)
            pixmap = QPixmap.fromImage(q_img).scaled(self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(0, 0, pixmap)
            
    def remove_middle_region(self, frame, region_size=30):
        height, width, _ = frame.shape
        center_x, center_y = width // 2, height // 2
        half_size = region_size // 2

        # Set alpha channel to 0 in the 30x30 center region
        frame[
            center_y - half_size : center_y + half_size,
            center_x - half_size : center_x + half_size,
            3
        ] = 0
        return frame




class ValorantThemeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.video_overlay = VideoOverlay()
        self.video_overlay.hide()
        self.theme = None
        self.init_ui()

    def openCrosshairFileDialog(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Crosshair File", "", "All Files (*);;Text Files (*.txt)")
        if fileName:
            print("Selected file:", fileName)
            self.checkBox_crosshair_enabled.setChecked(True)

    def openThemeFileDialog(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Theme Video File", "", "Video Files (*.mp4 *.avi *.mkv *.mov)")
        if fileName:
            self.theme = fileName
            self.checkBox_theme_enabled.setChecked(True)
            if self.checkBox_theme_enabled.isChecked():
                self.play_theme_video()

    def toggle_theme_video(self, state):
        if state == Qt.Checked and self.theme:
            self.play_theme_video()
        else:
            self.stop_theme_video()

    def play_theme_video(self):
        self.video_overlay.show()
        self.video_overlay.play_video(self.theme)

    def stop_theme_video(self):
        self.video_overlay.stop_video()
        self.video_overlay.hide()

    def init_ui(self):
        self.setWindowTitle('♡ Val UI ♡')
        self.setFixedSize(400, 350)

        self.primary_color = 'rgb(255, 230, 235)'
        self.secondary_color = 'rgb(220, 180, 250)'
        self.font_family = 'Comic Sans MS'
        self.font_size = 18
        
        self.button_stylesheet = f"""
            QPushButton {{
                color: {self.primary_color};
                border-radius: 5px;
                background-color: rgba(220, 220, 220, 64);
                font-family: {self.font_family};
                font-size: {self.font_size}px;
            }}
            QPushButton:pressed {{
                background-color: rgba(180, 170, 200, 64);
            }}
            """

        font_style = f"font-family: {self.font_family}; font-size: {self.font_size}px;"

        btn_import_cross_hair = QPushButton('Import Crosshair')
        btn_import_cross_hair.setStyleSheet(self.button_stylesheet)
        btn_import_cross_hair.setFixedSize(160, 35)
        btn_import_cross_hair.clicked.connect(self.openCrosshairFileDialog)

        checkBox_crosshair_enabled = QCheckBox('Enabled')
        checkBox_crosshair_enabled.setStyleSheet(f"{font_style} color: {self.primary_color};")

        slider = QSlider(Qt.Vertical)
        slider.setMinimum(-30)
        slider.setMaximum(0)
        slider.setValue(0)
        slider.setTickInterval(1)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setFixedWidth(50)
        slider.setFixedHeight(200)
        slider.setStyleSheet(f"""
            QSlider::groove:vertical {{
                border: 1px solid #FFC0CB;
                background: {self.primary_color};
                width: 8px;
                border-radius: 5px;
                margin: 2px 0;  /* Adds space at top and bottom to prevent cutoff */
            }}
            QSlider::sub-page:vertical {{
                background: {self.primary_color};
                border-radius: 4px;
            }}
            QSlider::add-page:vertical {{
                background: {self.primary_color};
                border-radius: 4px;
            }}
            QSlider::handle:vertical {{
                background: rgb(100, 40, 120);  /* Dark purple */
                border: 1px solid #5E2B87;
                height: 12px;
                width: 12px;
                margin: -3px;  /* Aligns the smaller handle within the groove */
                border-radius: 6px;  /* Perfect circle: radius = width/2 */
            }}
            QSlider::handle:vertical:hover {{
                background: rgb(120, 60, 140);  /* Slightly lighter purple on hover */
            }}
            QSlider::tick-mark:vertical {{
                background: rgb(255, 105, 180);  /* Dark pink for rungs */
                width: 2px;
                height: 6px;
            }}
        """)

        label_offset = QLabel('Offset')
        label_offset.setStyleSheet(f"{font_style} color: {self.secondary_color};")
        label_slider_value = QLabel('0')
        label_slider_value.setStyleSheet(f"{font_style} color: {self.secondary_color};")
        slider.valueChanged.connect(lambda value: label_slider_value.setText(str(value)))

        hbox_slider = QHBoxLayout()
        hbox_slider.addWidget(label_offset, 0, Qt.AlignCenter)
        hbox_slider.addWidget(slider, 0, Qt.AlignCenter)
        hbox_slider.addWidget(label_slider_value, 0, Qt.AlignCenter)
        hbox_slider.setSpacing(10)

        btn_import_theme = QPushButton('Import Theme')
        btn_import_theme.setStyleSheet(self.button_stylesheet)
        btn_import_theme.setFixedSize(160, 35)
        btn_import_theme.clicked.connect(self.openThemeFileDialog)

        self.checkBox_theme_enabled = QCheckBox(' Enabled ')
        self.checkBox_theme_enabled.setStyleSheet(f"{font_style} color: {self.primary_color};")
        self.checkBox_theme_enabled.stateChanged.connect(self.toggle_theme_video)

        checkBox_animated = QCheckBox('Animated')
        checkBox_animated.setStyleSheet(f"{font_style} color: {self.primary_color};")

        vbox1 = QVBoxLayout()
        vbox1.addWidget(btn_import_cross_hair, 0, Qt.AlignCenter)
        vbox1.addWidget(checkBox_crosshair_enabled, 0, Qt.AlignCenter)
        vbox1.addLayout(hbox_slider)
        vbox1.setSpacing(30)
        vbox1.addStretch(1)

        vbox2 = QVBoxLayout()
        vbox2.addWidget(btn_import_theme, 0, Qt.AlignCenter)
        vbox2.addWidget(self.checkBox_theme_enabled, 0, Qt.AlignCenter)
        vbox2.addWidget(checkBox_animated, 0, Qt.AlignCenter)
        vbox2.setSpacing(30)
        vbox2.addStretch(1)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox1)
        hbox.addLayout(vbox2)

        container = QWidget()
        container.setLayout(hbox)

        main_layout = QStackedLayout(self)
        main_layout.addWidget(container)
        self.setLayout(main_layout)

        self.show()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor(8, 16, 32))
        gradient.setColorAt(1, QColor(54, 24, 54))

        brush = QBrush(gradient)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ValorantThemeApp()
    sys.exit(app.exec_())
