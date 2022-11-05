import copy
import os

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QStatusBar, QHBoxLayout, QAction

import utils
from constants import FILE_EXTENSION_VIDEO, FILE_EXTENSION_PHOTO
from controller import MainController
from model import MainModel
from views.tileview.widgets import UserCommentWidget, ImageWidget, VideoWidget


class MainTileWindow(QtWidgets.QMainWindow):
    def __init__(self, config=None, parent=None, model: MainModel = None, controller: MainController = None):
        super(MainTileWindow, self).__init__(parent)
        self.setWindowTitle("Tile View")
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        # MVC model
        self._model = model
        self._controller = controller

        # listen for model event signals
        self._model.selected_dir_changed.connect(self.on_dirpath_changed)
        self._model.selected_media_changed.connect(self.on_selected_media_changed)
        self._model.selected_dir_content_changed.connect(self.on_watcher_dir_changed)
        self._model.selected_file_content_changed.connect(self.on_watcher_file_changed)
        self._model.selected_media_comment_updated.connect(self.on_model_comment_updated)

        # Max col settings for the gridlayout
        self.max_col = config["MAX_COL"] if config else 3
        # Available position in the grid layout
        self._col_idx = 0
        self._row_idx = 0
        # List of file to process (widget creation and placement)
        self._files_to_process = None
        # Path -> widget dict
        self.media_widgets = {}
        # Current selected file
        self.file = ''

        # Tiles widget
        self.scrollArea = QtWidgets.QScrollArea(widgetResizable=True)
        self.content_widget = QtWidgets.QWidget()
        self.scrollArea.setWidget(self.content_widget)
        self._layout = QtWidgets.QGridLayout()
        self.content_widget.setLayout(self._layout)

        # Side Comment widget
        self.comment_widget = UserCommentWidget()
        self.comment_widget.resize(self.size() * 1 / 4)

        # Set the central Widget
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.scrollArea, 3)
        self.layout.addWidget(self.comment_widget, 1)
        self.central_widget = QtWidgets.QWidget()
        self.central_widget.setLayout(self.layout)
        self.setCentralWidget(self.central_widget)

        # Timer for loading the images (avoid freeze)
        self._timer = QtCore.QTimer(self, interval=1)
        self._timer.timeout.connect(self.on_timeout_process_next_file)

        # Menu Actions
        self.save_user_comment = QAction("Save user comment / tags...", self)
        self.save_user_comment.setShortcut('Ctrl+S')
        self.save_user_comment.triggered.connect(self._save_user_comment)
        self.delete_thumbnails = QAction("Delete embedded thumbnails...", self)
        self.delete_thumbnails.triggered.connect(self._delete_thumbnails)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        file_menu.addAction(self.save_user_comment)
        tools_menu = menubar.addMenu("Tools")
        tools_menu.addAction(self.delete_thumbnails)

        # Initial window size
        self.resize(QGuiApplication.primaryScreen().availableSize() * 3 / 5)
        self.setStatusBar(QStatusBar())

    def _save_user_comment(self):
        comment = self.comment_widget.get_comment()
        self._controller.update_media_comment(comment=comment)
        self._controller.save_media_comment()

    def _delete_thumbnails(self):
        for file in self._model.files:
            exif_dict = utils.get_exif_v2(file)
            if 'thumbnail' in exif_dict and exif_dict['thumbnail'] is not None:
                del exif_dict['thumbnail']
            utils.save_exif(exif_dict, filepath=file)

    def _reset_state(self):
        self._timer.stop()
        self._col_idx = 0
        self._row_idx = 0
        for widget in self.media_widgets.values():
            self._layout.removeWidget(widget)
            widget.close()
        self.media_widgets = {}

    def set_dirpath(self, dirpath):
        if dirpath == '':
            return
        self._reset_state()
        self._files_to_process = copy.deepcopy(self._model.files)
        self._timer.start()

    def update_dirpath_content(self):
        # Make sure not conflict with if we're populating the files
        self._timer.stop()

        files_it = self._model.files
        key_to_del = []  # List of filepaths that dont exist anymore
        for widget in self.media_widgets.values():
            self._layout.removeWidget(widget)
            if widget.file not in files_it:
                key_to_del.append(widget.file)
                widget.close()
        for key in key_to_del:
            del self.media_widgets[key]

        self._col_idx = 0
        self._row_idx = 0
        self._files_to_process = copy.deepcopy(self._model.files)
        self._timer.start()

    def resizeEvent(self, event):
        self.resize_widgets()
        QtWidgets.QMainWindow.resizeEvent(self, event)

    @pyqtSlot(str)
    def on_dirpath_changed(self, dirpath):
        self.set_dirpath(dirpath)

    @pyqtSlot(str)
    def on_selected_media_changed(self, file):
        self.file = file
        # No more selected image
        if file == '':
            return
        # Make sure we reload the selected filepath, in case the signal is emitted because the image has been modified
        if file in self.media_widgets:
            self.media_widgets[file].open_media(file)
            self.media_widgets[file].scaledToWidth(self.scrollArea.size().width() / self.max_col)
            # Scroll down to the selected image
            posy = self.scrollArea.findChild(QtWidgets.QWidget, file).pos().y()
            self.scrollArea.verticalScrollBar().setValue(posy)
        else:
            # Seems like a file has been added (or a rename)
            self.update_dirpath_content()

    @pyqtSlot(utils.UserComment)
    def on_model_comment_updated(self):
        # Display the comment
        self.comment_widget.update_from_comment(self._model.media_comment, self.file)

    def on_timeout_process_next_file(self):
        try:
            file = self._files_to_process.pop(0)
            self._add_media_widget(file)
        except IndexError:
            self._timer.stop()
            # Scroll down to the selected image
            filepath = self._model.media_path
            try:
                posy = self.scrollArea.findChild(QtWidgets.QLabel, filepath).pos().y()
                self.scrollArea.verticalScrollBar().setValue(posy)
            except:
                pass

    @pyqtSlot(str)
    def on_watcher_file_changed(self, filepath):
        self.media_widgets[filepath].open_media(filepath)
        self.media_widgets[filepath].scaledToWidth(self.scrollArea.size().width() / self.max_col)
        self.repaint()

    @pyqtSlot(str)
    def on_watcher_dir_changed(self, dirpath):
        self.update_dirpath_content()

    def reset(self, delete_widget=False):
        self._timer.stop()
        self._col_idx = 0
        self._row_idx = 0
        for widget in self.media_widgets.values():
            self._layout.removeWidget(widget)
            if delete_widget:
                widget.close()
        if delete_widget:
            self.media_widgets = {}

    def _add_media_widget(self, file):
        if file in self.media_widgets:
            widget = self.media_widgets[file]
        else:
            ext = os.path.splitext(file)[1][1:]
            if ext in FILE_EXTENSION_PHOTO:
                widget = ImageWidget(file)
            elif ext in FILE_EXTENSION_VIDEO:
                widget = VideoWidget(file)
            widget.doubleClicked.connect(self._controller.set_media_path)

        if widget.orig_pixmap and not widget.orig_pixmap.isNull():
            widget.setAttribute(Qt.WA_DeleteOnClose, True)
            widget.scaledToWidth(self.scrollArea.size().width() / self.max_col)
            self.media_widgets[file] = widget
            self._layout.addWidget(widget, self._row_idx, self._col_idx)
            self._col_idx = (self._col_idx + 1)
            if self._col_idx == self.max_col:
                self._col_idx = 0
                self._row_idx += 1
        else:
            widget.close()

    def resize_widgets(self):
        win_size = self.scrollArea.size()
        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            item.widget().scaledToWidth(win_size.width() / self.max_col)
