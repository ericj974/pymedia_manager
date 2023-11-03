from pathlib import Path

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QSize, pyqtSlot
from PyQt5.QtGui import QIcon, QPalette, QWheelEvent, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QAction,
                             QSlider, QToolButton, QToolBar, QDockWidget, QMessageBox, QGridLayout,
                             QScrollArea, QStatusBar, QFileDialog, QShortcut)

import common.comment
import resources.icons as icons
from common.constants import FILE_EXTENSION_PHOTO_JPG, FILE_EXTENSION_PHOTO
from common.face import unknown_tag
from common.widgets import PersonQListWidgetItem
from mvc.controllers.face import FaceDetectionController
from mvc.controllers.main import MainController
from mvc.models.face import FaceDetectionModel
from mvc.models.main import MainModel
from mvc.views.img_editor.widgets import ImageLabel, State, FaceDetectionWidget
from mvc.views.tileview.widgets import UserCommentWidget

icon_path = Path(icons.__file__).parent


class PhotoEditorWindow(QMainWindow):

    def __init__(self, model: MainModel, controller: MainController,
                 model_local: FaceDetectionModel, controller_local: FaceDetectionController):
        super().__init__()

        # MVC global
        self._model = model
        self._controller = controller
        self._controller.set_parent(self)

        # MVC Local
        self._model_local = model_local
        self._controller_local = controller_local

        self.cumul_scale_factor = 1

        self.create_main_label()
        self.create_editing_bar()
        self.create_face_toolbar()
        self.create_actions_shortcuts()
        self.create_menus()
        self.create_top_toolbar()
        self.create_user_comment_widget()
        self.setAttribute(Qt.WA_DeleteOnClose, True)

        # listen for model event
        # Model Event - selected image has changed
        self._model.selected_media_changed.connect(self.on_selected_media_changed)

        # drop event
        self.setAcceptDrops(True)
        self.__class__.dragEnterEvent = lambda _, event: event.acceptProposedAction()
        self.__class__.dropEvent = self.on_drop_media

        # listen for model event signals
        self._model.selected_media_comment_updated.connect(self.on_model_comment_updated)
        self._model.tag_added.connect(
            lambda _: self.comment_toolbar.tags_widget.set_known_tags(self._model.db_tags.tags))
        self._model_local.detection_results_changed.connect(self.on_detection_results_changed)
        self._model_local.selected_detection_result_changed.connect(self.on_detection_results_selection_changed)

        self.setMinimumSize(300, 200)
        self.setWindowTitle("Photo Editor")
        self.showMaximized()
        self.setStatusBar(QStatusBar())
        self.setVisible(False)

        # Open selected image
        if self._model.media_path:
            ext = self._model.media_path.suffix
            if ext in FILE_EXTENSION_PHOTO_JPG:
                self.open_media(file=self._model.media_path)
            else:
                self.media_widget.reset()
                self.setEnabled(False)

    @pyqtSlot(Path)
    def on_selected_media_changed(self, path):
        ok = self.open_media(file=path)
        if ok or self.isVisible():
            self.show()

    @pyqtSlot(Path)
    def on_drop_media(self, event):
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                ext = path.suffix
                if ext in FILE_EXTENSION_PHOTO_JPG:
                    self._controller.set_media_path(path)
            break

    def create_actions_shortcuts(self):
        # Actions for Photo Editor menu
        self.about_act = QAction('About', self)
        self.about_act.triggered.connect(self.aboutDialog)

        self.exit_act = QAction(QIcon(str(icon_path / "exit.png")), 'Quit Photo Editor', self)
        self.exit_act.setShortcut('Ctrl+Q')
        self.exit_act.triggered.connect(self.close)

        # Actions for File menu
        self.new_act = QAction(QIcon(str(icon_path / "new.png")), 'New...')

        self.open_act = QAction(QIcon(str(icon_path / "open.png")), 'Open...', self)
        self.open_act.setShortcut('Ctrl+O')
        self.open_act.triggered.connect(self.open_media)

        self.print_act = QAction(QIcon(str(icon_path / "print.png")), "Print...", self)
        self.print_act.setShortcut('Ctrl+P')
        # self.print_act.triggered.connect(self.printImage)
        self.print_act.setEnabled(False)

        self.save_act = QAction(QIcon(str(icon_path / "save.png")), "Save...", self)
        self.save_act.setShortcut('Ctrl+S')
        self.save_act.triggered.connect(self.save_media)
        self.save_act.setEnabled(False)

        self.save_as_act = QAction("Save As...", self)
        self.save_as_act.setShortcut('Ctrl+Shift+S')
        self.save_as_act.triggered.connect(self.save_media_as)
        self.save_as_act.setEnabled(False)

        # Actions for Edit menu
        self.revert_act = QAction("Revert to Original", self)
        self.revert_act.triggered.connect(self.media_widget.revert_original_img)
        self.revert_act.setEnabled(False)

        # Actions for Tools menu
        self.crop_act = QAction(QIcon(str(icon_path / "crop.png")), "Crop", self)
        self.crop_act.setShortcut('C')
        self.crop_act.triggered.connect(lambda: self.media_widget.set_state(State.crop))

        self.rotate90_cw_act = QAction(QIcon(str(icon_path / "rotate90_cw.png")), 'Rotate 90º CW', self)
        self.rotate90_cw_act.setShortcut('R')
        self.rotate90_cw_act.triggered.connect(lambda: self.media_widget.img_rotate_90("cw"))

        self.rotate90_ccw_act = QAction(QIcon(str(icon_path / "rotate90_ccw.png")), 'Rotate 90º CCW', self)
        self.rotate90_ccw_act.setShortcut('Shift+R')
        self.rotate90_ccw_act.triggered.connect(lambda: self.media_widget.img_rotate_90("ccw"))

        self.flip_horizontal = QAction(QIcon(str(icon_path / "flip_horizontal.png")), 'Flip Horizontal', self)
        self.flip_horizontal.triggered.connect(lambda: self.media_widget.img_flip("horizontal"))

        self.flip_vertical = QAction(QIcon(str(icon_path / "flip_vertical.png")), 'Flip Vertical', self)
        self.flip_vertical.triggered.connect(lambda: self.media_widget.img_flip('vertical'))

        self.zoom_in_act = QAction(QIcon(str(icon_path / "zoom_in.png")), 'Zoom In', self)
        self.zoom_in_act.setShortcut('Ctrl++')
        self.zoom_in_act.triggered.connect(lambda: self.scale_image(1.25))
        self.zoom_in_act.setEnabled(False)

        self.zoom_out_act = QAction(QIcon(str(icon_path / "zoom_out.png")), 'Zoom Out', self)
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

        self.detect_faces_act = QAction((QIcon(str(icon_path / "detect_faces.png"))), "Detect Faces", self)
        self.detect_faces_act.setShortcut('Ctrl+D')
        self.detect_faces_act.triggered.connect(self._detect_faces)

        # And the shortcuts
        QShortcut(QtCore.Qt.Key.Key_Right, self, lambda: self._controller.select_next_media(
            extension=FILE_EXTENSION_PHOTO))
        QShortcut(QtCore.Qt.Key.Key_Left, self,
                  lambda: self._controller.select_prev_media(extension=FILE_EXTENSION_PHOTO))
        QShortcut(QtCore.Qt.Key.Key_Delete, self,
                  lambda: self._controller.delete_cur_media(extension=FILE_EXTENSION_PHOTO))

    def create_menus(self):
        """Set up the menubar."""
        menu_bar = self.menuBar()
        menu_bar.setNativeMenuBar(False)

        # Create Photo Editor menu and add actions
        main_menu = menu_bar.addMenu('Photo Editor')
        main_menu.addAction(self.about_act)
        main_menu.addSeparator()
        main_menu.addAction(self.exit_act)

        # Create file menu and add actions
        file_menu = menu_bar.addMenu('File')
        file_menu.addAction(self.open_act)
        file_menu.addAction(self.save_act)
        file_menu.addAction(self.save_as_act)
        file_menu.addSeparator()
        file_menu.addAction(self.print_act)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_act)

        edit_menu = menu_bar.addMenu('Edit')
        edit_menu.addAction(self.revert_act)

        tool_menu = menu_bar.addMenu('Tools')
        tool_menu.addAction(self.crop_act)
        # tool_menu.addAction(self.resize_act)
        tool_menu.addSeparator()
        tool_menu.addAction(self.rotate90_cw_act)
        tool_menu.addAction(self.rotate90_ccw_act)
        tool_menu.addAction(self.flip_horizontal)
        tool_menu.addAction(self.flip_vertical)
        tool_menu.addSeparator()
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
        tool_bar.addAction(self.open_act)
        tool_bar.addAction(self.save_act)
        tool_bar.addAction(self.print_act)
        tool_bar.addAction(self.exit_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.crop_act)
        # tool_bar.addAction(self.resize_act)
        tool_bar.addSeparator()
        tool_bar.addAction(self.rotate90_ccw_act)
        tool_bar.addAction(self.rotate90_cw_act)
        tool_bar.addAction(self.flip_horizontal)
        tool_bar.addAction(self.flip_vertical)
        tool_bar.addSeparator()
        tool_bar.addAction(self.zoom_in_act)
        tool_bar.addAction(self.zoom_out_act)
        # Add Face detection
        tool_bar.addSeparator()
        tool_bar.addAction(self.detect_faces_act)

    def create_user_comment_widget(self):
        tag_dock_widget = QDockWidget("Comments / Tags")
        self.comment_toolbar = UserCommentWidget(model=self._model)
        self.comment_toolbar.persons_widget.persons_widget.__class__.dropEvent = self.on_tag_drop
        self.comment_toolbar.persons_widget.persons_widget.clicked.connect(self.on_person_widget_clicked)
        tag_dock_widget.setWidget(self.comment_toolbar)
        self.addDockWidget(Qt.RightDockWidgetArea, tag_dock_widget)

    def create_editing_bar(self):
        """Create dock widget for editing tools."""
        # TODO: Add a tab widget for the different editing tools
        self.editing_bar = QDockWidget("Tools")
        self.editing_bar.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.editing_bar.setMinimumWidth(90)

        convert_to_grayscale = QToolButton()
        convert_to_grayscale.setToolTip("Convert to grayscale")
        convert_to_grayscale.setIcon(QIcon(str(icon_path / "grayscale.png")))
        convert_to_grayscale.clicked.connect(self.media_widget.img_to_gray)

        convert_to_RGB = QToolButton()
        convert_to_RGB.setToolTip("Convert to rgb")
        convert_to_RGB.setIcon(QIcon(str(icon_path / "rgb.png")))
        convert_to_RGB.clicked.connect(self.media_widget.img_to_rgb)

        convert_to_sepia = QToolButton()
        convert_to_sepia.setToolTip("Convert to sepia")
        convert_to_sepia.setIcon(QIcon(str(icon_path / "sepia.png")))
        convert_to_sepia.clicked.connect(self.media_widget.img_to_sepia)

        change_hue = QToolButton()
        change_hue.setToolTip("Set hue")
        change_hue.setIcon(QIcon(str(icon_path / "hue.png")))
        change_hue.clicked.connect(self.media_widget.img_set_hue)

        brightness_label = QLabel("Brightness")
        self.lum_slider = QSlider(Qt.Horizontal)
        self.lum_slider.setRange(-255, 255)
        self.lum_slider.setTickInterval(35)
        self.lum_slider.setTickPosition(QSlider.TicksAbove)
        self.lum_slider.valueChanged.connect(
            lambda: self.media_widget.img_set_lum_contrast(self.lum_slider.value(),
                                                           self.contrast_slider.value()))

        contrast_label = QLabel("Contrast")
        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setRange(-255, 255)
        self.contrast_slider.setTickInterval(35)
        self.contrast_slider.setTickPosition(QSlider.TicksAbove)
        self.contrast_slider.valueChanged.connect(
            lambda: self.media_widget.img_set_lum_contrast(self.lum_slider.value(),
                                                           self.contrast_slider.value()))

        # Set layout for dock widget
        editing_grid = QGridLayout()
        # editing_grid.addWidget(filters_label, 0, 0, 0, 2, Qt.AlignTop)
        editing_grid.addWidget(convert_to_grayscale, 1, 0)
        editing_grid.addWidget(convert_to_RGB, 1, 1)
        editing_grid.addWidget(convert_to_sepia, 2, 0)
        editing_grid.addWidget(change_hue, 2, 1)
        editing_grid.addWidget(brightness_label, 3, 0)
        editing_grid.addWidget(self.lum_slider, 4, 0, 1, 0)
        editing_grid.addWidget(contrast_label, 5, 0)
        editing_grid.addWidget(self.contrast_slider, 6, 0, 1, 0)
        editing_grid.setRowStretch(7, 10)

        container = QWidget()
        container.setLayout(editing_grid)

        self.editing_bar.setWidget(container)

        self.addDockWidget(Qt.LeftDockWidgetArea, self.editing_bar)

        self.tools_menu_act = self.editing_bar.toggleViewAction()

    def create_face_toolbar(self):
        """Create dock widget for editing tools."""
        # TODO: Add a tab widget for the different editing tools
        self.face_bar = QDockWidget("Detection")
        self.face_bar.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.face_bar.setMinimumWidth(90)

        self.det_face_widget = FaceDetectionWidget(db=self._model_local.db)
        self.det_face_widget.result_widget.clicked.connect(self.on_det_res_widget_clicked)
        self.face_bar.setWidget(self.det_face_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.face_bar)
        self.tools_menu_act = self.face_bar.toggleViewAction()

    def create_main_label(self):
        """Create an instance of the imageLabel class and set it 
           as the main window's central widget."""

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setBackgroundRole(QPalette.Dark)
        self.scroll_area.setAlignment(Qt.AlignCenter)

        self.media_widget = ImageLabel(self)
        self.scroll_area.setWidget(self.media_widget)

        self.setCentralWidget(self.scroll_area)
        # self.media_widget.setAcceptDrops(True)
        # self.media_widget.__class__.dropEvent = self.on_drop_media
        self.resize(QApplication.primaryScreen().availableSize() * 3 / 5)

    def update_actions(self):
        """Update the values of menu and toolbar items when an image 
        is loaded."""
        self.save_act.setEnabled(True)
        self.revert_act.setEnabled(True)
        self.zoom_in_act.setEnabled(True)
        self.zoom_out_act.setEnabled(True)
        self.normal_size_act.setEnabled(True)

    def _detect_faces(self):

        # Get models
        detection_model = self.det_face_widget.detection_model_combobox.itemText(
            self.det_face_widget.detection_model_combobox.currentIndex())
        recognition_model = self.det_face_widget.face_model_combobox.itemText(
            self.det_face_widget.face_model_combobox.currentIndex())
        self._controller_local.set_detection_model(detection_model)
        self._controller_local.set_recognition_model(recognition_model)

        # Detect
        self._controller_local.detect_faces([self._model.media_path])

    def open_media(self, file: Path = None):
        """Load a new media"""
        if file is None:
            extensions = ['*' + ext for ext in FILE_EXTENSION_PHOTO]
            ext = "("
            for e in extensions:
                ext += e + " "
            ext += ")"

            file, _ = QFileDialog.getOpenFileName(self, "Open Media",
                                                  "", f"Files {ext}")

        # Deactivate the img_editor if not an image
        ext = file.suffix
        if ext not in FILE_EXTENSION_PHOTO:
            self.media_widget.reset()
            self.setEnabled(False)
            return False
        self.setEnabled(True)

        if file:
            self.media_widget.open_media(file)
            self.comment_toolbar.set_user_comment(self.media_widget.load_comment(), file)
            self.det_face_widget.clear()
            self.det_face_widget.set_file(file)
            self.cumul_scale_factor = 1
            self.scroll_area.setVisible(True)
            self.print_act.setEnabled(True)
            self.fit_to_window_act.setEnabled(True)
            self.update_actions()

            if not self.fit_to_window_act.isChecked():
                self.media_widget.adjustSize()
            else:
                self.fit_window()

            # Reset all sliders
            self.lum_slider.setValue(0)

        elif file == "":
            # User selected Cancel
            pass
        else:
            QMessageBox.information(self, "Error",
                                    "Unable to open image.", QMessageBox.Ok)
        return True

    def save_media_as(self):
        """Save the image displayed in the label."""
        if not self.media_widget.qimage.isNull():
            file, _ = QFileDialog.getSaveFileName(self, "Save Image",
                                                  "", "PNG Files (*.png);;JPG Files (*.jpeg *.jpg );;Bitmap Files (*.bmp);;\
                    GIF Files (*.gif)")
            self.save_media(file=file)
        else:
            QMessageBox.information(self, "Empty Image",
                                    "There is no image to save.", QMessageBox.Ok)

    def save_media(self, file=None):
        """Save the image displayed in the label."""
        file = file if file else self._model.media_path
        if not self.media_widget.qimage.isNull():
            if file:
                self.media_widget.save_media(file=file)
                self.media_widget.save_comment(self.comment_toolbar.get_user_comment(), file=file)
                # Save tags
                tags = self.comment_toolbar.tags_widget.get_entities()
                for tag in tags:
                    self._controller.add_tag_to_db(tag)
            else:
                QMessageBox.information(self, "Error",
                                        "Unable to save image.", QMessageBox.Ok)
                return
        else:
            QMessageBox.information(self, "Empty Image",
                                    "There is no image to save.", QMessageBox.Ok)
            return

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
        QMessageBox.about(self, "About Photo Editor",
                          "Photo Editor\nVersion 0.2\n\nCreated by Joshua Willman")

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

    @pyqtSlot(common.comment.UserComment)
    def on_model_comment_updated(self):
        # Display the comment
        self.comment_toolbar.persons_widget.set_entities(self._model.media_comment.persons)

    def on_det_res_widget_clicked(self, index):
        row = index.row()
        self.display_entities(entities=self._model_local.detection_results, selected_ind=row)

    def on_detection_results_changed(self, results):
        self.display_entities(results, selected_ind=-1)
        self.det_face_widget.set_detection_results(results)

    def on_detection_results_selection_changed(self, idx):
        self.display_entities(entities=self._model_local.detection_results, selected_ind=idx)
        self.det_face_widget.result_widget.setCurrentRow(idx)

    def on_person_widget_clicked(self, index):
        row = index.row()
        items = self.comment_toolbar.persons_widget.get_items()
        entities = [item.entity for item in items]
        self.display_entities(entities=entities, selected_ind=row)

    def on_tag_drop(self, e):
        if (e.source() == self.det_face_widget.result_widget):
            widget = e.source()
            tags = self.comment_toolbar.persons_widget.get_items()
            tag_names = [tag.text() for tag in tags]
            for item, index in zip(widget.selectedItems(), widget.selectionModel().selectedIndexes()):
                if (item.text() == unknown_tag) or (item.text() in tag_names):
                    continue
                entity = common.comment.PersonEntity(name=item.text(), location=item.result.location)
                tags.append(PersonQListWidgetItem(entity))
            self.comment_toolbar.persons_widget.set_entities([tag.entity for tag in tags])

    def display_entities(self, entities: list[common.comment.PersonEntity], selected_ind=-1):
        qimage = self.media_widget.qimage.copy()
        painter = QPainter(qimage)

        pen_red = QPen(QtCore.Qt.red)
        pen_red.setWidth(10)
        pen_blue = QPen(QtCore.Qt.blue)
        pen_blue.setWidth(10)
        painter.setPen(pen_blue)

        for i, result in enumerate(entities):
            (top, right, bottom, left), name = result.location, result.name
            if i == selected_ind:
                painter.setPen(pen_red)
                painter.drawRect(left, top, right - left, bottom - top)
                painter.setPen(pen_blue)
            else:
                painter.drawRect(left, top, right - left, bottom - top)
        self.media_widget.setPixmap(QPixmap().fromImage(qimage))
        painter.end()
