import face_recognition
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import QVBoxLayout, QListWidget, QLineEdit, \
    QScrollArea, QLabel, QMenu, QAction, QHBoxLayout, QPushButton

from utils import QImageToCvMat, image_resize
from views.face_editor.utils import FaceDetectionDB

unknown_tag = "unknown"


class FaceTagWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        self.title = QtWidgets.QLabel()

        self.persons_widget = QtWidgets.QTextEdit()

        vlay = QVBoxLayout()
        self.setLayout(vlay)
        vlay.addWidget(self.title)
        vlay.addWidget(QtWidgets.QLabel("Img Tags"))
        vlay.addWidget(self.persons_widget, 1)

    def update_from_comment(self, user_comment):
        text = ""
        for tag in user_comment.persons:
            text += tag + " "
        self.persons_widget.setText(text)

    def get_tags(self):
        pass


class FaceDetectionWidget(QtWidgets.QWidget):
    def __init__(self, db_folder, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        self.db = FaceDetectionDB(db_folder)

        # Search bar.
        self.searchbar = QLineEdit()
        self.searchbar.textChanged.connect(self.update_display_when_searching)
        self.list_db_tags_widget = QListWidget()
        self.list_db_tags_widget.doubleClicked.connect(self.on_db_table_clicked)
        self.scroll_db = QScrollArea()
        self.scroll_db.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_db.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_db.setWidgetResizable(True)
        self.scroll_db.setWidget(self.list_db_tags_widget)

        # Detection part
        self.result_widget = QListWidget()
        # self.result_widget.setSelectionModel(QtGui.QItem)
        self.result_widget.installEventFilter(self)
        self.scroll_detection = QScrollArea()
        self.scroll_detection.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_detection.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_detection.setWidgetResizable(True)
        self.scroll_detection.setWidget(self.result_widget)

        # Buttons
        self.btn_save_to_db = QPushButton('Save to DB', self)
        self.btn_save_to_db.clicked.connect(self.save_tag_to_db)
        # Create layouts to place inside widget
        layout_buttons = QHBoxLayout()
        layout_buttons.setContentsMargins(0, 0, 0, 0)
        layout_buttons.addWidget(self.btn_save_to_db)

        # Set layout for dock widget
        vlay = QVBoxLayout()
        self.setLayout(vlay)
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

        frame_orig = QImageToCvMat(qimage)

        if frame_orig.shape[0] > frame_orig.shape[1]:
            frame = image_resize(frame_orig, height=800)
        else:
            frame = image_resize(frame_orig, width=800)
        r = qimage.height() / frame.shape[0]
        face_locations = face_recognition.face_locations(frame)
        self.face_encodings = face_recognition.face_encodings(frame, face_locations)
        self.face_imgs = []
        self.face_locations = []
        for (top, right, bottom, left) in face_locations:
            (top, right, bottom, left) = (int(top * r), int(right * r), int(bottom * r), int(left * r))
            self.face_imgs.append(frame_orig[top:bottom, left:right])
            self.face_locations.append((top, right, bottom, left))
        self.face_names = []
        for face_encoding in self.face_encodings:
            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(self.db.known_face_encodings, face_encoding)
            name = unknown_tag

            # If a match was found in known_face_encodings, select the on with the lowest distance
            if True in matches:
                known_face_encodings = np.array(self.db.known_face_encodings)[matches]
                known_face_names = np.array(self.db.known_face_names)[matches]
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                name = known_face_names[best_match_index]
            self.face_names.append(name)

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

    def save_tag_to_db(self):
        if len(self.result_widget.selectedItems()) > 0 and self.result_widget.currentItem().text() != unknown_tag:
            ind = self.result_widget.currentIndex().row()
            self.db.add_to_db(name=self.face_names[ind],
                              encoding=self.face_encodings[ind],
                              img=self.face_imgs[ind],
                              file=self.file)
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
