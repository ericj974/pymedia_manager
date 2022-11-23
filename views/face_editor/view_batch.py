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
from views.face_editor.controller_model import FaceDetectionController, FaceDetectionModel
from views.face_editor.utils import DetectionResult


class FaceEditorBatchWindow(QMainWindow):

    def __init__(self, model: MainModel, controller: MainController,
                 model_local: FaceDetectionModel, controller_local: FaceDetectionController):
        super(QMainWindow, self).__init__()

        # MVC global
        self._model = model
        self._controller = controller

        # MVC Local
        self._model_local = model_local
        self._controller_local = controller_local

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

        # listen for model event signals
        # self._model.selected_media_changed.connect(self.on_selected_media_changed)
        # self._model.selected_media_comment_updated.connect(self.on_model_comment_updated)
        self._model_local.detection_results_changed.connect(self.on_detection_results_changed)


        self.setMinimumSize(807, 737)
        self.setWindowTitle("Tags")
        self.showMaximized()
        self.setStatusBar(QStatusBar())
        self.setVisible(False)

        # Files
        self.results = {}

    def on_detection_results_changed(self, _):
        results = self._model_local.detection_results
        ind = 0
        # Display
        for result in results:
            filename = os.path.basename(result.file)
            self.table_result.setItem(ind, 0, MyQTableWidgetItem(result))
            self.table_result.setItem(ind, 1, QTableWidgetItem(filename))
            ind +=1

    def on_table_double_clicked(self, index):
        row = index.row()
        file = self.table_result.item(row, 0).file
        self._controller.set_media_path(file)

class MyQTableWidgetItem(QTableWidgetItem):
    def __init__(self, result: DetectionResult):
        super(QTableWidgetItem, self).__init__(os.path.basename(result.file))
        self.result = result

    @property
    def file(self):
        return self.result.file
