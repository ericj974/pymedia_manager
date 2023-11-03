from pathlib import Path

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout
from moviepy.video.io.VideoFileClip import VideoFileClip

import common.comment
import common.cv
from common.widgets import PersonTagWidget, MediaWithMetadata, TagBar


class PersonsTextEdit(QtWidgets.QTextEdit):
    def __init__(self, persons=None):
        super(PersonsTextEdit, self).__init__()
        # Persons entities
        self.persons: list[common.comment.PersonEntity] = []
        if persons:
            self.set_entities(persons)

    def set_entities(self, persons):
        self.persons: list[common.comment.Entity] = persons
        text = ""
        for tag in persons:
            text += tag.name + " "
        self.setText(text)

    def get_entities(self) -> list[common.comment.PersonEntity]:
        return self.persons


class UserCommentWidget(QtWidgets.QWidget):
    def __init__(self, model=None, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        vlay = QVBoxLayout()
        self.setLayout(vlay)
        self.title = QtWidgets.QLabel()

        self.comment_widget = QtWidgets.QTextEdit()

        known_tags = model.db_tags.tags if model else []
        self.tags_widget = TagBar(known_tags=known_tags)
        self.persons_widget = PersonTagWidget()

        vlay.addWidget(self.title)
        vlay.addWidget(self.comment_widget, 3)
        vlay.addWidget(QtWidgets.QLabel("Tags"))
        vlay.addWidget(self.tags_widget, 1)
        vlay.addWidget(QtWidgets.QLabel("Persons"))
        vlay.addWidget(self.persons_widget, 1)
        self.user_comment = None

    def set_user_comment(self, user_comment: common.comment.UserComment, path: Path = None):
        self.user_comment = user_comment

        # Generic comment
        text = user_comment.comment.data if user_comment.comment else ""
        self.comment_widget.setText(text)
        # Tags
        self.tags_widget.set_entities(user_comment.tags)
        # Persons' tag
        self.persons_widget.set_entities(user_comment.persons)
        if path:
            self.title.setText(path.name)

    def get_user_comment(self):
        entity_comment = [common.comment.CommentEntity(content=self.comment_widget.toPlainText())]
        entity_tag = self.tags_widget.get_entities()
        entity_person = self.persons_widget.get_entities()
        entities = entity_comment + entity_tag + entity_person
        return common.comment.ImageUserComment(entities)


class ImageWidget(QtWidgets.QWidget, MediaWithMetadata):
    doubleClicked = pyqtSignal(Path)

    def __init__(self, file: Path, config=None):
        QtWidgets.QWidget.__init__(self)

        self.thumbnail_size = config["TILES_THUMBNAIL_SIZE"] if config else 800
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setObjectName(str(file))
        self.file = None
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

    def open_media(self, path: Path, **kwargs):
        if not path.is_file():
            return

        self.file = path
        qimage, _ = common.cv.load_image(self.file)
        self.orig_pixmap = QtGui.QPixmap().fromImage(qimage).scaledToWidth(self.thumbnail_size)
        # QtGui.QPixmap(file).scaledToWidth(TILES_THUMBNAIL_SIZE)
        if not self.orig_pixmap.isNull():
            self.img_label.setPixmap(self.orig_pixmap)
            self.file_label.setText(path.name)

    def save_media(self, file, **kwargs):
        pass


class VideoWidget(QtWidgets.QWidget, MediaWithMetadata):
    doubleClicked = pyqtSignal(Path)

    def __init__(self, file, config=None):
        QtWidgets.QWidget.__init__(self)

        self.thumbnail_size = config["TILES_THUMBNAIL_SIZE"] if config else 800
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setObjectName(str(file))
        self.file = None
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

    def open_media(self, path: Path, **kwargs):
        if not path.is_file():
            return

        self.file = path
        clip = VideoFileClip(str(path), audio=False, fps_source='fps')
        qimage = common.cv.toQImage(clip.get_frame(0))
        self.orig_pixmap = QtGui.QPixmap().fromImage(qimage).scaledToWidth(self.thumbnail_size)
        if not self.orig_pixmap.isNull():
            self.img_label.setPixmap(self.orig_pixmap)
            self.file_label.setText(path.name)

    def save_media(self, file, **kwargs):
        pass
