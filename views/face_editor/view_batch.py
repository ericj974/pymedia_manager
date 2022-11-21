# -*- coding: utf-8 -*-
import os

# Form implementation generated from reading ui file 'gui.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QStatusBar, QTableWidgetItem

from controller import MainController
from model import MainModel
from utils import load_image
from views.face_editor import utils


class FaceEditorBatchWindow(QMainWindow):

    def __init__(self, model: MainModel, controller: MainController, db):
        super().__init__()

        # MVC
        self._model = model
        self._controller = controller

        # DB
        self.db = db

        # Central widget
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Main table
        self.table_result = QtWidgets.QTableWidget(self.central_widget)
        self.table_result.doubleClicked.connect(self.on_table_double_clicked)
        self.table_result.setColumnCount(2)
        self.table_result.setRowCount(0)
        self.table_result.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem("Issue/Tag"))
        self.table_result.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem("Filename"))

        self.table_result.horizontalHeader().setVisible(True)
        self.table_result.setSortingEnabled(True)
        self.table_result.horizontalHeader().setCascadingSectionResizes(True)
        self.table_result.horizontalHeader().setDefaultSectionSize(250)
        self.table_result.horizontalHeader().setSortIndicatorShown(True)
        self.table_result.horizontalHeader().setStretchLastSection(False)
        self.table_result.verticalHeader().setCascadingSectionResizes(True)

        self.setMinimumSize(807, 737)
        self.setWindowTitle("Tags")
        self.showMaximized()
        self.setStatusBar(QStatusBar())
        self.setVisible(False)

        # Files
        self.results = {}

    def detect_faces_batch(self, files):
        self.results = {}

        ind = 0

        for file in files:
            qimage, exif_dict = load_image(file)
            # Detection and Representation
            detection_backend = self.detection_model_combobox.itemText(self.detection_model_combobox.currentIndex())
            face_recognition_model = self.face_model_combobox.itemText(self.face_model_combobox.currentIndex())

            encodings, imgs, locations, names = utils.face_recognition(qimage=qimage,
                                                                       detection_backend=detection_backend,
                                                                       face_recognition_model=face_recognition_model,
                                                                       db=self.db)

            # Keep Track
            self.results[file] = (file, encodings, imgs, locations, names)

            # Display
            for (encoding, img, location, name) in zip(encodings, imgs, locations, names):
                filename = os.path.basename(file)
                self.table_result.setItem(ind, 0, MyQTableWidgetItem(filename, file, encoding, img, location, name))
                self.table_result.setItem(ind, 1, QTableWidgetItem(filename))
                ind +=1

    def on_table_double_clicked(self, index):
        row = index.row()
        file = self.table_result.item(row, 0).file
        self._controller.set_media_path(file)

class MyQTableWidgetItem(QTableWidgetItem):
    def __init__(self, filename, file, encoding, img, location, name):
        super().__init__(filename)
        self.file = file
        self.encoding = encoding
        self.img = img
        self.location = location
        self.name = name
