import os

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout
from moviepy.video.io.VideoFileClip import VideoFileClip

import utils
from views.common import MediaWithMetadata


class UserCommentWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        vlay = QVBoxLayout()
        self.setLayout(vlay)
        self.title = QtWidgets.QLabel()
        self.text_widget = QtWidgets.QTextEdit()
        self.tags_widget = QtWidgets.QTextEdit()
        self.persons_widget = QtWidgets.QTextEdit()
        vlay.addWidget(self.title)
        vlay.addWidget(self.text_widget, 3)
        vlay.addWidget(QtWidgets.QLabel("Tags"))
        vlay.addWidget(self.tags_widget, 1)
        vlay.addWidget(QtWidgets.QLabel("Persons"))
        vlay.addWidget(self.persons_widget, 1)

    def update_from_comment(self, user_comment, file=None):
        self.text_widget.setText(user_comment.comments)
        text = ""
        for tag in user_comment.tags:
            text += tag + " "
        self.tags_widget.setText(text)
        text = ""
        for tag in user_comment.persons:
            text += tag + " "
        self.persons_widget.setText(text)
        if file:
            self.title.setText(os.path.basename(file))

    def get_comment(self):
        return utils.ImageUserComment(comments=self.text_widget.toPlainText(),
                                      tags=self.tags_widget.toPlainText().split(),
                                      persons=self.persons_widget.toPlainText().split())


class ImageWidget(QtWidgets.QWidget, MediaWithMetadata):
    doubleClicked = pyqtSignal(str)

    def __init__(self, file, config=None):
        QtWidgets.QWidget.__init__(self)

        self.thumbnail_size = config["TILES_THUMBNAIL_SIZE"] if config else 800
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setObjectName(file)
        self.file = ''
        self.orig_pixmap = None

        self.img_label = QtWidgets.QLabel(self)
        self.file_label = QtWidgets.QLabel(self)
        # Main Layout
        layout_main = QVBoxLayout(self)
        layout_main.setAlignment(Qt.AlignTop)
        layout_main.addWidget(self.img_label)
        layout_main.addWidget(self.file_label)
        self.setLayout(layout_main)

        self.open_media(file)

    def mouseDoubleClickEvent(self, e):
        self.doubleClicked.emit(self.file)

    def scaledToWidth(self, width):
        pixmap = self.orig_pixmap.scaledToWidth(int(width))
        self.img_label.setPixmap(pixmap)

    def open_media(self, file, **kwargs):
        if os.path.exists(file) and os.path.isfile(file):
            self.file = file
            qimage, _ = utils.load_image(self.file)
            self.orig_pixmap = QtGui.QPixmap().fromImage(qimage).scaledToWidth(self.thumbnail_size)
            # QtGui.QPixmap(file).scaledToWidth(TILES_THUMBNAIL_SIZE)
            if not self.orig_pixmap.isNull():
                self.img_label.setPixmap(self.orig_pixmap)
                self.file_label.setText(os.path.basename(file))

    def save_media(self, file, **kwargs):
        pass

    def load_comment(self):
        user_comment = utils.ImageUserComment.load_from_file(self.file)
        return user_comment

    def save_comment(self, user_comment, file=None):
        exif_dic = utils.get_exif_v2(self.file)
        user_comment.update_exif(exif_dic)
        utils.save_exif(exif_dict=exif_dic, filepath=self.file)


class VideoWidget(QtWidgets.QWidget, MediaWithMetadata):
    doubleClicked = pyqtSignal(str)

    def __init__(self, file, config=None):
        QtWidgets.QWidget.__init__(self)

        self.thumbnail_size = config["TILES_THUMBNAIL_SIZE"] if config else 800
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setObjectName(file)
        self.file = ''
        self.orig_pixmap = None

        self.img_label = QtWidgets.QLabel(self)
        self.file_label = QtWidgets.QLabel(self)

        # Main Layout
        layout_main = QVBoxLayout(self)
        layout_main.setAlignment(Qt.AlignTop)
        layout_main.addWidget(self.img_label)
        layout_main.addWidget(self.file_label)
        self.setLayout(layout_main)

        self.open_media(file)

    def mouseDoubleClickEvent(self, e):
        self.doubleClicked.emit(self.file)

    def scaledToWidth(self, width):
        pixmap = self.orig_pixmap.scaledToWidth(int(width))
        self.img_label.setPixmap(pixmap)

    def open_media(self, file, **kwargs):
        if os.path.exists(file) and os.path.isfile(file):
            self.file = file
            clip = VideoFileClip(file, audio=False, fps_source='fps')
            qimage = utils.toQImage(clip.get_frame(0))
            self.orig_pixmap = QtGui.QPixmap().fromImage(qimage).scaledToWidth(self.thumbnail_size)
            if not self.orig_pixmap.isNull():
                self.img_label.setPixmap(self.orig_pixmap)
                self.file_label.setText(os.path.basename(file))

    def save_media(self, file, **kwargs):
        pass

    def load_comment(self):
        user_comment = utils.VideoUserComment.load_from_file(self.file)
        return user_comment

    def save_comment(self, user_comment, file=None):
        pass
