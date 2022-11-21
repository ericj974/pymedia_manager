import os

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from constants import FILE_EXTENSION_MEDIA, FILE_EXTENSION_PHOTO_JPG


class FileExplorerWidget(QWidget):
    # Change of directory path
    selected_files_face_det = pyqtSignal()

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        hlay = QHBoxLayout(self)
        self.treeview = QTreeView()
        self.listview = QListView()
        self.listview.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.listview.installEventFilter(self)

        hlay.addWidget(self.treeview)
        hlay.addWidget(self.listview)

        path = QDir.rootPath()

        self.dirModel = QFileSystemModel()
        self.dirModel.setRootPath(QDir.rootPath())
        self.dirModel.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs)

        self.fileModel = QFileSystemModel()
        self.fileModel.setFilter(QDir.NoDotAndDotDot | QDir.Files)
        self.fileModel.setNameFilters(['*.' + ext for ext in FILE_EXTENSION_MEDIA])
        self.treeview.setModel(self.dirModel)
        self.listview.setModel(self.fileModel)

        self.treeview.setRootIndex(self.dirModel.index(path))
        self.listview.setRootIndex(self.fileModel.index(path))
        self.listview.doubleClicked.connect(self.listview_double_clicked)

        self.treeview.clicked.connect(self.on_clicked)

    def listview_double_clicked(self, index):
        filepath = self.fileModel.filePath(index)
        pass

    def on_clicked(self, index):
        path = self.dirModel.fileInfo(index).absoluteFilePath()
        self.listview.setRootIndex(self.fileModel.setRootPath(path))

    def set_dirpath(self, dirpath):
        parentpath = os.path.dirname(dirpath)
        idx = self.dirModel.setRootPath(parentpath)
        self.treeview.setRootIndex(idx)
        self.listview.setRootIndex(self.fileModel.setRootPath(dirpath))

    def eventFilter(self, source, event):
        if event.type() == QEvent.ContextMenu and source is self.listview:
            menu = QMenu()
            action = QAction('Face Detection', self)
            action.triggered.connect(lambda: self.selected_files_face_det.emit())
            menu.addAction(action)
            if menu.exec_(event.globalPos()):
                item = source.itemAt(event.pos())
            return True
        return super().eventFilter(source, event)



