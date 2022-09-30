import os
import sys

from PyQt5.QtCore import Qt, QUrl, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                             QSizePolicy, QSlider, QStyle, QVBoxLayout, QStatusBar)
from PyQt5.QtWidgets import QMainWindow, QWidget, QPushButton, QAction

from controller import MainController
from model import MainModel
from renamer.parsers import FILE_EXTENSION_VIDEO


class VideoPlayerWindow(QMainWindow):

    def __init__(self, model: MainModel, controller: MainController):
        super().__init__()
        self.setWindowTitle("Video Player")

        self._model = model
        self._controller = controller

        self.createMainLabel()
        self.createActionsShortcuts()
        self.createMenus()

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        # listen for model event
        # Model Event - selected image has changed
        self._model.selected_media_changed.connect(self.on_media_path_changed)

        self.setMinimumSize(300, 200)
        self.setWindowTitle("Video Player")
        self.showMaximized()
        self.setStatusBar(QStatusBar())
        self.setVisible(False)

        # Open selected video
        if self._model.media_path:
            ext = os.path.splitext(self._model.media_path)[1][1:]
            if ext in FILE_EXTENSION_VIDEO:
                self.open_media(file=self._model.media_path)
            else:
                self.setEnabled(False)

    def createMainLabel(self):
        self.btn_play = QPushButton()
        self.btn_play.setEnabled(False)
        self.btn_play.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.btn_play.clicked.connect(self.clip_play)

        self.btn_pause = QPushButton()
        self.btn_pause.setCheckable(True)
        self.btn_pause.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.btn_pause.clicked.connect(self.clip_pause)

        self.slider_frame = QSlider(Qt.Horizontal)
        self.slider_frame.setRange(0, 0)
        self.slider_frame.sliderMoved.connect(self.goto_frame)

        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred,
                                      QSizePolicy.Maximum)

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        media_widget = QVideoWidget()

        # Create a widget for window contents
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # Create layouts to place inside widget
        layout_buttons = QHBoxLayout()
        layout_buttons.setContentsMargins(0, 0, 0, 0)
        layout_buttons.addWidget(self.btn_play)
        layout_buttons.addWidget(self.btn_pause)
        layout_buttons.addWidget(self.slider_frame)

        layout = QVBoxLayout()
        layout.addWidget(media_widget)
        layout.addLayout(layout_buttons)
        layout.addWidget(self.errorLabel)

        # Set widget to contain window contents
        wid.setLayout(layout)

        self.mediaPlayer.setVideoOutput(media_widget)
        self.mediaPlayer.stateChanged.connect(self.on_media_state_changed)
        self.mediaPlayer.positionChanged.connect(self.on_slider_position_changed)
        self.mediaPlayer.durationChanged.connect(self.on_duration_changed)
        self.mediaPlayer.error.connect(self.handleError)

    def createActionsShortcuts(self):
        # Create new action
        self.openAction = QAction(QIcon('open.png'), '&Open', self)
        self.openAction.setShortcut('Ctrl+O')
        self.openAction.setStatusTip('Open movie')
        self.openAction.triggered.connect(self.open_media)

        # Create exit action
        self.exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(self.exitCall)

    def createMenus(self):
        # Create menu bar and add action
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        # fileMenu.addAction(newAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.exitAction)

    @pyqtSlot(str)
    def on_media_path_changed(self, path):
        ok = self.open_media(file=path)
        if ok or self.isVisible():
            self.show()

    def open_media(self, file=""):
        if file == "":
            file, _ = QFileDialog.getOpenFileName(self, "Open Movie")

        # Deactivate the img_editor if not a video
        ext = os.path.splitext(file)[1][1:]
        if ext in FILE_EXTENSION_VIDEO:
            self.mediaPlayer.setMedia(
                QMediaContent(QUrl.fromLocalFile(file)))
            self.btn_play.setEnabled(True)
            self.clip_play()
            return True
        else:
            self.setEnabled(False)
            return False

    def exitCall(self):
        pass
        # sys.exit(app.exec_())

    def clip_play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def clip_pause(self):
        self.mediaPlayer.pause()

    def on_media_state_changed(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.btn_play.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.btn_play.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay))

    def on_slider_position_changed(self, position):
        self.slider_frame.setValue(position)

    def on_duration_changed(self, duration):
        self.slider_frame.setRange(0, duration)

    def goto_frame(self, position):
        self.mediaPlayer.setPosition(position)

    def handleError(self):
        self.btn_play.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoPlayerWindow()
    player.resize(640, 480)
    player.show()
    sys.exit(app.exec_())
