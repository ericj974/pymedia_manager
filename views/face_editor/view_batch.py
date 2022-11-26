# -*- coding: utf-8 -*-
import logging
import os

# Form implementation generated from reading ui file 'gui.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtWidgets, Qt
from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QMainWindow, QStatusBar, QTableWidgetItem, QHBoxLayout, QLabel, QLineEdit, QCompleter, \
    QPushButton

from common.utils import pixmap_from_frame
from controller import MainController
from model import MainModel
from utils import load_image, ImageUserComment
from views.face_editor import utils
from views.face_editor.controller_model import FaceDetectionController, FaceDetectionModel
from views.face_editor.utils import DetectionResult
from views.img_editor.widgets import ImageLabel

idx_col_filename = 0
idx_col_name = 1
idx_col_faction_save_img = 2
idx_col_faction_save_db = 3


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
        self.table_result.setMinimumWidth(150 + 150 + 50 + 50)
        self.table_result.setMaximumWidth(150 + 150 + 50 + 50)
        # self.table_result.setColumnWidth(0, 150)

        self.table_result.doubleClicked.connect(self.on_table_double_clicked)
        self.table_result.clicked.connect(self.on_table_single_clicked)
        self.table_result.setColumnCount(4)
        self.table_result.setRowCount(0)

        self.table_result.setHorizontalHeaderItem(0, QtWidgets.QTableWidgetItem("Filename"))
        self.table_result.setHorizontalHeaderItem(1, QtWidgets.QTableWidgetItem("Issue/Tag"))
        self.table_result.setHorizontalHeaderItem(2, QtWidgets.QTableWidgetItem(""))
        self.table_result.setHorizontalHeaderItem(3, QtWidgets.QTableWidgetItem(""))

        self.table_result.horizontalHeader().setVisible(True)
        self.table_result.setSortingEnabled(True)
        self.table_result.horizontalHeader().setCascadingSectionResizes(True)
        self.table_result.horizontalHeader().setSortIndicatorShown(True)
        self.table_result.verticalHeader().setCascadingSectionResizes(True)

        # Patch viewer widget
        self.media_widget = QLabel()

        # Main Layout
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.table_result)
        self.layout.addWidget(self.media_widget)
        self.central_widget.setLayout(self.layout)

        # listen for model event signals
        # self._model.selected_media_changed.connect(self.on_selected_media_changed)
        # self._model.selected_media_comment_updated.connect(self.on_model_comment_updated)
        # self._model_local.detection_results_changed.connect(self.on_detection_results_changed)

        self.setMinimumSize(640, 480)
        self.setWindowTitle("Tags")
        # self.showMaximized()
        self.setStatusBar(QStatusBar())
        self.setVisible(False)

        # Files
        self.results = {}

    def detect_faces(self, files):
        self.results = []

        # Detect
        for file in files:
            temp = utils.face_recognition(file=file,
                                          detection_model=self._model_local.detection_model,
                                          recognition_model=self._model_local.recognition_model,
                                          db=self._model_local.db)
            self.results += temp

        # Display
        self.table_result.setRowCount(len(self.results))
        for i, result in enumerate(self.results):
            # Filename
            self.table_result.setItem(i, idx_col_filename, QTableWidgetItem(os.path.basename(result.file)))

            # Name
            cell = MyQTableWidgetCell(result, self._model_local.db.known_face_names)
            index = QtCore.QPersistentModelIndex(self.table_result.model().index(i, idx_col_name))
            cell.returnPressed.connect(lambda *args, index=index: self.on_return_pressed(index))
            self.table_result.setCellWidget(i, idx_col_name, cell)

            # Action save to Image
            btn = QPushButton('Save to Img', self)
            index = QtCore.QPersistentModelIndex(self.table_result.model().index(i, idx_col_faction_save_img))
            btn.clicked.connect(lambda *args, index=index: self.save_to_img(index))
            btn.setEnabled(True)
            self.table_result.setCellWidget(i, idx_col_faction_save_img, btn)

            # Action save to DB
            btn = QPushButton('Save to db', self)
            index = QtCore.QPersistentModelIndex(
                self.table_result.model().index(i, idx_col_faction_save_db))
            btn.clicked.connect(lambda *args, index=index: self.save_to_db(index))
            btn.setEnabled(False)
            self.table_result.setCellWidget(i, idx_col_faction_save_db, btn)

        self.table_result.repaint()

    def save_to_img(self, index):
        if index.isValid():
            # Get the result and (maybe) updated tag
            cell = self.table_result.cellWidget(index.row(), idx_col_name)
            result = cell.result
            result.name = cell.text()

            # Update the file comment
            comment = ImageUserComment.load_from_file(result.file)
            comment.persons = list(set(comment.persons + [result.name]))

            if result.file == self._model.media_path:
                self._controller.update_media_comment(comment)
                self._controller.save_media_comment()
            else:
                comment.save_comment(result.file)

            # Turn the background green and deactivate button
            palette = QPalette()
            palette.setColor(QPalette.Base, QtCore.Qt.green)
            palette.setColor(QPalette.Text, QtCore.Qt.black)
            btn = self.table_result.cellWidget(index.row(), idx_col_faction_save_img)
            btn.setPalette(palette)
            btn.update()
            btn.setEnabled(False)

    def save_to_db(self, index):
        if index.isValid():
            # Get the result and (maybe) updated tag
            cell = self.table_result.cellWidget(index.row(), idx_col_name)
            result = cell.result
            result.name = cell.text()

            # Create encoding for all recognition models
            for model in utils.face_recognition_model:
                item_db = self._model_local.db.get_entry(name=result.name, filename=os.path.basename(result.file),
                                                         model=model)
                if item_db is not None:
                    continue
                logging.info(f"Creating embedding for model {model}")

                # Representation
                embedding = utils.face_encodings(imgs=[result.patch], recognition_model=model)[0]

                # Add to db
                self._model_local.db.add_to_db(name=result.name, patch=result.patch, embedding=embedding,
                                               location=result.location, file=result.file, model=model, overwrite=True)

                # Turn the background green and deactivate button
                palette = QPalette()
                palette.setColor(QPalette.Base, QtCore.Qt.green)
                palette.setColor(QPalette.Text, QtCore.Qt.black)
                btn = self.table_result.cellWidget(index.row(), idx_col_faction_save_db)
                btn.setPalette(palette)
                btn.update()
                btn.setEnabled(False)

    def on_table_double_clicked(self, index):
        file = self.table_result.cellWidget(index.row(), idx_col_name).result.file
        self._controller.set_media_path(file)

        # Detection results
        results = []
        for i in range(self.table_result.rowCount()):
            cell = self.table_result.cellWidget(i, idx_col_name)
            if cell.result.file != file:
                continue
            result = cell.result
            # Maybe name has been changed by user
            result.name = cell.text()
            results.append(result)

        idx = results.index(self.table_result.cellWidget(index.row(), idx_col_name).result)
        self._controller_local.set_detection_results(results)
        self._controller_local.set_selected_result(idx)

    def on_table_single_clicked(self, index):
        row = index.row()
        patch = self.table_result.cellWidget(row, idx_col_name).result.patch
        pix = pixmap_from_frame(patch)
        self.media_widget.setPixmap(
            pix.scaled(self.media_widget.width(), self.media_widget.height(), QtCore.Qt.KeepAspectRatio))

    def on_return_pressed(self, index):
        if index.isValid():
            # Get the result and (maybe) updated tag
            cell = self.table_result.cellWidget(index.row(), idx_col_name)
            if cell.text() != cell.result.name:
                # Change BG color to red
                palette = QPalette()
                palette.setColor(QPalette.Base, QtCore.Qt.red)
                palette.setColor(QPalette.Text, QtCore.Qt.black)
                cell.setPalette(palette)
                # Make the add to db btn visible
                if cell.result.name != utils.unknown_tag:
                    self.table_result.cellWidget(index.row(), idx_col_faction_save_db).setEnabled(True)


class MyQTableWidgetCell(QLineEdit):
    def __init__(self, result: DetectionResult, wordlist):
        super(MyQTableWidgetCell, self).__init__(os.path.basename(result.name))
        self.result = result
        # Autocomplete
        completer = QCompleter(wordlist, self)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.setCompleter(completer)
        # Escape key event
        self.installEventFilter(self)

    @property
    def file(self):
        return self.result.file

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress and event.key() == QtCore.Qt.Key_Escape and source is self:
            super(MyQTableWidgetCell, self).setText(self.result.name)
        return super().eventFilter(source, event)
