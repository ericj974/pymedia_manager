import os
import sys

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class FileExplorerWidget(QWidget):
    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        hlay = QHBoxLayout(self)
        self.treeview = QTreeView()
        self.listview = QListView()
        hlay.addWidget(self.treeview)
        hlay.addWidget(self.listview)

        path = QDir.rootPath()

        self.dirModel = QFileSystemModel()
        self.dirModel.setRootPath(QDir.rootPath())
        self.dirModel.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs)

        self.fileModel = QFileSystemModel()
        self.fileModel.setFilter(QDir.NoDotAndDotDot | QDir.Files)
        self.fileModel.setNameFilters(["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.heic"])

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