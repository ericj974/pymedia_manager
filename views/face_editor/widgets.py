import logging
import os
import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QDragMoveEvent
from PyQt5.QtWidgets import QVBoxLayout, QListWidget, QLineEdit, \
    QScrollArea, QLabel, QMenu, QAction, QHBoxLayout, QPushButton, QAbstractItemView

from views.face_editor import utils
from views.face_editor.db import FaceDetectionDB

# logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO, stream=sys.stdout)


class MyTextEdit(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super(MyTextEdit, self).__init__(parent)
        self.setAcceptDrops(True)
        self.__class__.dragEnterEvent = lambda _, event: event.acceptProposedAction()
        self.src_widget = None

    def dragMoveEvent(self, e: QDragMoveEvent):
        if (e.source() != self):
            e.accept()
        else:
            e.ignore()


class MyListWidget(QListWidget):
    def __init__(self, parent=None):
        super(MyListWidget, self).__init__(parent)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDropIndicatorShown(True)
        self.src_widget = None

    def dragMoveEvent(self, e: QDragMoveEvent):
        if (e.source() != self):
            e.accept()
        else:
            e.ignore()


class FaceTagWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        self.title = QtWidgets.QLabel()
        self.persons_widget = MyListWidget()
        self.persons_widget.installEventFilter(self)

        vlay = QVBoxLayout()
        self.setLayout(vlay)
        vlay.addWidget(self.title)
        vlay.addWidget(QtWidgets.QLabel("Face Tags"))
        vlay.addWidget(self.persons_widget, 1)

    def update_from_comment(self, media_comment):
        self.update_from_tags(media_comment.persons)

    def update_from_tags(self, tags):
        self.persons_widget.clear()
        self.persons_widget.addItems(tags)

    def get_person_tags(self):
        return [self.persons_widget.item(i).text() for i in range(self.persons_widget.count())]

    def act_rename(self):
        if len(self.persons_widget.selectedItems()) == 0:
            return
        text, okPressed = QtWidgets.QInputDialog.getText(self, "New Name", "New Name:")
        if okPressed and text != '':
            if len(self.persons_widget.selectedItems()) > 0:
                self.persons_widget.currentItem().setText(text)

    def act_add_tag(self):
        text, okPressed = QtWidgets.QInputDialog.getText(self, "New tag", "New tag:")
        if okPressed and text != '':
            tags = self.get_person_tags()
            if text not in tags:
                self.persons_widget.addItem(text)

    def eventFilter(self, source, event):
        if event.type() == QEvent.ContextMenu and source is self.persons_widget:
            menu = QMenu()
            if len(self.persons_widget.selectedItems()) > 0:
                action = QAction('Rename', self)
                action.triggered.connect(self.act_rename)
                menu.addAction(action)
            action = QAction('New Tag', self)
            action.triggered.connect(self.act_add_tag)
            menu.addAction(action)
            if menu.exec_(event.globalPos()):
                item = source.itemAt(event.pos())
            return True
        return super().eventFilter(source, event)


class FaceDetectionWidget(QtWidgets.QWidget):
    def __init__(self, db, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)


        self.db = db
        # Detection model selection
        self.detection_model_combobox = QtWidgets.QComboBox()
        self.detection_model_combobox.addItems(utils.detection_backend)
        self.face_model_combobox = QtWidgets.QComboBox()
        self.face_model_combobox.addItems(utils.face_recognition_model)

        # Search bar.
        self.searchbar = QLineEdit()
        self.searchbar.textChanged.connect(self.update_display_when_searching)

        # Listing of existing face tags
        self.list_db_tags_widget = MyListWidget()
        self.list_db_tags_widget.doubleClicked.connect(self.on_db_table_clicked)
        self.list_db_tags_widget.__class__.dropEvent = self.on_db_drop

        self.scroll_db = QScrollArea()
        self.scroll_db.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_db.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_db.setWidgetResizable(True)
        self.scroll_db.setWidget(self.list_db_tags_widget)

        # Listing of detection results
        self.result_widget = MyListWidget()
        self.list_db_tags_widget.src_widget = self.result_widget
        self.result_widget.installEventFilter(self)

        self.scroll_detection = QScrollArea()
        self.scroll_detection.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_detection.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_detection.setWidgetResizable(True)
        self.scroll_detection.setWidget(self.result_widget)

        # Buttons
        self.btn_save_to_db = QPushButton('Save to DB', self)
        self.btn_save_to_db.clicked.connect(self.save_selected_det_to_db)
        # Create layouts to place inside widget
        layout_buttons = QHBoxLayout()
        layout_buttons.setContentsMargins(0, 0, 0, 0)
        layout_buttons.addWidget(self.btn_save_to_db)

        # Set layout for dock widget
        vlay = QVBoxLayout()
        self.setLayout(vlay)
        vlay.addWidget(QLabel("Detection Backend"))
        vlay.addWidget(self.detection_model_combobox)
        vlay.addWidget(QLabel("Face Recognition Model"))
        vlay.addWidget(self.face_model_combobox)
        vlay.addWidget(self.searchbar)
        vlay.addWidget(QtWidgets.QLabel("Existing Tags"))
        vlay.addWidget(self.scroll_db, 2)
        vlay.addWidget(QLabel("Detection Results"))
        vlay.addWidget(self.scroll_detection)
        vlay.addLayout(layout_buttons)

        # Result of the detection
        self.file = ''
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.face_imgs = []

        # Display update
        self.update_db_display()
        self.update_det_result_display()

    def set_file(self, file):
        self.file = file

    def _detect_faces(self, qimage):

        # Detection and Representation
        detection_backend = self.detection_model_combobox.itemText(self.detection_model_combobox.currentIndex())
        face_recognition_model = self.face_model_combobox.itemText(self.face_model_combobox.currentIndex())

        encodings, imgs, locations, names = utils.face_recognition(qimage=qimage, detection_backend=detection_backend,
                                                                   face_recognition_model=face_recognition_model,
                                                                   db=self.db)

        self.face_encodings = encodings
        self.face_imgs = imgs
        self.face_locations = locations
        self.face_names = names

        # Show in list widget
        self.update_det_result_display()

    def update_display_when_searching(self, text):
        for i in range(self.list_db_tags_widget.count()):
            # item(row)->setHidden(!item(row)->text().contains(filter, Qt::CaseInsensitive));
            self.list_db_tags_widget.item(i).setHidden(
                self.list_db_tags_widget.item(i).text().contains(text, Qt.CaseInsensitive))

    def update_db_display(self):
        self.list_db_tags_widget.clear()
        self.list_db_tags_widget.addItems(list(set(self.db.known_face_names)))

    def update_det_result_display(self):
        self.result_widget.clear()
        self.result_widget.addItems(self.face_names)
        self.result_widget.installEventFilter(self)

    def clear(self):
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        self.face_imgs = []
        self.update_det_result_display()

    def save_selected_det_to_db(self):

        for item, index in zip(self.result_widget.selectedItems(),
                               self.result_widget.selectionModel().selectedIndexes()):
            if item.text() == utils.unknown_tag:
                continue
            ind = index.row()
            name = self.face_names[ind]
            img = self.face_imgs[ind]
            filename = os.path.basename(self.file)

            # Add an entry without encodings
            self.db.add_to_db(name=name,
                              img=img,
                              file=self.file)

            # Create encoding for all recognition models
            for model in utils.face_recognition_model:
                item = self.db.get_entry(name=name, filename=filename)
                if model in item.embeddings:
                    continue
                logging.info(f"Creating embedding for model {model}")

                # Representation
                embedding = utils.face_encodings(imgs=[img], model_name=model)[0]

                # Add to db
                self.db.update_embedding_entry(name=item.name, embedding=embedding,
                                               filename=item.filename, model=model)

            # self.db.add_to_db(name=self.face_names[ind],
            #                   encoding=self.face_encodings[ind],
            #                   img=self.face_imgs[ind],
            #                   file=self.file)
        self.update_db_display()

    def eventFilter(self, source, event):
        def rename():
            text, okPressed = QtWidgets.QInputDialog.getText(self, "New tag", "New tag:")
            if okPressed and text != '':
                if len(self.result_widget.selectedItems()) > 0:
                    self.face_names[self.result_widget.currentIndex().row()] = text
                    self.result_widget.currentItem().setText(self.face_names[self.result_widget.currentIndex().row()])

        if event.type() == QEvent.ContextMenu and source is self.result_widget:
            if len(self.result_widget.selectedItems()) > 0:
                menu = QMenu()
                action = QAction('Rename', self)
                action.triggered.connect(rename)
                menu.addAction(action)

                if menu.exec_(event.globalPos()):
                    item = source.itemAt(event.pos())
                    print(item.text())
                return True
        return super().eventFilter(source, event)

    def on_db_table_clicked(self, index):
        if len(self.result_widget.selectedItems()) > 0:
            self.face_names[self.result_widget.currentIndex().row()] = self.list_db_tags_widget.item(index.row()).text()
            self.result_widget.currentItem().setText(self.face_names[self.result_widget.currentIndex().row()])

    def on_db_drop(self, e):
        if (e.source() == self.result_widget):
            self.save_selected_det_to_db()
