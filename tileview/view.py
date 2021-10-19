import copy
import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QStatusBar

from controller import MainController
from model import MainModel
from settings import TILES_THUMBNAIL_SIZE


class MainTileWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None, max_col=3, model: MainModel = None, controller: MainController = None):
        super(MainTileWindow, self).__init__(parent)
        self.setWindowTitle("Tile View")
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        # MVC model
        self._model = model
        self._controller = controller

        # listen for model event signals
        self._model.selected_dir_changed.connect(self.on_dirpath_changed)
        self._model.selected_image_changed.connect(self.on_selected_image_changed)
        self._model.selected_dir_content_changed.connect(self.on_watcher_dir_changed)
        self._model.selected_file_content_changed.connect(self.on_watcher_file_changed)

        # Max col settings for the gridlayout
        self.max_col = max_col
        # Available position in the grid layout
        self.col_idx = 0
        self.row_idx = 0
        # List of file to process (widget creation and placement)
        self._files_to_process = None
        # Path -> widget dict
        self.image_widgets = {}
        self.scrollArea = QtWidgets.QScrollArea(widgetResizable=True)
        self.setCentralWidget(self.scrollArea)

        content_widget = QtWidgets.QWidget()
        self.scrollArea.setWidget(content_widget)
        self._layout = QtWidgets.QGridLayout()
        content_widget.setLayout(self._layout)

        # Timer for loading the images (avoid freeze)
        self._timer = QtCore.QTimer(self, interval=1)
        self._timer.timeout.connect(self.on_timeout_process_next_file)

        # Initial window size
        self.resize(QGuiApplication.primaryScreen().availableSize() * 3 / 5)
        self.setStatusBar(QStatusBar())

    def _reset_state(self):
        self._timer.stop()
        self.col_idx = 0
        self.row_idx = 0
        for widget in self.image_widgets.values():
            self._layout.removeWidget(widget)
            widget.close()
        self.image_widgets = {}

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
        self.resize_widgets()
        QtWidgets.QMainWindow.resizeEvent(self, event)

    @pyqtSlot(str)
    def on_dirpath_changed(self, dirpath):
        self.set_dirpath(dirpath)

    @pyqtSlot(str)
    def on_selected_image_changed(self, filepath):
        # No more selected image
        if filepath == '':
            return
        # Make sure we reload the selected filepath, in case the signal is emitted because the image has been modified
        if filepath in self.image_widgets:
            self.image_widgets[filepath].set_file(filepath)
            self.image_widgets[filepath].scaledToWidth(self.size().width() / self.max_col)
            # Scroll down to the selected image
            posy = self.scrollArea.findChild(QtWidgets.QLabel, filepath).pos().y()
            self.scrollArea.verticalScrollBar().setValue(posy)
        else:
            # Seems like a file has been added (or a rename)
            self.update_dirpath_content()

    def on_timeout_process_next_file(self):
        try:
            file = self._files_to_process.pop(0)
            self.add_image_widget(file)
        except IndexError:
            self._timer.stop()
            # Scroll down to the selected image
            filepath = self._model.imagepath
            try:
                posy = self.scrollArea.findChild(QtWidgets.QLabel, filepath).pos().y()
                self.scrollArea.verticalScrollBar().setValue(posy)
            except:
                pass

    @pyqtSlot(str)
    def on_watcher_file_changed(self, filepath):
        self.image_widgets[filepath].set_file(filepath)
        self.image_widgets[filepath].scaledToWidth(self.size().width() / self.max_col)
        self.repaint()

    @pyqtSlot(str)
    def on_watcher_dir_changed(self, dirpath):
        self.update_dirpath_content()

    def reset(self, delete_widget=False):
        self._timer.stop()
        self.col_idx = 0
        self.row_idx = 0
        for widget in self.image_widgets.values():
            self._layout.removeWidget(widget)
            if delete_widget:
                widget.close()
        if delete_widget:
            self.image_widgets = {}

    def add_image_widget(self, file):
        if file in self.image_widgets:
            widget = self.image_widgets[file]
        else:
            widget = ImageWidget(file)
            widget.doubleClicked.connect(self._controller.set_imagepath)

        if widget.orig_pixmap and not widget.orig_pixmap.isNull():
            widget.setAttribute(Qt.WA_DeleteOnClose, True)
            widget.scaledToWidth(self.size().width() / self.max_col)
            self.image_widgets[file] = widget
            self._layout.addWidget(widget, self.row_idx, self.col_idx)
            self.col_idx = (self.col_idx + 1)
            if self.col_idx == self.max_col:
                self.col_idx = 0
                self.row_idx += 1
        else:
            widget.close()

    def resize_widgets(self):
        win_size = self.size()
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
        pixmap = self.orig_pixmap.scaledToWidth(width)
        self.setPixmap(pixmap)

    def set_file(self, file):
        if os.path.exists(file) and os.path.isfile(file):
            self.file = file
            self.orig_pixmap = QtGui.QPixmap(file).scaledToWidth(TILES_THUMBNAIL_SIZE)
            if not self.orig_pixmap.isNull():
                self.setPixmap(self.orig_pixmap)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    model = MainModel()
    controller = MainController(model=model)
    w = MainTileWindow(controller=controller, model=model)
    # w.set_dirpath('/home/ericj/Pictures/20200306-20200310 Indonesia_Bandung')
    # w.set_dirpath('/home/ericj/Pictures/test/')
    w.show()
    model.dirpath = '/home/ericj/Pictures/test/'
    model.imagepath = '/home/ericj/Pictures/test/20190626_224734.jpg'
    sys.exit(app.exec_())
