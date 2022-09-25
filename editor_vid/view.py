import os
import sys

from PyQt5 import QtMultimedia
from PyQt5.QtCore import Qt, QUrl, pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                             QSizePolicy, QSlider, QStyle, QVBoxLayout)
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

        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        videoWidget = QVideoWidget()

        self.setAttribute(Qt.WA_DeleteOnClose, True)
        # listen for model event
        # Model Event - selected image has changed
        self._model.selected_media_changed.connect(self.on_media_path_changed)

        self.playButton = QPushButton()
        self.playButton.setEnabled(False)
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.clicked.connect(self.play)

        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.setPosition)

        self.errorLabel = QLabel()
        self.errorLabel.setSizePolicy(QSizePolicy.Preferred,
                                      QSizePolicy.Maximum)

        # Create new action
        openAction = QAction(QIcon('open.png'), '&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Open movie')
        openAction.triggered.connect(self.open_media)

        # Create exit action
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.exitCall)

        # Create menu bar and add action
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        # fileMenu.addAction(newAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)

        # Create a widget for window contents
        wid = QWidget(self)
        self.setCentralWidget(wid)

        # Create layouts to place inside widget
        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0, 0, 0, 0)
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)

        layout = QVBoxLayout()
        layout.addWidget(videoWidget)
        layout.addLayout(controlLayout)
        layout.addWidget(self.errorLabel)

        # Set widget to contain window contents
        wid.setLayout(layout)

        self.mediaPlayer.setVideoOutput(videoWidget)
        self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.durationChanged)
        self.mediaPlayer.error.connect(self.handleError)

        # Open selected image
        if self._model.media_path:
            ext = os.path.splitext(self._model.media_path)[1][1:]
            if ext in FILE_EXTENSION_VIDEO:
                self.open_media(file=self._model.media_path)
            else:
                self.setEnabled(False)

    @pyqtSlot(str)
    def on_media_path_changed(self, path):
        self.open_media(file=path)
        self.show()

    def open_media(self, file=""):
        if file == "":
            file, _ = QFileDialog.getOpenFileName(self, "Open Movie")

        # Deactivate the editor_img if not a video
        ext = os.path.splitext(file)[1][1:]
        if ext in FILE_EXTENSION_VIDEO:
            self.mediaPlayer.setMedia(
                QMediaContent(QUrl.fromLocalFile(file)))
            self.playButton.setEnabled(True)
            self.play()
        else:
            self.setEnabled(False)
            return

    def exitCall(self):
        pass
        # sys.exit(app.exec_())

    def play(self):
        img = self.mediaPlayer.metaData(QtMultimedia.QMediaMetaData.ThumbnailImage)
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playButton.setIcon(
                self.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionSlider.setValue(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def handleError(self):
        self.playButton.setEnabled(False)
        self.errorLabel.setText("Error: " + self.mediaPlayer.errorString())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = VideoPlayerWindow()
    player.resize(640, 480)
    player.show()
    sys.exit(app.exec_())
