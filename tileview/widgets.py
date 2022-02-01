import copy
import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout

import utils
from settings import TILES_THUMBNAIL_SIZE


class UserCommentWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        vlay = QVBoxLayout()
        self.setLayout(vlay)
        self.title = QtWidgets.QLabel()
        self.text_widget = QtWidgets.QTextEdit()
        self.tags_widget = QtWidgets.QTextEdit()
        self.filepath = None
        vlay.addWidget(self.title)
        vlay.addWidget(self.text_widget, 3)
        vlay.addWidget(QtWidgets.QLabel("Tags"))
        vlay.addWidget(self.tags_widget, 1)

    def update_comment(self, filepath):
        user_comment = utils.get_exif_user_comment(filepath)
        assert 'tags' in user_comment
        assert 'comments' in user_comment
        self.filepath = filepath
        self.text_widget.setText(user_comment['comments'])
        text = ""
        for tag in user_comment['tags']:
            text += tag + " "
        self.tags_widget.setText(text)
        self.title.setText(os.path.basename(filepath))

    def save_comment(self):
        if self.filepath is None: return

        user_comment = {
            'comments': self.text_widget.toPlainText(),
            'tags': self.tags_widget.toPlainText().split()
        }

        exif_dic = utils.get_exif_v2(self.filepath)
        utils.update_user_comment(exif_dict=exif_dic, userdata=user_comment)
        utils.save_exif(exif_dict=exif_dic, filepath=self.filepath)


class TilesWidget(QtWidgets.QWidget):
    def __init__(self, max_col=3, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        # Max col settings for the gridlayout
        self.max_col = max_col
        # Available position in the grid layout
        self.col_idx = 0
        self.row_idx = 0
        # List of file to process (widget creation and placement)
        self._files_to_process = None
        # Path -> widget dict
        self.image_widgets = {}

        # Tiles widget
        self.scrollArea = QtWidgets.QScrollArea(widgetResizable=True)
        self.content_widget = QtWidgets.QWidget()
        self.scrollArea.setWidget(self.content_widget)
        self._layout = QtWidgets.QGridLayout()
        self.content_widget.setLayout(self._layout)

        # Timer for loading the images (avoid freeze)
        self._timer = QtCore.QTimer(self, interval=1)
        self._timer.timeout.connect(self._on_timeout_process_next_file)

    def _reset_state(self):
        self._timer.stop()
        self.col_idx = 0
        self.row_idx = 0
        for widget in self.image_widgets.values():
            self._layout.removeWidget(widget)
            widget.close()
        self.image_widgets = {}

    def set_files(self, files):
        self._reset_state()
        self._files_to_process = copy.deepcopy(files)
        self._timer.start()

    def update_dirpath_content(self, new_files):
        # Make sure not conflict with if we're populating the files
        self._timer.stop()

        files_it = new_files
        key_to_del = []  # List of filepaths that dont exist anymore
        for widget in self.image_widgets.values():
            self._layout.removeWidget(widget)
            if widget.file not in files_it:
                key_to_del.append(widget.file)
                widget.close()
        for key in key_to_del:
            del self.image_widgets[key]

        self.col_idx = 0
        self.row_idx = 0
        self._files_to_process = copy.deepcopy(self._model.files)
        self._timer.start()

    def resizeEvent(self, event):
        self._resize_widgets()
        QtWidgets.QMainWindow.resizeEvent(self, event)

    def update_selected_image(self, filepath):
        # No more selected image
        if filepath == '':
            return
        # Make sure we reload the selected filepath, in case the signal is emitted because the image has been modified
        if filepath in self.image_widgets:
            self.image_widgets[filepath].set_file(filepath)
            self.image_widgets[filepath].scaledToWidth(self.scrollArea.size().width() / self.max_col)
            # Scroll down to the selected image
            posy = self.scrollArea.findChild(QtWidgets.QLabel, filepath).pos().y()
            self.scrollArea.verticalScrollBar().setValue(posy)
            # Display the comment
            self.text_widget.update_comment(filepath)
        else:
            # Seems like a file has been added (or a rename)
            self.update_dirpath_content()

    def _on_timeout_process_next_file(self):
        try:
            file = self._files_to_process.pop(0)
            self._add_image_widget(file)
        except IndexError:
            self._timer.stop()
            # Scroll down to the selected image
            filepath = self._model.imagepath
            try:
                posy = self.scrollArea.findChild(QtWidgets.QLabel, filepath).pos().y()
                self.scrollArea.verticalScrollBar().setValue(posy)
            except:
                pass

    def reset(self, delete_widget=False):
        """
            Remove all widgets
        """
        self._timer.stop()
        self.col_idx = 0
        self.row_idx = 0
        for widget in self.image_widgets.values():
            self._layout.removeWidget(widget)
            if delete_widget:
                widget.close()
        if delete_widget:
            self.image_widgets = {}

    def _add_image_widget(self, file):
        if file in self.image_widgets:
            widget = self.image_widgets[file]
        else:
            widget = ImageWidget(file)
            widget.doubleClicked.connect(self._controller.set_imagepath)

        if widget.orig_pixmap and not widget.orig_pixmap.isNull():
            widget.setAttribute(Qt.WA_DeleteOnClose, True)
            widget.scaledToWidth(self.scrollArea.size().width() / self.max_col)
            self.image_widgets[file] = widget
            self._layout.addWidget(widget, self.row_idx, self.col_idx)
            self.col_idx = (self.col_idx + 1)
            if self.col_idx == self.max_col:
                self.col_idx = 0
                self.row_idx += 1
        else:
            widget.close()

    def _resize_widgets(self):
        win_size = self.scrollArea.size()
        for i in range(self._layout.count()):
            item = self._layout.itemAt(i)
            item.widget().scaledToWidth(win_size.width() / self.max_col)


class ImageWidget(QtWidgets.QLabel):
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
            self.orig_pixmap = QtGui.QPixmap(file).scaledToWidth(TILES_THUMBNAIL_SIZE)
            if not self.orig_pixmap.isNull():
                self.setPixmap(self.orig_pixmap)
