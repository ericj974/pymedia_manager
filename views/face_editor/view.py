import os

import face_recognition
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QSize, pyqtSlot, QRect
from PyQt5.QtGui import QIcon, QPalette, QWheelEvent, QPainter, QColor, QPen, QPixmap
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QAction,
                             QSlider, QToolButton, QToolBar, QDockWidget, QMessageBox, QGridLayout,
                             QScrollArea, QStatusBar, QFileDialog, QShortcut, QListWidget, QVBoxLayout)

from controller import MainController
from utils import QImageToCvMat, image_resize
from views.face_editor.widgets import FaceTagWidget
from views.img_editor.widgets import ImageLabel, State
from model import MainModel
from constants import FILE_EXTENSION_PHOTO_JPG, FILE_EXTENSION_PHOTO
import resources.icons as icons
from views.tileview.widgets import UserCommentWidget

icon_path = os.path.join(os.path.dirname(os.path.abspath(icons.__file__)))


class FaceEditorWindow(QMainWindow):

    def __init__(self, model: MainModel, controller: MainController):
        super().__init__()

        self._model = model
        self._controller = controller

        self.cumul_scale_factor = 1

        self.create_main_label()
        self.create_editing_bar()
        self.create_actions_shortcuts()
        self.create_menus()
        self.create_top_toolbar()
        self.create_face_tag_toolbar()
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        # listen for model event
        # Model Event - selected image has changed
        self._model.selected_media_changed.connect(self.on_media_path_changed)

        self.setMinimumSize(300, 200)
        self.setWindowTitle("Face Editor")
        self.showMaximized()
        self.setStatusBar(QStatusBar())
        self.setVisible(False)

        # Open selected image
        if self._model.media_path:
            ext = os.path.splitext(self._model.media_path)[1][1:]
            if ext in FILE_EXTENSION_PHOTO_JPG:
                self.open_media(file=self._model.media_path)
            else:
                self.media_widget.reset()
                self.setEnabled(False)

    @pyqtSlot(str)
    def on_media_path_changed(self, path):
        ok = self.open_media(file=path)
        if ok or self.isVisible():
            self.show()

    def create_actions_shortcuts(self):
        # Actions for Photo Editor menu
        self.about_act = QAction('About', self)
        self.about_act.triggered.connect(self.aboutDialog)

        self.exit_act = QAction(QIcon(os.path.join(icon_path, "exit.png")), 'Quit Photo Editor', self)
        self.exit_act.setShortcut('Ctrl+Q')
        self.exit_act.triggered.connect(self.close)

        self.save_act = QAction(QIcon(os.path.join(icon_path, "save.png")), "Save...", self)
        self.save_act.setShortcut('Ctrl+S')
        self.save_act.triggered.connect(self.save_metadata)
        self.save_act.setEnabled(False)

        self.zoom_in_act = QAction(QIcon(os.path.join(icon_path, "zoom_in.png")), 'Zoom In', self)
        self.zoom_in_act.setShortcut('Ctrl++')
        self.zoom_in_act.triggered.connect(lambda: self.scale_image(1.25))
        self.zoom_in_act.setEnabled(False)

        self.zoom_out_act = QAction(QIcon(os.path.join(icon_path, "zoom_out.png")), 'Zoom Out', self)
        self.zoom_out_act.setShortcut('Ctrl+-')
        self.zoom_out_act.triggered.connect(lambda: self.scale_image(0.8))
        self.zoom_out_act.setEnabled(False)

        self.normal_size_act = QAction("Normal Size", self)
        self.normal_size_act.setShortcut('Ctrl+=')
        self.normal_size_act.triggered.connect(self._normal_size)
        self.normal_size_act.setEnabled(False)

        self.fit_to_window_act = QAction("&Fit to Window", self)
        self.fit_to_window_act.setShortcut('Ctrl+F')
        self.fit_to_window_act.triggered.connect(self.fit_window)
        self.fit_to_window_act.setEnabled(False)
        self.fit_to_window_act.setCheckable(True)
        self.fit_to_window_act.setChecked(True)

        self.detect_faces_act = QAction((QIcon(os.path.join(icon_path, "detect_faces.png"))), "Detect Faces", self)
        self.detect_faces_act.triggered.connect(self._detect_faces)


    def create_menus(self):
        """Set up the menubar."""
        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)

        # Create Photo Editor menu and add actions
        main_menu = menu_bar.addMenu('Face Editor')
        main_menu.addAction(self.about_act)
        main_menu.addSeparator()
        main_menu.addAction(self.exit_act)

        # Create file menu and add actions
        file_menu = menu_bar.addMenu('File')
        file_menu.addAction(self.save_act)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_act)

        edit_menu = menu_bar.addMenu('Edit')
        # edit_menu.addAction(self.revert_act)

        tool_menu = menu_bar.addMenu('Tools')
        tool_menu.addAction(self.zoom_in_act)
        tool_menu.addAction(self.zoom_out_act)
        tool_menu.addAction(self.normal_size_act)
        tool_menu.addSeparator()
        tool_menu.addAction(self.fit_to_window_act)
        tool_menu.addSeparator()
        tool_menu.addAction(self.detect_faces_act)

        views_menu = menu_bar.addMenu('Views')
        views_menu.addAction(self.tools_menu_act)

    def create_top_toolbar(self):
        """Set up the toolbar."""
        tool_bar = QToolBar("Main Toolbar")
        tool_bar.setIconSize(QSize(26, 26))
        self.addToolBar(tool_bar)

        # Add actions to the toolbar
        tool_bar.addAction(self.detect_faces_act)

    def create_face_tag_toolbar(self):
        tag_dock_widget = QDockWidget("Face Tags")
        self.face_tag_toolbar = FaceTagWidget()
        tag_dock_widget.setWidget(self.face_tag_toolbar)
        self.addDockWidget(Qt.RightDockWidgetArea, tag_dock_widget)

    def create_editing_bar(self):
        """Create dock widget for editing tools."""
        # TODO: Add a tab widget for the different editing tools
        self.editing_bar = QDockWidget("Detection")
        self.editing_bar.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.editing_bar.setMinimumWidth(90)


        self.detection_widget = QListWidget()
        self.scroll_detection = QScrollArea()
        self.scroll_detection.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_detection.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_detection.setWidgetResizable(True)
        self.scroll_detection.setWidget(self.detection_widget)


        # Set layout for dock widget
        vlay = QVBoxLayout()
        vlay.addWidget(QLabel("Detection Results"))
        vlay.addWidget(self.scroll_detection)

        container = QWidget()
        container.setLayout(vlay)

        self.editing_bar.setWidget(container)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.editing_bar)
        self.tools_menu_act = self.editing_bar.toggleViewAction()

    def create_main_label(self):
        """Create an instance of the imageLabel class and set it 
           as the main window's central widget."""
        self.media_widget = ImageLabel(self)

        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.Dark)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.media_widget)
        self.setCentralWidget(self.scroll_area)
        self.resize(QApplication.primaryScreen().availableSize() * 3 / 5)

    def update_actions(self):
        """Update the values of menu and toolbar items when an image
        is loaded."""
        self.save_act.setEnabled(True)

    def _detect_faces(self):
        frame = QImageToCvMat(self.media_widget.qimage)
        if frame.shape[0] > frame.shape[1]:
            frame = image_resize(frame, height=800)
        else:
            frame = image_resize(frame, width=800)
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        face_names = ["Unknown" for _ in face_encodings]
        r = int(self.media_widget.qimage.height() / frame.shape[0] )
        painter = QPainter(self.media_widget.qimage)
        penRectangle = QPen(QtCore.Qt.red)
        penRectangle.setWidth(10)
        painter.setPen(penRectangle)
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= r
            right *= r
            bottom *= r
            left *= r
            painter.drawRect(left, top, right-left, bottom-top)
        self.media_widget.setPixmap(QPixmap().fromImage(self.media_widget.qimage))
        painter.end()

    def open_media(self, file=""):
        """Load a new media"""
        if file == "":
            extensions = ['*.'+ext for ext in FILE_EXTENSION_PHOTO]
            ext = "("
            for e in extensions:
                ext += e + " "
            ext += ")"

            file, _ = QFileDialog.getOpenFileName(self, "Open Media",
                                                  "", f"Files {ext}")

        # Deactivate the img_editor if not an image
        ext = os.path.splitext(file)[1][1:]
        if ext not in FILE_EXTENSION_PHOTO:
            self.media_widget.reset()
            self.setEnabled(False)
            return False
        self.setEnabled(True)

        if file:
            self.media_widget.open_media(file)
            self.face_tag_toolbar.set_tags(self.media_widget.load_comment(), file)
            self.cumul_scale_factor = 1
            self.scroll_area.setVisible(True)
            self.fit_to_window_act.setEnabled(True)
            self.update_actions()

            if not self.fit_to_window_act.isChecked():
                self.media_widget.adjustSize()
            else:
                self.fit_window()

        elif file == "":
            # User selected Cancel
            pass
        else:
            QMessageBox.information(self, "Error",
                                    "Unable to open image.", QMessageBox.Ok)
        return True

    def save_metadata(self):
        """Save the image displayed in the label."""
        if not self.media_widget.qimage.isNull():
            self.media_widget.save_media(self._model.media_path)
            self.media_widget.save_comment(self.face_tag_toolbar.get_tags())
        else:
            QMessageBox.information(self, "Empty Image",
                                    "There is no image to save.", QMessageBox.Ok)

    def scale_image(self, scale_factor):
        """Zoom in and zoom out."""
        self.cumul_scale_factor *= scale_factor
        self.media_widget.resize(scale_factor * self.media_widget.size())

        self.adjustScrollBar(self.scroll_area.horizontalScrollBar(), scale_factor)
        self.adjustScrollBar(self.scroll_area.verticalScrollBar(), scale_factor)

        self.zoom_in_act.setEnabled(self.cumul_scale_factor < 4.0)
        self.zoom_out_act.setEnabled(self.cumul_scale_factor > 0.333)

    def _normal_size(self):
        """View image with its normal dimensions."""
        self.media_widget.adjustSize()
        self.cumul_scale_factor = 1.0

    def fit_window(self):
        fitToWindow = self.fit_to_window_act.isChecked()
        if not fitToWindow:
            self._normal_size()
        else:
            if not self.media_widget.pixmap().isNull():
                w, h = self.scroll_area.width(), self.scroll_area.height()
                wi, hi = self.media_widget.pixmap().width(), self.media_widget.pixmap().height()
                self.cumul_scale_factor = factor = min(h / hi, w / wi)
                self.media_widget.resize(factor * self.media_widget.pixmap().size())

        self.update_actions()

    def adjustScrollBar(self, scroll_bar, factor):
        """Adjust the scrollbar when zooming in or out."""
        scroll_bar.setValue(int(factor * scroll_bar.value() + ((factor - 1) * scroll_bar.pageStep() / 2)))

    def aboutDialog(self):
        QMessageBox.about(self, "About Face Editor",
                          "Face Editor\nVersion 0.9\n\nCreated by Joshua Willman")

    def wheelEvent(self, event: QWheelEvent) -> None:
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            numDegrees = event.angleDelta() / 8
            if not numDegrees.isNull():
                numSteps = int(numDegrees.y() / 15)
                if numSteps > 0:
                    for i in range(numSteps):
                        self.scale_image(1.25)
                else:
                    for i in range(-numSteps):
                        self.scale_image(0.8)
        QMainWindow.wheelEvent(self, event)

    def resizeEvent(self, event):
        self.fit_window()
        QMainWindow.resizeEvent(self, event)

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.key() == Qt.Key_F1:  # fn + F1 on Mac
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()

    def closeEvent(self, event):
        pass