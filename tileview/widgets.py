import os
from abc import abstractmethod

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout
from moviepy.video.io.VideoFileClip import VideoFileClip

import utils
from settings import TILES_THUMBNAIL_SIZE


class TileWidget(QtWidgets.QLabel):

    def __init__(self):
        super(TileWidget, self).__init__()

    def mouseDoubleClickEvent(self, e):
        self.doubleClicked.emit(self.file)

    @abstractmethod
    def set_file(self, file):
        """

        :param file:
        :return:
        """

    @abstractmethod
    def update_comment(self):
        """
        Update the comments
        :return: user_comment:  comment in the following dic form
        {
            'comments': Comments,
            'tags': list of tags in a single string format with whitespace as separator
        }
        """

    @abstractmethod
    def save_comment(self, user_comment):
        """
        If handled by the file format, save user_comment in the media file metadata
        :param user_comment:  comment in the following dic form
        {
            'comments': Comments,
            'tags': list of tags in a single string format with whitespace as separator
        }
        :return: None
        """


class UserCommentWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        vlay = QVBoxLayout()
        self.setLayout(vlay)
        self.title = QtWidgets.QLabel()
        self.text_widget = QtWidgets.QTextEdit()
        self.tags_widget = QtWidgets.QTextEdit()
        vlay.addWidget(self.title)
        vlay.addWidget(self.text_widget, 3)
        vlay.addWidget(QtWidgets.QLabel("Tags"))
        vlay.addWidget(self.tags_widget, 1)

        self._media_widget = None

    def update_comment(self, media_widget: TileWidget):
        self._media_widget = media_widget
        user_comment = media_widget.update_comment()
        if 'comments' in user_comment:
            self.text_widget.setText(user_comment['comments'])
        if 'tags' in user_comment:
            text = ""
            for tag in user_comment['tags']:
                text += tag + " "
            self.tags_widget.setText(text)
        self.title.setText(os.path.basename(media_widget.file))

    def save_comment(self):
        if self._media_widget is None: return

        user_comment = {
            'comments': self.text_widget.toPlainText(),
            'tags': self.tags_widget.toPlainText().split()
        }
        self._media_widget.save_comment(user_comment)


class ImageWidget(TileWidget):
    doubleClicked = pyqtSignal(str)

    def __init__(self, file):
        super(ImageWidget, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setObjectName(file)
        self.file = ''
        self.orig_pixmap = None
        self.set_file(file)

    def mouseDoubleClickEvent(self, e):
        self.doubleClicked.emit(self.file)

    def scaledToWidth(self, width):
        pixmap = self.orig_pixmap.scaledToWidth(int(width))
        self.setPixmap(pixmap)

    def set_file(self, file):
        if os.path.exists(file) and os.path.isfile(file):
            self.file = file
            qimage, _ = utils.load_image(self.file)
            self.orig_pixmap = QtGui.QPixmap().fromImage(qimage).scaledToWidth(TILES_THUMBNAIL_SIZE)
            # QtGui.QPixmap(file).scaledToWidth(TILES_THUMBNAIL_SIZE)
            if not self.orig_pixmap.isNull():
                self.setPixmap(self.orig_pixmap)

    def update_comment(self):
        user_comment = utils.get_exif_user_comment(self.file)
        return user_comment

    def save_comment(self, user_comment):
        exif_dic = utils.get_exif_v2(self.file)
        utils.update_user_comment(exif_dict=exif_dic, userdata=user_comment)
        utils.save_exif(exif_dict=exif_dic, filepath=self.file)


class VideoWidget(TileWidget):
    doubleClicked = pyqtSignal(str)

    def __init__(self, file):
        super(VideoWidget, self).__init__()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setObjectName(file)
        self.file = ''
        self.orig_pixmap = None
        self.set_file(file)

    def mouseDoubleClickEvent(self, e):
        self.doubleClicked.emit(self.file)

    def scaledToWidth(self, width):
        pixmap = self.orig_pixmap.scaledToWidth(int(width))
        self.setPixmap(pixmap)

    def set_file(self, file):
        if os.path.exists(file) and os.path.isfile(file):
            self.file = file
            clip = VideoFileClip(file, audio=False, fps_source='fps')
            qimage = utils.toQImage(clip.get_frame(0))
            self.orig_pixmap = QtGui.QPixmap().fromImage(qimage).scaledToWidth(TILES_THUMBNAIL_SIZE)
            if not self.orig_pixmap.isNull():
                self.setPixmap(self.orig_pixmap)

    def update_comment(self):
        return {}

    def save_comment(self, user_comment):
        pass
